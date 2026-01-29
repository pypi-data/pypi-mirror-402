"""
BFK AuthSystem - Cliente HTTP para API

Cliente HTTP que integra retry handler e circuit breaker.
"""

import logging
from typing import Dict, Optional, Any
from urllib.parse import urljoin

import requests

from .exceptions import (
    AuthSystemError,
    AuthenticationError,
    NetworkError,
    ServerError,
    TimeoutError as AuthTimeoutError,
    raise_for_error_code
)
from .retry_handler import RetryHandler, RetryConfig
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig


logger = logging.getLogger(__name__)


class APIClient:
    """
    Cliente HTTP para comunicacao com a API do BFK AuthSystem.

    Integra:
    - Retry com backoff exponencial
    - Circuit breaker para protecao contra falhas
    - Tratamento de erros consistente

    Exemplo:
        client = APIClient(base_url='https://api.example.com')
        response = client.post('/auth/login', json={'username': 'user', 'password': 'pass'})
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        retry_config: RetryConfig = None,
        circuit_config: CircuitBreakerConfig = None,
        session_token: str = None,
        verify_ssl: bool = True
    ):
        """
        Inicializa o cliente.

        Args:
            base_url: URL base da API (ex: https://api.example.com/api/v1)
            timeout: Timeout padrao para requisicoes em segundos
            retry_config: Configuracao de retry (usa padrao se None)
            circuit_config: Configuracao do circuit breaker (usa padrao se None)
            session_token: Token de sessao para autenticacao (opcional)
            verify_ssl: Se deve verificar certificado SSL
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session_token = session_token

        # Configurar retry handler
        self._retry_config = retry_config or RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0,
            jitter=True
        )
        self._retry_handler = RetryHandler(self._retry_config)

        # Configurar circuit breaker
        self._circuit_config = circuit_config or CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            recovery_timeout=60.0
        )
        self._circuit_breaker = CircuitBreaker(
            name='api_client',
            config=self._circuit_config
        )

        # Sessao HTTP persistente
        self._session = requests.Session()
        self._session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'BFK-AuthSystem-Client/1.0'
        })

    @property
    def session_token(self) -> Optional[str]:
        """Retorna o token de sessao atual."""
        return self._session_token

    @session_token.setter
    def session_token(self, value: Optional[str]):
        """Define o token de sessao."""
        self._session_token = value

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        """Retorna o circuit breaker."""
        return self._circuit_breaker

    def _build_url(self, endpoint: str) -> str:
        """
        Constroi URL completa a partir do endpoint.

        Args:
            endpoint: Endpoint da API (ex: /auth/login)

        Returns:
            URL completa
        """
        if endpoint.startswith('/'):
            return f"{self.base_url}{endpoint}"
        return f"{self.base_url}/{endpoint}"

    def _get_headers(self, extra_headers: Dict[str, str] = None) -> Dict[str, str]:
        """
        Retorna headers para requisicao.

        Args:
            extra_headers: Headers adicionais

        Returns:
            Dict com headers
        """
        headers = {}

        if self._session_token:
            headers['Authorization'] = f'Bearer {self._session_token}'

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Processa resposta da API.

        Args:
            response: Resposta HTTP

        Returns:
            Dict com dados da resposta

        Raises:
            AuthSystemError: Se a resposta indicar erro
        """
        # Tentar extrair JSON
        try:
            data = response.json()
        except ValueError:
            data = {'message': response.text}

        # Verificar status code
        if response.status_code >= 500:
            raise ServerError(
                message=data.get('message', 'Erro interno do servidor'),
                code=data.get('code', 'SERVER_ERROR'),
                details={'status_code': response.status_code}
            )

        if response.status_code == 401:
            code = data.get('code', 'AUTH_FAILED')
            # Para MFA_REQUIRED e MFA_SETUP_REQUIRED, retornar dados
            # para que o cliente possa tratar o fluxo de MFA
            if code in ['MFA_REQUIRED', 'MFA_SETUP_REQUIRED', 'MFA_INVALID']:
                return data
            raise AuthenticationError(
                message=data.get('message', 'Nao autorizado'),
                code=code,
                details=data
            )

        # PASSWORD_CHANGE_REQUIRED retorna 200 com codigo especifico
        if response.status_code == 200 and data.get('code') == 'PASSWORD_CHANGE_REQUIRED':
            return data

        if response.status_code == 403:
            code = data.get('code', 'FORBIDDEN')
            # Levantar excecao especifica baseada no codigo
            if code in ['NO_LICENSE', 'LICENSE_EXPIRED', 'LICENSE_SUSPENDED', 'MACHINE_LIMIT']:
                raise_for_error_code(code, data.get('message'), data)
            raise AuthSystemError(
                message=data.get('message', 'Acesso negado'),
                code=code,
                details=data
            )

        if response.status_code >= 400:
            code = data.get('code', 'CLIENT_ERROR')
            # LICENSE_KEY_REQUIRED deve retornar dados para o fluxo de autenticacao
            if code == 'LICENSE_KEY_REQUIRED':
                return data
            raise AuthSystemError(
                message=data.get('message', 'Erro na requisicao'),
                code=code,
                details=data
            )

        return data

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json: Dict = None,
        params: Dict = None,
        headers: Dict = None,
        timeout: float = None
    ) -> Dict[str, Any]:
        """
        Faz requisicao HTTP com retry e circuit breaker.

        Args:
            method: Metodo HTTP (GET, POST, etc)
            endpoint: Endpoint da API
            json: Corpo da requisicao (JSON)
            params: Query parameters
            headers: Headers adicionais
            timeout: Timeout especifico

        Returns:
            Dict com resposta

        Raises:
            AuthSystemError: Em caso de erro
        """
        url = self._build_url(endpoint)
        req_headers = self._get_headers(headers)
        req_timeout = timeout or self.timeout

        def do_request():
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    headers=req_headers,
                    timeout=req_timeout,
                    verify=self.verify_ssl
                )
                return self._handle_response(response)

            except requests.exceptions.Timeout as e:
                raise AuthTimeoutError(
                    message=f"Timeout na requisicao para {endpoint}",
                    code="TIMEOUT",
                    details={'url': url, 'timeout': req_timeout}
                )

            except requests.exceptions.ConnectionError as e:
                raise NetworkError(
                    message=f"Erro de conexao: {str(e)}",
                    code="NETWORK_ERROR",
                    details={'url': url}
                )

            except requests.exceptions.RequestException as e:
                raise NetworkError(
                    message=f"Erro na requisicao: {str(e)}",
                    code="REQUEST_ERROR",
                    details={'url': url}
                )

        # Executar com circuit breaker e retry
        return self._circuit_breaker.call(
            lambda: self._retry_handler.execute(do_request)
        )

    def get(
        self,
        endpoint: str,
        params: Dict = None,
        headers: Dict = None,
        timeout: float = None
    ) -> Dict[str, Any]:
        """
        Faz requisicao GET.

        Args:
            endpoint: Endpoint da API
            params: Query parameters
            headers: Headers adicionais
            timeout: Timeout especifico

        Returns:
            Dict com resposta
        """
        return self._make_request('GET', endpoint, params=params, headers=headers, timeout=timeout)

    def post(
        self,
        endpoint: str,
        json: Dict = None,
        params: Dict = None,
        headers: Dict = None,
        timeout: float = None
    ) -> Dict[str, Any]:
        """
        Faz requisicao POST.

        Args:
            endpoint: Endpoint da API
            json: Corpo da requisicao
            params: Query parameters
            headers: Headers adicionais
            timeout: Timeout especifico

        Returns:
            Dict com resposta
        """
        return self._make_request('POST', endpoint, json=json, params=params, headers=headers, timeout=timeout)

    def put(
        self,
        endpoint: str,
        json: Dict = None,
        params: Dict = None,
        headers: Dict = None,
        timeout: float = None
    ) -> Dict[str, Any]:
        """
        Faz requisicao PUT.

        Args:
            endpoint: Endpoint da API
            json: Corpo da requisicao
            params: Query parameters
            headers: Headers adicionais
            timeout: Timeout especifico

        Returns:
            Dict com resposta
        """
        return self._make_request('PUT', endpoint, json=json, params=params, headers=headers, timeout=timeout)

    def delete(
        self,
        endpoint: str,
        params: Dict = None,
        headers: Dict = None,
        timeout: float = None
    ) -> Dict[str, Any]:
        """
        Faz requisicao DELETE.

        Args:
            endpoint: Endpoint da API
            params: Query parameters
            headers: Headers adicionais
            timeout: Timeout especifico

        Returns:
            Dict com resposta
        """
        return self._make_request('DELETE', endpoint, params=params, headers=headers, timeout=timeout)

    # ===== Endpoints especificos =====

    def verify_license(
        self,
        username: str = None,
        password: str = None,
        email: str = None,
        mfa_token: str = None,
        auth_token: str = None,
        license_key: str = None,
        app_code: str = None,
        machine_id: str = None,
        hostname: str = None,
        os_info: str = None,
        hardware_components: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Verifica licenca do usuario.

        Args:
            username: Nome de usuario
            password: Senha
            email: Email (alternativa ao username)
            mfa_token: Token MFA de 6 digitos (se MFA habilitado)
            auth_token: Token de autenticacao (alternativa a username/password)
            license_key: Chave de licenca (obrigatoria na primeira execucao)
            app_code: Codigo da aplicacao
            machine_id: ID da maquina
            hostname: Nome do computador
            os_info: Informacoes do SO
            hardware_components: Componentes de hardware

        Returns:
            Dict com resultado da verificacao incluindo session_token
        """
        payload = {
            'app_code': app_code,
            'machine_id': machine_id,
        }

        if auth_token:
            payload['auth_token'] = auth_token
        if username:
            payload['username'] = username
        if email:
            payload['email'] = email
        if password:
            payload['password'] = password
        if mfa_token:
            payload['mfa_token'] = mfa_token
        if license_key:
            payload['license_key'] = license_key
        if hostname:
            payload['hostname'] = hostname
        if os_info:
            payload['os_info'] = os_info
        if hardware_components:
            payload['hardware_components'] = hardware_components

        response = self.post('/license/verify', json=payload)

        # Salvar session_token se presente
        if 'session_token' in response:
            self._session_token = response['session_token']

        return response

    def login(
        self,
        username: str = None,
        password: str = None,
        email: str = None,
        mfa_token: str = None
    ) -> Dict[str, Any]:
        """
        Realiza login.

        Args:
            username: Nome de usuario
            password: Senha
            email: Email (alternativa ao username)
            mfa_token: Token MFA (se habilitado)

        Returns:
            Dict com tokens de sessao
        """
        payload = {'password': password}

        if username:
            payload['username'] = username
        if email:
            payload['email'] = email
        if mfa_token:
            payload['mfa_token'] = mfa_token

        response = self.post('/auth/login', json=payload)

        # Salvar token de sessao
        if 'session_token' in response:
            self._session_token = response['session_token']

        return response

    def logout(self) -> Dict[str, Any]:
        """
        Realiza logout.

        Returns:
            Dict com resultado
        """
        response = self.post('/auth/logout')
        self._session_token = None
        return response

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Renova token de sessao.

        Args:
            refresh_token: Token de refresh

        Returns:
            Dict com novos tokens
        """
        response = self.post('/auth/refresh', json={'refresh_token': refresh_token})

        # Atualizar token de sessao
        if 'session_token' in response:
            self._session_token = response['session_token']

        return response

    def get_me(self) -> Dict[str, Any]:
        """
        Obtem informacoes do usuario atual.

        Returns:
            Dict com dados do usuario
        """
        return self.get('/auth/me')

    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Altera senha do usuario.

        Args:
            current_password: Senha atual
            new_password: Nova senha

        Returns:
            Dict com resultado
        """
        return self.post('/auth/change-password', json={
            'current_password': current_password,
            'new_password': new_password
        })

    def change_password_required(
        self,
        password_change_token: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        Altera senha obrigatoria (primeiro login ou reset por admin).

        Args:
            password_change_token: Token recebido na resposta PASSWORD_CHANGE_REQUIRED
            new_password: Nova senha

        Returns:
            Dict com tokens de sessao
        """
        response = self.post('/auth/change-password-required', json={
            'password_change_token': password_change_token,
            'new_password': new_password
        })

        # Salvar token de sessao
        if 'session_token' in response:
            self._session_token = response['session_token']

        return response

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Solicita reset de senha.

        Envia email com link para redefinir a senha.

        Args:
            email: Email do usuario

        Returns:
            Dict com resultado da solicitacao
        """
        return self.post('/auth/forgot-password', json={'email': email})

    def setup_mfa(self) -> Dict[str, Any]:
        """
        Inicia configuracao de MFA.

        Returns:
            Dict com secret e QR code
        """
        return self.post('/auth/mfa/setup')

    def setup_mfa_required(self, mfa_setup_token: str, app_code: str = None) -> Dict[str, Any]:
        """
        Inicia configuracao de MFA obrigatorio.

        Args:
            mfa_setup_token: Token recebido na resposta MFA_SETUP_REQUIRED
            app_code: Codigo da aplicacao (para exibir nome correto no Google Authenticator)

        Returns:
            Dict com secret e QR code
        """
        payload = {'mfa_setup_token': mfa_setup_token}
        if app_code:
            payload['app_code'] = app_code
        return self.post('/auth/mfa/setup-required', json=payload)

    def confirm_mfa_required(self, mfa_setup_token: str, mfa_code: str) -> Dict[str, Any]:
        """
        Confirma MFA obrigatorio.

        IMPORTANTE: Este metodo NAO retorna session_token.
        Apos MFA configurado, chame verify_license() para obter session_token.

        Args:
            mfa_setup_token: Token recebido na resposta MFA_SETUP_REQUIRED
            mfa_code: Codigo MFA de 6 digitos

        Returns:
            Dict com:
            - auth_token: Token temporario para usar em verify_license()
            - recovery_codes: Codigos de recuperacao MFA
            - next_step: 'LICENSE_VALIDATION'
        """
        response = self.post('/auth/mfa/confirm-required-setup', json={
            'mfa_setup_token': mfa_setup_token,
            'mfa_code': mfa_code
        })

        # NAO salvar token - auth_token e temporario
        # O session_token sera obtido em verify_license()

        return response

    def enable_mfa(self, token: str) -> Dict[str, Any]:
        """
        Habilita MFA com token de verificacao.

        Args:
            token: Token TOTP de 6 digitos

        Returns:
            Dict com recovery codes
        """
        return self.post('/auth/mfa/enable', json={'token': token})

    def verify_mfa(
        self,
        username: str,
        password: str,
        mfa_token: str = None,
        recovery_code: str = None
    ) -> Dict[str, Any]:
        """
        Verifica token MFA durante login.

        Usado quando login retorna mfa_required=true.

        Args:
            username: Nome de usuario ou email
            password: Senha
            mfa_token: Token TOTP de 6 digitos
            recovery_code: Codigo de recuperacao (alternativa ao mfa_token)

        Returns:
            Dict com session_token e refresh_token
        """
        payload = {
            'username': username,
            'password': password
        }

        if mfa_token:
            payload['mfa_token'] = mfa_token
        if recovery_code:
            payload['recovery_code'] = recovery_code

        response = self.post('/auth/mfa/verify', json=payload)

        # Salvar token de sessao
        if 'session_token' in response:
            self._session_token = response['session_token']

        return response

    def disable_mfa(self, password: str, token: str) -> Dict[str, Any]:
        """
        MFA e obrigatorio e nao pode ser desabilitado.

        Este metodo existe apenas para compatibilidade da API,
        mas sempre lancara excecao.

        Raises:
            Exception: Sempre, pois MFA e obrigatorio
        """
        raise Exception("MFA e obrigatorio neste sistema e nao pode ser desabilitado")

    def get_sessions(self) -> Dict[str, Any]:
        """
        Lista sessoes ativas.

        Returns:
            Dict com lista de sessoes
        """
        return self.get('/auth/sessions')

    def revoke_session(self, session_id: int) -> Dict[str, Any]:
        """
        Revoga uma sessao especifica.

        Args:
            session_id: ID da sessao

        Returns:
            Dict com resultado
        """
        return self.delete(f'/auth/sessions/{session_id}')

    def revoke_all_sessions(self) -> Dict[str, Any]:
        """
        Revoga todas as outras sessoes.

        Returns:
            Dict com resultado
        """
        return self.delete('/auth/sessions')

    def get_app_config(self, app_code: str) -> Dict[str, Any]:
        """
        Obtem configuracao da aplicacao.

        Args:
            app_code: Codigo da aplicacao

        Returns:
            Dict com configuracao
        """
        return self.get('/app/config/get', params={'app_code': app_code})

    def get_machine_info(self, app_code: str) -> Dict[str, Any]:
        """
        Obtem informacoes da maquina registrada.

        Args:
            app_code: Codigo da aplicacao

        Returns:
            Dict com informacoes da maquina
        """
        return self.get('/machine/info', params={'app_code': app_code})

    def get_health(self) -> Dict[str, Any]:
        """
        Verifica saude da API.

        Returns:
            Dict com status
        """
        return self.get('/health')

    def close(self):
        """Fecha a sessao HTTP."""
        self._session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
