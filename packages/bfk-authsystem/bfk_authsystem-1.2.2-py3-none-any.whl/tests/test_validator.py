"""
Testes para validator.py - LicenseValidator.
"""
import pytest
import responses
from unittest.mock import patch, Mock, MagicMock

from bfk_authsystem.validator import LicenseValidator, create_validator
from bfk_authsystem.models import ValidationResult, AuthTokens
from bfk_authsystem.exceptions import (
    AuthSystemError,
    AuthenticationError,
    NetworkError,
    MFARequiredError
)
from tests.conftest import (
    TEST_BASE_URL,
    TEST_APP_CODE,
    TEST_USERNAME,
    TEST_PASSWORD,
    TEST_SESSION_TOKEN,
    TEST_REFRESH_TOKEN,
    TEST_MFA_TOKEN,
    TEST_LICENSE_KEY,
    TEST_MACHINE_ID,
    license_verify_success_response,
    login_success_response,
    mfa_required_response,
    health_response,
    add_health_response,
    add_license_verify_response
)


class TestLicenseValidatorInit:
    """Testes para inicializacao do LicenseValidator."""

    def test_init_basic(self, mock_hardware):
        """Inicializacao basica."""
        validator = LicenseValidator(
            server_url=TEST_BASE_URL,
            app_code=TEST_APP_CODE,
            cache_enabled=False
        )

        assert validator.server_url == TEST_BASE_URL
        assert validator.app_code == TEST_APP_CODE
        assert validator.machine_id == TEST_MACHINE_ID

        validator.close()

    def test_init_with_cache_disabled(self, mock_hardware):
        """Inicializacao com cache desabilitado."""
        validator = LicenseValidator(
            server_url=TEST_BASE_URL,
            app_code=TEST_APP_CODE,
            cache_enabled=False
        )

        assert validator._cache is None

        validator.close()

    def test_properties(self, mock_hardware):
        """Propriedades do validador."""
        validator = LicenseValidator(
            server_url=TEST_BASE_URL,
            app_code=TEST_APP_CODE,
            cache_enabled=False
        )

        assert validator.machine_id == TEST_MACHINE_ID
        assert validator.hostname == 'TEST-PC'
        assert validator.os_info == 'Windows 10 Pro'
        assert 'cpu' in validator.hardware_components
        assert validator.current_user is None
        assert validator.app_config is None

        validator.close()


class TestLicenseValidatorVerify:
    """Testes para verificacao de licenca."""

    @responses.activate
    def test_verify_success(self, license_validator):
        """Verificacao de licenca com sucesso."""
        add_license_verify_response(responses)

        result = license_validator.verify(
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            mfa_token=TEST_MFA_TOKEN
        )

        assert result.valid is True

    @responses.activate
    def test_verify_invalid_credentials(self, license_validator):
        """Verificacao com credenciais invalidas."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/license/verify',
            json={
                'success': False,
                'code': 'INVALID_CREDENTIALS',
                'message': 'Credenciais invalidas'
            },
            status=401
        )

        with pytest.raises(AuthenticationError):
            license_validator.verify(
                username=TEST_USERNAME,
                password='wrong'
            )

    @responses.activate
    def test_verify_network_error(self, license_validator):
        """Verificacao com erro de rede."""
        import requests
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/license/verify',
            body=requests.exceptions.ConnectionError()
        )

        with pytest.raises(NetworkError):
            license_validator.verify(
                username=TEST_USERNAME,
                password=TEST_PASSWORD
            )


class TestLicenseValidatorAuthenticate:
    """Testes para autenticacao."""

    @responses.activate
    def test_authenticate_success(self, license_validator):
        """Autenticacao com sucesso."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=login_success_response(),
            status=200
        )
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/me',
            json={
                'success': True,
                'user': {
                    'id': 1,
                    'username': TEST_USERNAME,
                    'email': 'test@example.com'
                }
            },
            status=200
        )

        tokens = license_validator.authenticate(
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            mfa_token=TEST_MFA_TOKEN
        )

        assert tokens.session_token == TEST_SESSION_TOKEN
        assert tokens.refresh_token == TEST_REFRESH_TOKEN

    @responses.activate
    def test_authenticate_mfa_required(self, license_validator):
        """Autenticacao requer MFA."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=mfa_required_response(),
            status=401
        )

        # MFA required retorna dados para tratamento pelo cliente
        tokens = license_validator.authenticate(
            username=TEST_USERNAME,
            password=TEST_PASSWORD
        )

        # Nao ha token porque MFA e necessario (pode ser None ou string vazia)
        assert not tokens.session_token


class TestLicenseValidatorSessions:
    """Testes para gerenciamento de sessoes."""

    @responses.activate
    def test_get_active_sessions(self, license_validator):
        """Lista sessoes ativas."""
        # Login primeiro
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=login_success_response(),
            status=200
        )
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/me',
            json={'user': {}},
            status=200
        )
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/sessions',
            json={
                'success': True,
                'sessions': [
                    {'id': 1, 'device_info': 'Chrome', 'is_current': True},
                    {'id': 2, 'device_info': 'Firefox', 'is_current': False}
                ]
            },
            status=200
        )

        license_validator.authenticate(TEST_USERNAME, TEST_PASSWORD, mfa_token=TEST_MFA_TOKEN)
        sessions = license_validator.get_active_sessions()

        assert len(sessions) == 2

    @responses.activate
    def test_revoke_session(self, license_validator):
        """Revoga sessao especifica."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=login_success_response(),
            status=200
        )
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/me',
            json={'user': {}},
            status=200
        )
        responses.add(
            responses.DELETE,
            f'{TEST_BASE_URL}/auth/sessions/2',
            json={'success': True},
            status=200
        )

        license_validator.authenticate(TEST_USERNAME, TEST_PASSWORD, mfa_token=TEST_MFA_TOKEN)
        result = license_validator.revoke_session(2)

        assert result is True


class TestLicenseValidatorLogout:
    """Testes para logout."""

    @responses.activate
    def test_logout(self, license_validator):
        """Logout limpa tokens."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=login_success_response(),
            status=200
        )
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/me',
            json={'user': {}},
            status=200
        )
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/logout',
            json={'success': True},
            status=200
        )

        license_validator.authenticate(TEST_USERNAME, TEST_PASSWORD, mfa_token=TEST_MFA_TOKEN)
        license_validator.logout()

        assert license_validator._api.session_token is None
        assert license_validator.current_user is None


class TestLicenseValidatorOnlineCheck:
    """Testes para verificacao de conectividade."""

    @responses.activate
    def test_is_online_true(self, license_validator):
        """Servidor acessivel."""
        add_health_response(responses)

        assert license_validator.is_online is True

    @responses.activate
    def test_is_online_false(self, license_validator):
        """Servidor inacessivel."""
        import requests
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/health',
            body=requests.exceptions.ConnectionError()
        )

        assert license_validator.is_online is False


class TestLicenseValidatorMFA:
    """Testes para operacoes MFA."""

    @responses.activate
    def test_setup_mfa(self, license_validator):
        """Setup MFA retorna info."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=login_success_response(),
            status=200
        )
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/me',
            json={'user': {}},
            status=200
        )
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/mfa/setup',
            json={
                'success': True,
                'secret': 'JBSWY3DPEHPK3PXP',
                'qr_code': 'data:image/png;base64,...'
            },
            status=200
        )

        license_validator.authenticate(TEST_USERNAME, TEST_PASSWORD, mfa_token=TEST_MFA_TOKEN)
        mfa_info = license_validator.setup_mfa()

        assert mfa_info.secret == 'JBSWY3DPEHPK3PXP'

    @responses.activate
    def test_enable_mfa(self, license_validator):
        """Habilita MFA retorna recovery codes."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=login_success_response(),
            status=200
        )
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/me',
            json={'user': {}},
            status=200
        )
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/mfa/enable',
            json={
                'success': True,
                'recovery_codes': ['CODE1', 'CODE2', 'CODE3']
            },
            status=200
        )

        license_validator.authenticate(TEST_USERNAME, TEST_PASSWORD, mfa_token=TEST_MFA_TOKEN)
        codes = license_validator.enable_mfa('123456')

        assert len(codes) == 3


class TestLicenseValidatorChangePassword:
    """Testes para troca de senha."""

    @responses.activate
    def test_change_password(self, license_validator):
        """Troca de senha com sucesso."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=login_success_response(),
            status=200
        )
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/me',
            json={'user': {}},
            status=200
        )
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/change-password',
            json={'success': True},
            status=200
        )

        license_validator.authenticate(TEST_USERNAME, TEST_PASSWORD, mfa_token=TEST_MFA_TOKEN)
        result = license_validator.change_password('OldPass', 'NewPass123!')

        assert result is True


class TestCreateValidator:
    """Testes para funcao factory."""

    def test_create_validator(self, mock_hardware):
        """Cria validador via factory."""
        validator = create_validator(
            server_url=TEST_BASE_URL,
            app_code=TEST_APP_CODE,
            cache_enabled=False
        )

        assert isinstance(validator, LicenseValidator)
        assert validator.app_code == TEST_APP_CODE

        validator.close()


class TestLicenseValidatorContextManager:
    """Testes para context manager."""

    def test_context_manager(self, mock_hardware):
        """Uso como context manager."""
        with LicenseValidator(
            server_url=TEST_BASE_URL,
            app_code=TEST_APP_CODE,
            cache_enabled=False
        ) as validator:
            assert validator.app_code == TEST_APP_CODE


class TestTryCachedSession:
    """Testes para _try_cached_session() - bug de sessao revogada."""

    @responses.activate
    def test_session_revoked_returns_false(self, mock_hardware):
        """
        Bug fix: Quando servidor retorna SESSION_REVOKED no refresh,
        _try_cached_session() deve retornar False (nao usar cache).
        """
        from datetime import datetime

        # Criar validador com cache
        validator = LicenseValidator(
            server_url=TEST_BASE_URL,
            app_code=TEST_APP_CODE,
            cache_enabled=True
        )

        # Simular cache valido
        mock_cache = Mock()
        mock_cache.load_verification.return_value = Mock(
            valid=True,
            reauth_days=30,
            days_since_auth=1,
            username=TEST_USERNAME,
            license_key=TEST_LICENSE_KEY,
            app_code=TEST_APP_CODE,
            app_config='{}',
            hardware_validation_token=None,
            last_verification=datetime.now().isoformat()
        )
        mock_cache.load_tokens.return_value = Mock(
            session_token=TEST_SESSION_TOKEN,
            refresh_token=TEST_REFRESH_TOKEN
        )
        validator._cache = mock_cache

        # Mock API que retorna SESSION_REVOKED (sessao revogada pelo admin)
        mock_api = Mock()
        error = AuthenticationError("Sessao foi revogada")
        error.code = 'SESSION_REVOKED'
        mock_api.refresh_token.side_effect = error
        validator._api = mock_api

        # Deve retornar False - NAO usar cache quando sessao foi revogada
        result = validator._try_cached_session()

        assert result is False, "Cache nao deve ser usado quando sessao foi revogada"

        validator.close()

    @responses.activate
    def test_refresh_token_expired_uses_cache(self, mock_hardware):
        """
        Quando refresh token expira normalmente (REFRESH_TOKEN_EXPIRED),
        pode usar cache se ainda tem dias de reauth.
        """
        from datetime import datetime

        validator = LicenseValidator(
            server_url=TEST_BASE_URL,
            app_code=TEST_APP_CODE,
            cache_enabled=True
        )

        # Simular cache valido
        mock_cache = Mock()
        mock_cache.load_verification.return_value = Mock(
            valid=True,
            reauth_days=30,
            days_since_auth=1,
            username=TEST_USERNAME,
            license_key=TEST_LICENSE_KEY,
            app_code=TEST_APP_CODE,
            app_config='{}',
            hardware_validation_token=None,
            last_verification=datetime.now().isoformat()
        )
        mock_cache.load_tokens.return_value = Mock(
            session_token=TEST_SESSION_TOKEN,
            refresh_token=TEST_REFRESH_TOKEN
        )
        validator._cache = mock_cache

        # Mock API - refresh token expirou normalmente
        mock_api = Mock()
        error = AuthenticationError("Refresh token expirado")
        error.code = 'REFRESH_TOKEN_EXPIRED'
        mock_api.refresh_token.side_effect = error
        validator._api = mock_api

        # Deve retornar True - token expirou mas ainda tem dias de reauth
        result = validator._try_cached_session()

        assert result is True, "Cache deve ser usado quando token expirou normalmente"

        validator.close()

    @responses.activate
    def test_server_offline_uses_cache(self, mock_hardware):
        """
        Quando servidor esta offline, pode usar cache (comportamento correto).
        """
        from datetime import datetime

        validator = LicenseValidator(
            server_url=TEST_BASE_URL,
            app_code=TEST_APP_CODE,
            cache_enabled=True
        )

        # Simular cache valido
        mock_cache = Mock()
        mock_cache.load_verification.return_value = Mock(
            valid=True,
            reauth_days=30,
            days_since_auth=1,
            username=TEST_USERNAME,
            license_key=TEST_LICENSE_KEY,
            app_code=TEST_APP_CODE,
            app_config='{}',
            hardware_validation_token=None,
            last_verification=datetime.now().isoformat()
        )
        mock_cache.load_tokens.return_value = Mock(
            session_token=TEST_SESSION_TOKEN,
            refresh_token=TEST_REFRESH_TOKEN
        )
        validator._cache = mock_cache

        # Mock API - servidor offline
        mock_api = Mock()
        mock_api.refresh_token.side_effect = NetworkError("Connection refused")
        validator._api = mock_api

        # Deve retornar True - servidor offline, pode usar cache
        result = validator._try_cached_session()

        assert result is True, "Cache deve ser usado quando servidor esta offline"

        validator.close()
