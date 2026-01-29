"""
BFK AuthSystem - License Validator

Classe principal para validacao de licencas.
Orquestra todos os componentes (API, cache, hardware, UI).
"""

import logging
from typing import Optional, List, Callable, Dict, Any

from .api_client import APIClient
from .cache import CacheManager
from .hardware import get_hardware_info, generate_machine_id
from .models import (
    ValidationResult,
    RequiredAction,
    AppConfig,
    LicenseInfo,
    MachineInfo,
    SessionInfo,
    UserInfo,
    AuthTokens,
    MFASetupInfo
)
from .exceptions import (
    AuthSystemError,
    AuthenticationError,
    MFARequiredError,
    LicenseError,
    LicenseNotFoundError,
    NetworkError,
    CacheExpiredError,
    CacheCorruptedError,
    PasswordChangeRequiredError,
    ReauthenticationRequiredError,
    CircuitBreakerOpenError
)
from .retry_handler import RetryConfig
from .circuit_breaker import CircuitBreakerConfig


logger = logging.getLogger(__name__)


class LicenseValidator:
    """
    Validador de licencas do BFK AuthSystem.

    Orquestra a comunicacao com a API, cache local, coleta de hardware
    e interface grafica para fornecer uma experiencia completa de
    validacao de licencas.

    Exemplo basico:
        validator = LicenseValidator(
            server_url='https://api.example.com',
            app_code='MYAPP'
        )
        result = validator.verify(username='user', password='pass')
        if result.valid:
            print('Licenca valida!')

    Exemplo com UI automatica:
        result = validator.verify_with_ui()
        if result.valid:
            # Aplicacao pode iniciar
            pass
    """

    def __init__(
        self,
        server_url: str,
        app_code: str,
        timeout: float = 30.0,
        max_offline_days: int = 7,
        retry_config: RetryConfig = None,
        circuit_config: CircuitBreakerConfig = None,
        verify_ssl: bool = True,
        cache_enabled: bool = True
    ):
        """
        Inicializa o validador.

        Args:
            server_url: URL base da API (ex: https://api.example.com/api/v1)
            app_code: Codigo da aplicacao
            timeout: Timeout para requisicoes em segundos
            max_offline_days: Dias maximos em modo offline
            retry_config: Configuracao de retry
            circuit_config: Configuracao do circuit breaker
            verify_ssl: Se deve verificar certificado SSL
            cache_enabled: Se o cache local esta habilitado
        """
        self.server_url = server_url.rstrip('/')
        self.app_code = app_code
        self.max_offline_days = max_offline_days
        self.cache_enabled = cache_enabled

        # Coletar informacoes de hardware
        self._machine_id, self._hardware_components, self._system_info = get_hardware_info()

        # Cliente da API
        self._api = APIClient(
            base_url=self.server_url,
            timeout=timeout,
            retry_config=retry_config,
            circuit_config=circuit_config,
            verify_ssl=verify_ssl
        )

        # Cache local
        self._cache: Optional[CacheManager] = None
        if cache_enabled:
            self._cache = CacheManager(
                app_code=app_code,
                machine_id=self._machine_id,
                max_offline_days=max_offline_days
            )

        # Estado
        self._current_user: Optional[UserInfo] = None
        self._app_config: Optional[AppConfig] = None
        self._last_verification: Optional[ValidationResult] = None

        # Recuperar tokens do cache se existirem
        self._restore_session_from_cache()

    def _try_cached_session(self) -> bool:
        """
        Tenta usar sessao do cache para autenticacao.

        Verifica se ha verificacao valida no cache e se ainda
        esta dentro do periodo de reauth (dias_until_reauth > 0).

        Se estiver dentro do periodo, tenta renovar tokens com servidor.
        Se servidor offline, usa cache diretamente.

        Returns:
            True se sessao do cache e valida, False caso contrario
        """
        if not self._cache:
            return False

        try:
            # Verificar se ha verificacao valida no cache
            cached_verif = self._cache.load_verification()
            if not cached_verif or not cached_verif.valid:
                logger.debug("Sem verificacao valida no cache")
                return False

            # Calcular dias offline
            from datetime import datetime
            last_verif = datetime.fromisoformat(cached_verif.last_verification)
            days_offline = (datetime.now() - last_verif).days

            # Verificar se ainda esta dentro do periodo de reauth
            days_until_reauth = cached_verif.reauth_days - cached_verif.days_since_auth - days_offline
            if days_until_reauth <= 0:
                logger.info("Sessao expirada - requer reautenticacao")
                return False

            logger.info(f"Cache valido - {days_until_reauth} dias ate reauth")

            # Carregar tokens do cache
            cached_tokens = self._cache.load_tokens()

            # Tentar renovar sessao com servidor (tokens JWT expiram em minutos)
            server_offline = False
            session_revoked = False

            if cached_tokens and cached_tokens.refresh_token:
                try:
                    tokens = self.refresh_session()
                    if tokens and tokens.session_token:
                        # Tokens renovados - verificar licenca
                        result = self.verify(auth_token=tokens.session_token)
                        if result.valid:
                            logger.info("Sessao renovada com sucesso")
                            return True
                        else:
                            # Servidor respondeu mas licenca invalida
                            logger.info("Licenca invalida no servidor")
                            session_revoked = True
                except AuthenticationError as e:
                    # Refresh falhou - verificar codigo de erro
                    error_code = getattr(e, 'code', '')
                    logger.info(f"Refresh falhou: {error_code} - {e}")

                    if error_code == 'SESSION_REVOKED':
                        # Sessao foi revogada pelo admin - NAO usar cache
                        logger.info("Sessao revogada pelo servidor")
                        session_revoked = True
                    elif error_code in ['REFRESH_TOKEN_EXPIRED', 'INVALID_REFRESH_TOKEN']:
                        # Token expirou normalmente - pode usar cache se ainda tem dias
                        logger.info("Refresh token expirado, pode usar cache")
                        server_offline = False
                    else:
                        # Outro erro de autenticacao - tratar como revogacao por seguranca
                        logger.info(f"Erro de autenticacao: {error_code}")
                        session_revoked = True
                except (NetworkError, CircuitBreakerOpenError) as e:
                    # Servidor inacessivel - pode usar cache offline
                    logger.info(f"Servidor offline: {e}")
                    server_offline = True
                except Exception as e:
                    # Outro erro - verificar se servidor esta online
                    logger.info(f"Erro no refresh: {e}")
                    try:
                        self._api.get_health()
                        # Servidor online mas refresh falhou por outro motivo
                        logger.info("Servidor online, erro no refresh - usando cache")
                        server_offline = False
                    except Exception:
                        server_offline = True
            else:
                # Sem refresh_token - verificar se servidor esta online
                logger.info("Sem refresh_token no cache")
                try:
                    self._api.get_health()
                    # Servidor online mas sem tokens
                    server_offline = False
                except Exception:
                    server_offline = True

            # Se sessao foi explicitamente revogada, pedir login
            if session_revoked:
                return False

            # Usar cache se ainda tem dias de reauth
            # (servidor pode estar online mas refresh_token expirado)
            if days_until_reauth > 0:
                logger.info(f"Usando cache ({'offline' if server_offline else 'online, token expirado'})")

                # Verificar se _last_verification esta preenchido e atualizar is_offline
                if self._last_verification and self._last_verification.valid:
                    # Atualizar flag is_offline
                    self._last_verification = ValidationResult(
                        valid=self._last_verification.valid,
                        message=self._last_verification.message,
                        days_until_reauth=days_until_reauth,
                        days_since_auth=cached_verif.days_since_auth + days_offline,
                        app_config=self._last_verification.app_config,
                        license_info=self._last_verification.license_info,
                        is_offline=server_offline
                    )
                    return True

                # Recriar _last_verification do cache
                import json
                app_config_dict = json.loads(cached_verif.app_config) if cached_verif.app_config else {}
                if app_config_dict:
                    self._app_config = AppConfig.from_dict(app_config_dict)

                self._last_verification = ValidationResult(
                    valid=True,
                    message="Sessao do cache",
                    days_until_reauth=days_until_reauth,
                    days_since_auth=cached_verif.days_since_auth + days_offline,
                    app_config=self._app_config,
                    license_info=LicenseInfo(
                        license_key=cached_verif.license_key,
                        user=cached_verif.username,
                        email='',
                        app_name=cached_verif.app_code
                    ),
                    is_offline=server_offline
                )

                self._current_user = UserInfo(
                    id=0,
                    username=cached_verif.username,
                    email='',
                    full_name=cached_verif.username,
                    mfa_enabled=True
                )

                return True

            return False

        except CacheExpiredError:
            logger.info("Cache expirado")
            return False
        except Exception as e:
            logger.debug(f"Erro ao verificar sessao do cache: {e}")
            return False

    def _restore_session_from_cache(self):
        """Recupera sessao do cache se disponivel."""
        if not self._cache:
            return

        try:
            # Recuperar tokens
            cached_tokens = self._cache.load_tokens()
            if cached_tokens and cached_tokens.session_token:
                self._api.session_token = cached_tokens.session_token

            # Recuperar ultima verificacao
            cached_verif = self._cache.load_verification()
            if cached_verif:
                import json
                app_config_dict = json.loads(cached_verif.app_config) if cached_verif.app_config else {}
                if app_config_dict:
                    self._app_config = AppConfig.from_dict(app_config_dict)

                # Criar ValidationResult basico do cache
                self._last_verification = ValidationResult(
                    valid=cached_verif.valid,
                    message="Dados do cache",
                    days_until_reauth=cached_verif.reauth_days - cached_verif.days_since_auth,
                    days_since_auth=cached_verif.days_since_auth,
                    app_config=self._app_config,
                    license_info=LicenseInfo(
                        license_key=cached_verif.license_key,
                        user=cached_verif.username,
                        email='',
                        app_name=cached_verif.app_code
                    ),
                    is_offline=True
                )

                # Criar UserInfo basico
                self._current_user = UserInfo(
                    id=0,
                    username=cached_verif.username,
                    email='',
                    full_name=cached_verif.username,
                    mfa_enabled=True
                )

        except Exception as e:
            logger.debug(f"Nao foi possivel restaurar sessao do cache: {e}")

    @property
    def machine_id(self) -> str:
        """Retorna o ID da maquina."""
        return self._machine_id

    @property
    def hardware_components(self) -> dict:
        """Retorna os componentes de hardware."""
        return self._hardware_components

    @property
    def hostname(self) -> str:
        """Retorna o nome do computador."""
        return self._system_info.get('hostname', 'unknown')

    @property
    def os_info(self) -> str:
        """Retorna informacoes do sistema operacional."""
        return self._system_info.get('os_info', 'unknown')

    @property
    def current_user(self) -> Optional[UserInfo]:
        """Retorna informacoes do usuario atual."""
        return self._current_user

    @property
    def app_config(self) -> Optional[AppConfig]:
        """Retorna configuracao da aplicacao."""
        return self._app_config

    @property
    def is_online(self) -> bool:
        """Verifica se consegue conectar ao servidor."""
        try:
            self._api.get_health()
            return True
        except Exception:
            return False

    def verify(
        self,
        username: str = None,
        password: str = None,
        email: str = None,
        mfa_token: str = None,
        auth_token: str = None,
        license_key: str = None,
        use_cache: bool = True
    ) -> ValidationResult:
        """
        Verifica a licenca do usuario.

        Fluxo:
        1. Se online, verifica com o servidor
        2. Se offline e cache valido, usa cache
        3. Retorna resultado com acoes necessarias

        Args:
            username: Nome de usuario
            password: Senha
            email: Email (alternativa ao username)
            mfa_token: Token MFA de 6 digitos (se MFA habilitado)
            auth_token: Token de autenticacao (alternativa a username/password)
            license_key: Chave de licenca (obrigatoria na primeira execucao)
            use_cache: Se deve usar cache em caso de falha

        Returns:
            ValidationResult com status da verificacao

        Raises:
            AuthenticationError: Credenciais invalidas
            LicenseError: Problemas com licenca
            NetworkError: Falha de conexao (se cache desabilitado)
        """
        # Tentar verificacao online
        try:
            result = self._verify_online(username, password, email, mfa_token, auth_token, license_key)
            self._last_verification = result

            # Salvar no cache se valido
            if result.valid and self._cache:
                self._save_to_cache(result)

            return result

        except (NetworkError, CircuitBreakerOpenError) as e:
            logger.warning(f"Falha na conexao: {e}")

            # Tentar cache offline
            if use_cache and self._cache:
                try:
                    return self._verify_offline()
                except (CacheExpiredError, CacheCorruptedError) as cache_error:
                    logger.warning(f"Cache invalido: {cache_error}")

            # Sem cache, propagar erro
            raise

    def _verify_online(
        self,
        username: str = None,
        password: str = None,
        email: str = None,
        mfa_token: str = None,
        auth_token: str = None,
        license_key: str = None
    ) -> ValidationResult:
        """Verifica licenca com o servidor."""
        response = self._api.verify_license(
            username=username,
            password=password,
            email=email,
            mfa_token=mfa_token,
            auth_token=auth_token,
            license_key=license_key,
            app_code=self.app_code,
            machine_id=self._machine_id,
            hostname=self.hostname,
            os_info=self.os_info,
            hardware_components=self._hardware_components
        )

        result = ValidationResult.from_dict(response)

        # Salvar app_config
        if result.app_config:
            self._app_config = result.app_config

        # Salvar tokens se retornados (autenticacao bem-sucedida)
        session_token = response.get('session_token')
        refresh_token = response.get('refresh_token')

        if session_token:
            # Definir token no cliente API para requisicoes futuras
            self._api.session_token = session_token

            # Salvar tokens no cache
            if self._cache and refresh_token:
                self._cache.save_tokens(session_token, refresh_token)

            # Carregar info do usuario
            try:
                me_response = self._api.get_me()
                self._current_user = UserInfo.from_dict(me_response.get('user', me_response))
            except Exception:
                pass

        return result

    def _verify_offline(self) -> ValidationResult:
        """Verifica licenca usando cache local e token JWT RS256."""
        if not self._cache:
            raise NetworkError("Cache desabilitado e servidor inacessivel")

        cached = self._cache.load_verification()
        if not cached:
            raise NetworkError("Sem cache disponivel")

        # Calcular dias offline
        days_offline = self._cache.get_days_offline()

        # Carregar app_config do cache
        import json
        app_config_dict = json.loads(cached.app_config) if cached.app_config else {}
        app_config = AppConfig.from_dict(app_config_dict) if app_config_dict else None

        # Verificar token JWT RS256 de hardware se disponivel
        hw_token_valid = False
        hw_token_message = ""

        if cached.hardware_validation_token:
            try:
                from .hardware_validator import verify_hardware_token

                is_valid, message, payload = verify_hardware_token(
                    token=cached.hardware_validation_token,
                    current_machine_id=self._machine_id,
                    current_components=self._hardware_components
                )

                hw_token_valid = is_valid
                hw_token_message = message

                if not is_valid:
                    logger.warning(f"Token de hardware invalido: {message}")
                else:
                    logger.info("Token de hardware verificado com sucesso (offline)")

            except ImportError:
                logger.warning("Modulo hardware_validator nao disponivel")
            except Exception as e:
                logger.warning(f"Erro ao verificar token de hardware: {e}")

        # Se tem token e ele e invalido, falhar
        if cached.hardware_validation_token and not hw_token_valid:
            return ValidationResult(
                valid=False,
                message=f"Validacao offline falhou: {hw_token_message}",
                requires_action=RequiredAction.REAUTH,
                days_offline=days_offline,
                is_offline=True,
                error_code="HARDWARE_TOKEN_INVALID"
            )

        # Verificar se precisa reautenticar
        requires_action = RequiredAction.NONE
        days_until_reauth = cached.reauth_days - cached.days_since_auth - days_offline

        if days_until_reauth <= 0:
            requires_action = RequiredAction.REAUTH

        return ValidationResult(
            valid=cached.valid,
            message=f"Verificacao offline ({days_offline} dias)" + (
                " - hardware validado" if hw_token_valid else ""
            ),
            requires_action=requires_action,
            days_offline=days_offline,
            days_until_reauth=max(0, days_until_reauth),
            days_since_auth=cached.days_since_auth + days_offline,
            app_config=app_config,
            is_offline=True
        )

    def _save_to_cache(self, result: ValidationResult):
        """Salva resultado no cache."""
        if not self._cache or not result.valid:
            return

        try:
            app_config_dict = result.app_config.to_dict() if result.app_config else {}

            self._cache.save_verification(
                valid=result.valid,
                username=result.license_info.user if result.license_info else '',
                license_key=result.license_info.license_key if result.license_info else '',
                reauth_days=result.days_until_reauth + result.days_since_auth,
                days_since_auth=result.days_since_auth,
                app_config=app_config_dict,
                hardware_validation_token=result.hardware_validation_token or ''
            )
        except Exception as e:
            logger.warning(f"Falha ao salvar cache: {e}")

    def authenticate(
        self,
        username: str = None,
        password: str = None,
        email: str = None,
        mfa_token: str = None
    ) -> AuthTokens:
        """
        Autentica usuario e obtem tokens.

        Args:
            username: Nome de usuario
            password: Senha
            email: Email (alternativa)
            mfa_token: Token MFA (se habilitado)

        Returns:
            AuthTokens com tokens de sessao (pode ter campos None se fluxo incompleto)

        Raises:
            AuthenticationError: Credenciais invalidas
            MFARequiredError: MFA necessario
        """
        response = self._api.login(
            username=username,
            password=password,
            email=email,
            mfa_token=mfa_token
        )

        tokens = AuthTokens.from_dict(response)

        # Salvar tokens no cache
        if self._cache and tokens.session_token:
            self._cache.save_tokens(tokens.session_token, tokens.refresh_token)

        # Carregar info do usuario
        if tokens.session_token:
            try:
                me_response = self._api.get_me()
                self._current_user = UserInfo.from_dict(me_response.get('user', me_response))
            except Exception:
                pass

        return tokens

    def logout(self):
        """Realiza logout e limpa tokens."""
        try:
            self._api.logout()
        except Exception as e:
            logger.warning(f"Erro no logout: {e}")
        finally:
            self._api.session_token = None
            if self._cache:
                self._cache.clear_tokens()
            self._current_user = None

    def refresh_session(self) -> AuthTokens:
        """
        Renova sessao usando refresh token do cache.

        Returns:
            Novos tokens

        Raises:
            AuthenticationError: Refresh token invalido
        """
        if not self._cache:
            raise AuthenticationError("Cache desabilitado")

        cached_tokens = self._cache.load_tokens()
        if not cached_tokens:
            raise AuthenticationError("Sem tokens em cache")

        response = self._api.refresh_token(cached_tokens.refresh_token)
        tokens = AuthTokens.from_dict(response)

        # Atualizar cache
        if tokens.session_token:
            self._cache.save_tokens(tokens.session_token, tokens.refresh_token)

        return tokens

    def change_password(self, current_password: str, new_password: str) -> bool:
        """
        Altera senha do usuario.

        Args:
            current_password: Senha atual
            new_password: Nova senha

        Returns:
            True se alterado com sucesso
        """
        response = self._api.change_password(current_password, new_password)
        return response.get('success', False)

    def change_password_required(
        self,
        password_change_token: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        Altera senha obrigatoria (primeiro login ou reset por admin).

        IMPORTANTE: Esta operacao pode retornar diferentes respostas:
        - Se MFA nao configurado: {'mfa_setup_required': True, 'mfa_setup_token': '...'}
        - Se MFA ja configurado: {'success': True, 'message': '...'}

        O chamador deve verificar 'mfa_setup_required' na resposta e chamar
        setup_mfa_required() se necessario.

        Args:
            password_change_token: Token recebido na resposta PASSWORD_CHANGE_REQUIRED
            new_password: Nova senha

        Returns:
            Dict com resposta que pode conter:
            - mfa_setup_required (bool)
            - mfa_setup_token (str)
            - message (str)

        Raises:
            AuthenticationError: Token invalido ou expirado
        """
        response = self._api.change_password_required(
            password_change_token=password_change_token,
            new_password=new_password
        )

        # NAO tentar extrair tokens aqui - a resposta geralmente nao contem tokens
        # O chamador precisa verificar mfa_setup_required e prosseguir com o fluxo
        return response

    def setup_mfa_required(self, mfa_setup_token: str) -> Dict[str, Any]:
        """
        Inicia setup MFA obrigatorio usando token temporario.

        Deve ser chamado apos change_password_required() retornar mfa_setup_required=True.

        Args:
            mfa_setup_token: Token recebido apos troca de senha

        Returns:
            Dict com:
            - secret (str): Chave secreta do MFA
            - qr_code (str): QR code em base64 para escanear no Google Authenticator

        Raises:
            AuthenticationError: Token invalido ou expirado
        """
        return self._api.setup_mfa_required(mfa_setup_token, app_code=self.app_code)

    def confirm_mfa_required(self, mfa_setup_token: str, mfa_code: str) -> Dict[str, Any]:
        """
        Confirma setup MFA obrigatorio.

        IMPORTANTE: Este metodo NAO retorna session_token.
        Apos MFA configurado, chame verify() para obter session_token.

        Deve ser chamado apos o usuario escanear o QR code e obter um codigo de 6 digitos.

        Args:
            mfa_setup_token: Token recebido apos troca de senha
            mfa_code: Codigo de 6 digitos do Google Authenticator

        Returns:
            Dict com:
            - auth_token: Token temporario para usar em verify()
            - recovery_codes: Lista de codigos de recuperacao
            - next_step: 'LICENSE_VALIDATION'

        Raises:
            AuthenticationError: Codigo MFA invalido
        """
        response = self._api.confirm_mfa_required(mfa_setup_token, mfa_code)

        # NAO salvar tokens - auth_token e temporario
        # O session_token sera obtido em verify()

        return response

    def setup_mfa(self) -> MFASetupInfo:
        """
        Inicia configuracao de MFA.

        Returns:
            MFASetupInfo com QR code e secret
        """
        response = self._api.setup_mfa()
        return MFASetupInfo.from_dict(response)

    def enable_mfa(self, token: str) -> List[str]:
        """
        Habilita MFA com token de verificacao.

        Args:
            token: Token TOTP de 6 digitos

        Returns:
            Lista de recovery codes
        """
        response = self._api.enable_mfa(token)
        return response.get('recovery_codes', [])

    def verify_mfa(self, token: str) -> bool:
        """
        Verifica token MFA.

        Args:
            token: Token TOTP ou recovery code

        Returns:
            True se valido
        """
        response = self._api.verify_mfa(token)
        return response.get('success', False)

    def disable_mfa(self, token: str) -> bool:
        """
        Desabilita MFA.

        Args:
            token: Token para confirmar

        Returns:
            True se desabilitado
        """
        response = self._api.disable_mfa(token)
        return response.get('success', False)

    def get_active_sessions(self) -> List[SessionInfo]:
        """
        Lista sessoes ativas do usuario.

        Returns:
            Lista de SessionInfo
        """
        response = self._api.get_sessions()
        sessions = response.get('sessions', [])
        return [SessionInfo.from_dict(s) for s in sessions]

    def revoke_session(self, session_id: int) -> bool:
        """
        Revoga uma sessao especifica.

        Args:
            session_id: ID da sessao

        Returns:
            True se revogado
        """
        response = self._api.revoke_session(session_id)
        return response.get('success', False)

    def revoke_all_sessions(self) -> int:
        """
        Revoga todas as outras sessoes.

        Returns:
            Numero de sessoes revogadas
        """
        response = self._api.revoke_all_sessions()
        return response.get('revoked_count', 0)

    def get_app_config(self) -> AppConfig:
        """
        Obtem configuracao da aplicacao.

        Returns:
            AppConfig
        """
        response = self._api.get_app_config(self.app_code)
        config = AppConfig.from_dict(response.get('config', response))
        self._app_config = config
        return config

    def show_status(self, parent=None) -> None:
        """
        Exibe dialog de status com informacoes do usuario, licenca e sessoes.

        Usa dados armazenados da ultima verificacao bem-sucedida.
        Requer PyQt5 instalado.

        Args:
            parent: Widget pai (opcional)
        """
        from .ui import show_status_dialog, PYQT_AVAILABLE

        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessario. Instale com: pip install bfk-authsystem[ui]")

        # Dados da ultima verificacao
        license_info = None
        user_info = None
        is_offline = False
        days_offline = 0
        days_until_reauth = 30
        sessions = []

        if self._last_verification:
            license_info = self._last_verification.license_info
            is_offline = self._last_verification.is_offline
            days_offline = self._last_verification.days_offline
            days_until_reauth = self._last_verification.days_until_reauth

        # Usar usuario atual ou criar um basico a partir de license_info
        if self._current_user:
            user_info = self._current_user
        elif license_info:
            # Criar UserInfo basico a partir dos dados da licenca
            user_info = UserInfo(
                id=0,
                username=license_info.user,
                email=license_info.email,
                full_name=license_info.user,
                mfa_enabled=True  # MFA sempre obrigatorio
            )

        # Tentar buscar sessoes ativas (opcional, nao falha se nao conseguir)
        if self._api.session_token:
            try:
                sessions = self.get_active_sessions()
            except Exception:
                pass

        show_status_dialog(
            app_config=self._app_config,
            user_info=user_info,
            license_info=license_info,
            sessions=sessions,
            is_offline=is_offline,
            days_offline=days_offline,
            days_until_reauth=days_until_reauth,
            parent=parent
        )

    def login_with_ui(self, parent=None) -> bool:
        """
        Executa fluxo completo de autenticacao com UI.

        Primeiro verifica se ha sessao valida no cache. Se houver,
        tenta revalidar com o servidor. So mostra dialogs se necessario:
        - Login (username/password)
        - Troca de senha (se obrigatorio)
        - Setup MFA (SEMPRE obrigatorio)
        - Recovery codes
        - License key (se primeira execucao)

        Requer PyQt5 instalado.

        Args:
            parent: Widget pai (opcional)

        Returns:
            True se autenticado com sucesso, False se cancelado

        Raises:
            ImportError: Se PyQt5 nao estiver instalado
        """
        from .ui import (
            PYQT_AVAILABLE,
            show_login_dialog,
            show_mfa_verify_dialog,
            show_mfa_setup_dialog,
            show_license_key_dialog,
            show_force_change_password_dialog,
            show_recovery_codes_dialog,
        )
        from .models import MFASetupInfo
        from PyQt5.QtWidgets import QMessageBox

        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessario. Instale com: pip install bfk-authsystem[ui]")

        # Verificar se ha sessao valida no cache
        if self._try_cached_session():
            return True

        # Obter configuracao visual da aplicacao
        try:
            config = self.get_app_config()
        except Exception:
            config = None

        # Variaveis para manter credenciais durante o fluxo
        username = None
        password = None
        auth_token = None

        while True:
            # 1. Login dialog (se ainda nao tem credenciais)
            if not username and not auth_token:
                credentials = show_login_dialog(
                    app_config=config,
                    parent=parent,
                    server_url=self.server_url
                )
                if not credentials:
                    return False  # Usuario cancelou

                username, password = credentials

            # 2. Tentar verificacao
            result = self.verify(
                username=username,
                password=password,
                auth_token=auth_token
            )

            # 3. Sucesso!
            if result.valid:
                return True

            # 4. Tratar cada caso de erro
            if result.error_code == 'MFA_REQUIRED':
                # Usuario tem MFA configurado - pedir codigo
                token = show_mfa_verify_dialog(app_config=config, parent=parent)
                if not token:
                    # Voltar para login
                    username = None
                    password = None
                    continue

                result = self.verify(username=username, password=password, mfa_token=token)
                if result.valid:
                    return True

                # Apos MFA valido, pode precisar de license_key
                if result.error_code == 'LICENSE_KEY_REQUIRED':
                    # Servidor retorna auth_token para evitar re-verificacao MFA
                    auth_token = result.auth_token

                    license_key = show_license_key_dialog(app_config=config, parent=parent)
                    if not license_key:
                        username = None
                        password = None
                        auth_token = None
                        continue

                    # Usar auth_token se disponivel (evita expiracao do codigo TOTP)
                    if auth_token:
                        result = self.verify(
                            auth_token=auth_token,
                            license_key=license_key
                        )
                    else:
                        result = self.verify(
                            username=username,
                            password=password,
                            mfa_token=token,
                            license_key=license_key
                        )
                    if result.valid:
                        return True

                # Se ainda nao valido, mostra erro e volta para login
                if result.error_code == 'MFA_INVALID':
                    QMessageBox.warning(parent, "Erro", "Codigo MFA invalido")
                    continue  # Pedir MFA novamente

                # Outro erro - voltar para login
                continue

            elif result.error_code == 'PASSWORD_CHANGE_REQUIRED':
                # Troca de senha obrigatoria
                new_password = show_force_change_password_dialog(app_config=config, parent=parent)
                if not new_password:
                    # Voltar para login
                    username = None
                    password = None
                    continue

                response = self.change_password_required(
                    password_change_token=result.password_change_token,
                    new_password=new_password
                )

                # Apos trocar senha, MFA SEMPRE sera obrigatorio
                if response.get('mfa_setup_required'):
                    mfa_result = self._handle_mfa_setup_flow(
                        mfa_setup_token=response.get('mfa_setup_token'),
                        config=config,
                        parent=parent
                    )
                    if mfa_result:
                        auth_token = mfa_result  # auth_token para usar em verify
                        continue  # Volta para validar license
                    else:
                        # Usuario cancelou MFA setup
                        username = None
                        password = None
                        continue
                else:
                    # MFA ja configurado - pedir novo login
                    QMessageBox.information(
                        parent, "Senha Alterada",
                        "Senha alterada com sucesso. Faca login novamente."
                    )
                    username = None
                    password = None
                    continue

            elif result.error_code == 'MFA_SETUP_REQUIRED':
                # Usuario autenticou mas precisa configurar MFA
                mfa_result = self._handle_mfa_setup_flow(
                    mfa_setup_token=result.mfa_setup_token,
                    config=config,
                    parent=parent
                )
                if mfa_result:
                    auth_token = mfa_result
                    continue  # Volta para validar license
                else:
                    # Usuario cancelou
                    username = None
                    password = None
                    continue

            elif result.error_code == 'LICENSE_KEY_REQUIRED':
                # Primeira execucao - pedir license key
                license_key = show_license_key_dialog(app_config=config, parent=parent)
                if not license_key:
                    # Voltar para login
                    username = None
                    password = None
                    auth_token = None
                    continue

                result = self.verify(
                    username=username,
                    password=password,
                    auth_token=auth_token,
                    license_key=license_key
                )
                if result.valid:
                    return True
                # Se ainda nao valido, continua loop

            elif result.error_code == 'INVALID_AUTH_TOKEN':
                # auth_token expirou - pedir novo login
                auth_token = None
                username = None
                password = None
                continue

            else:
                # Erro desconhecido - mostrar mensagem e pedir novo login
                QMessageBox.warning(
                    parent, "Erro",
                    result.message or "Falha na autenticacao"
                )
                username = None
                password = None
                auth_token = None
                continue

        return False

    def _handle_mfa_setup_flow(
        self,
        mfa_setup_token: str,
        config=None,
        parent=None
    ) -> str:
        """
        Executa fluxo de setup MFA.

        Args:
            mfa_setup_token: Token para setup MFA
            config: AppConfig (opcional)
            parent: Widget pai

        Returns:
            auth_token se sucesso, None se cancelado
        """
        from .ui import show_mfa_setup_dialog, show_recovery_codes_dialog
        from .models import MFASetupInfo

        # Obter QR code
        mfa_data = self.setup_mfa_required(mfa_setup_token)
        mfa_info = MFASetupInfo(
            secret=mfa_data.get('secret', ''),
            qr_code=mfa_data.get('qr_code', ''),
            provisioning_uri=mfa_data.get('provisioning_uri', '')
        )

        # Mostrar dialog de setup MFA
        mfa_code = show_mfa_setup_dialog(app_config=config, mfa_info=mfa_info, parent=parent)
        if not mfa_code:
            return None

        # Confirmar MFA
        response = self.confirm_mfa_required(
            mfa_setup_token=mfa_setup_token,
            mfa_code=mfa_code
        )

        # Mostrar recovery codes
        recovery_codes = response.get('recovery_codes', [])
        if recovery_codes:
            show_recovery_codes_dialog(
                app_config=config,
                recovery_codes=recovery_codes,
                parent=parent
            )

        # Retornar auth_token para continuar fluxo
        return response.get('auth_token')

    def clear_cache(self):
        """Limpa todo o cache local."""
        if self._cache:
            self._cache.clear()

    def close(self):
        """Fecha conexoes."""
        self._api.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_validator(
    server_url: str,
    app_code: str,
    **kwargs
) -> LicenseValidator:
    """
    Funcao factory para criar validador.

    Args:
        server_url: URL do servidor
        app_code: Codigo da aplicacao
        **kwargs: Argumentos adicionais para LicenseValidator

    Returns:
        Instancia configurada de LicenseValidator
    """
    return LicenseValidator(server_url=server_url, app_code=app_code, **kwargs)
