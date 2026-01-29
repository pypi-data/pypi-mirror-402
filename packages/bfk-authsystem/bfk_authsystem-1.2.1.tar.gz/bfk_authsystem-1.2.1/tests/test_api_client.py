"""
Testes para api_client.py - Cliente HTTP da API.
"""
import pytest
import responses
from unittest.mock import patch, Mock
import requests

from bfk_authsystem.api_client import APIClient
from bfk_authsystem.exceptions import (
    AuthSystemError,
    AuthenticationError,
    NetworkError,
    ServerError,
    TimeoutError as AuthTimeoutError
)
from tests.conftest import (
    TEST_BASE_URL,
    TEST_USERNAME,
    TEST_PASSWORD,
    TEST_SESSION_TOKEN,
    TEST_REFRESH_TOKEN,
    TEST_MFA_TOKEN,
    TEST_APP_CODE,
    TEST_MACHINE_ID,
    TEST_LICENSE_KEY,
    success_response,
    error_response,
    login_success_response,
    mfa_required_response,
    license_verify_success_response,
    health_response,
    add_login_response,
    add_health_response
)


class TestAPIClientInit:
    """Testes para inicializacao do APIClient."""

    def test_init_with_defaults(self):
        """Inicializacao com valores padrao."""
        client = APIClient(base_url=TEST_BASE_URL)

        assert client.base_url == TEST_BASE_URL
        assert client.timeout == 30.0
        assert client.session_token is None
        assert client.verify_ssl is True

        client.close()

    def test_init_with_custom_config(self, retry_config, circuit_config):
        """Inicializacao com configuracoes customizadas."""
        client = APIClient(
            base_url=TEST_BASE_URL,
            timeout=10.0,
            retry_config=retry_config,
            circuit_config=circuit_config,
            session_token='custom-token',
            verify_ssl=False
        )

        assert client.timeout == 10.0
        assert client.session_token == 'custom-token'
        assert client.verify_ssl is False

        client.close()

    def test_base_url_trailing_slash(self):
        """URL base remove barra final."""
        client = APIClient(base_url='http://example.com/api/v1/')

        assert client.base_url == 'http://example.com/api/v1'

        client.close()


class TestAPIClientBuildUrl:
    """Testes para construcao de URL."""

    def test_build_url_with_leading_slash(self, api_client):
        """Endpoint com barra inicial."""
        url = api_client._build_url('/auth/login')
        assert url == f'{TEST_BASE_URL}/auth/login'

    def test_build_url_without_leading_slash(self, api_client):
        """Endpoint sem barra inicial."""
        url = api_client._build_url('auth/login')
        assert url == f'{TEST_BASE_URL}/auth/login'


class TestAPIClientHeaders:
    """Testes para geracao de headers."""

    def test_headers_without_token(self, api_client):
        """Headers sem token de sessao."""
        headers = api_client._get_headers()
        assert 'Authorization' not in headers

    def test_headers_with_token(self, api_client_with_token):
        """Headers com token de sessao."""
        headers = api_client_with_token._get_headers()
        assert 'Authorization' in headers
        assert headers['Authorization'] == f'Bearer {TEST_SESSION_TOKEN}'

    def test_headers_with_extra(self, api_client):
        """Headers com valores adicionais."""
        headers = api_client._get_headers({'X-Custom': 'value'})
        assert headers['X-Custom'] == 'value'


class TestAPIClientLogin:
    """Testes para endpoint de login."""

    @responses.activate
    def test_login_success(self, api_client):
        """Login com sucesso."""
        add_login_response(responses)

        result = api_client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        assert result['success'] is True
        assert 'session_token' in result
        assert api_client.session_token == TEST_SESSION_TOKEN

    @responses.activate
    def test_login_with_mfa(self, api_client):
        """Login com MFA token."""
        add_login_response(responses)

        result = api_client.login(
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            mfa_token=TEST_MFA_TOKEN
        )

        assert result['success'] is True

    @responses.activate
    def test_login_mfa_required(self, api_client):
        """Login retorna MFA required."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=mfa_required_response(),
            status=401
        )

        result = api_client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        assert result['code'] == 'MFA_REQUIRED'
        assert result['mfa_required'] is True

    @responses.activate
    def test_login_invalid_credentials(self, api_client):
        """Login com credenciais invalidas."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/login',
            json=error_response('INVALID_CREDENTIALS', 'Credenciais invalidas'),
            status=401
        )

        with pytest.raises(AuthenticationError) as exc_info:
            api_client.login(username=TEST_USERNAME, password='wrong')

        assert exc_info.value.code == 'INVALID_CREDENTIALS'

    @responses.activate
    def test_login_with_email(self, api_client):
        """Login com email em vez de username."""
        add_login_response(responses)

        result = api_client.login(email='test@example.com', password=TEST_PASSWORD)

        assert result['success'] is True


class TestAPIClientLogout:
    """Testes para endpoint de logout."""

    @responses.activate
    def test_logout_success(self, api_client_with_token):
        """Logout com sucesso."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/logout',
            json=success_response(),
            status=200
        )

        result = api_client_with_token.logout()

        assert result['success'] is True
        assert api_client_with_token.session_token is None


class TestAPIClientRefreshToken:
    """Testes para endpoint de refresh token."""

    @responses.activate
    def test_refresh_token_success(self, api_client):
        """Refresh token com sucesso."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/refresh',
            json={
                'success': True,
                'session_token': 'new-session-token',
                'refresh_token': 'new-refresh-token'
            },
            status=200
        )

        result = api_client.refresh_token(TEST_REFRESH_TOKEN)

        assert result['success'] is True
        assert api_client.session_token == 'new-session-token'


class TestAPIClientVerifyLicense:
    """Testes para endpoint de verificacao de licenca."""

    @responses.activate
    def test_verify_license_success(self, api_client):
        """Verificacao de licenca com sucesso."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/license/verify',
            json=license_verify_success_response(),
            status=200
        )

        result = api_client.verify_license(
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            mfa_token=TEST_MFA_TOKEN,
            license_key=TEST_LICENSE_KEY,
            app_code=TEST_APP_CODE,
            machine_id=TEST_MACHINE_ID,
            hostname='TEST-PC',
            os_info='Windows 10'
        )

        assert result['success'] is True
        assert result['valid'] is True
        assert 'license' in result
        assert 'machine' in result

    @responses.activate
    def test_verify_license_without_license_key(self, api_client):
        """Verificacao sem license_key na primeira execucao.

        LICENSE_KEY_REQUIRED retorna dados (nao lanca excecao) para permitir
        o fluxo de UI que solicita a chave ao usuario.
        """
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/license/verify',
            json={
                'success': False,
                'code': 'LICENSE_KEY_REQUIRED',
                'first_run': True,
                'message': 'Informe a chave de licenca'
            },
            status=400
        )

        result = api_client.verify_license(
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            app_code=TEST_APP_CODE,
            machine_id=TEST_MACHINE_ID
        )

        assert result['code'] == 'LICENSE_KEY_REQUIRED'
        assert result['first_run'] == True


class TestAPIClientMFA:
    """Testes para endpoints de MFA."""

    @responses.activate
    def test_setup_mfa(self, api_client_with_token):
        """Setup MFA retorna QR code."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/mfa/setup',
            json={
                'success': True,
                'secret': 'JBSWY3DPEHPK3PXP',
                'qr_code': 'data:image/png;base64,...',
                'provisioning_uri': 'otpauth://totp/...'
            },
            status=200
        )

        result = api_client_with_token.setup_mfa()

        assert result['success'] is True
        assert 'secret' in result

    @responses.activate
    def test_enable_mfa(self, api_client_with_token):
        """Habilita MFA com token valido."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/mfa/enable',
            json={
                'success': True,
                'recovery_codes': ['CODE1', 'CODE2', 'CODE3']
            },
            status=200
        )

        result = api_client_with_token.enable_mfa(token='123456')

        assert result['success'] is True
        assert 'recovery_codes' in result

    @responses.activate
    def test_verify_mfa(self, api_client):
        """Verifica token MFA."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/mfa/verify',
            json=login_success_response(),
            status=200
        )

        result = api_client.verify_mfa(
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            mfa_token='123456'
        )

        assert result['success'] is True
        assert api_client.session_token == TEST_SESSION_TOKEN


class TestAPIClientSessions:
    """Testes para endpoints de sessoes."""

    @responses.activate
    def test_get_sessions(self, api_client_with_token):
        """Lista sessoes ativas."""
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/auth/sessions',
            json={
                'success': True,
                'sessions': [
                    {'id': 1, 'device_info': 'Chrome', 'is_current': True},
                    {'id': 2, 'device_info': 'Firefox', 'is_current': False}
                ],
                'total': 2
            },
            status=200
        )

        result = api_client_with_token.get_sessions()

        assert result['success'] is True
        assert len(result['sessions']) == 2

    @responses.activate
    def test_revoke_session(self, api_client_with_token):
        """Revoga sessao especifica."""
        responses.add(
            responses.DELETE,
            f'{TEST_BASE_URL}/auth/sessions/2',
            json=success_response(),
            status=200
        )

        result = api_client_with_token.revoke_session(session_id=2)

        assert result['success'] is True

    @responses.activate
    def test_revoke_all_sessions(self, api_client_with_token):
        """Revoga todas as sessoes."""
        responses.add(
            responses.DELETE,
            f'{TEST_BASE_URL}/auth/sessions',
            json={'success': True, 'revoked_count': 3},
            status=200
        )

        result = api_client_with_token.revoke_all_sessions()

        assert result['success'] is True
        assert result['revoked_count'] == 3


class TestAPIClientHealth:
    """Testes para endpoint de health."""

    @responses.activate
    def test_get_health(self, api_client):
        """Health check retorna status."""
        add_health_response(responses)

        result = api_client.get_health()

        assert result['status'] == 'healthy'


class TestAPIClientErrors:
    """Testes para tratamento de erros."""

    @responses.activate
    def test_server_error(self, api_client):
        """Erro 500 levanta ServerError."""
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/health',
            json={'message': 'Internal Server Error'},
            status=500
        )

        with pytest.raises(ServerError):
            api_client.get_health()

    @responses.activate
    def test_timeout_error(self, api_client):
        """Timeout levanta TimeoutError."""
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/health',
            body=requests.exceptions.Timeout()
        )

        with pytest.raises(AuthTimeoutError):
            api_client.get_health()

    @responses.activate
    def test_connection_error(self, api_client):
        """Erro de conexao levanta NetworkError."""
        responses.add(
            responses.GET,
            f'{TEST_BASE_URL}/health',
            body=requests.exceptions.ConnectionError()
        )

        with pytest.raises(NetworkError):
            api_client.get_health()


class TestAPIClientContextManager:
    """Testes para context manager."""

    @responses.activate
    def test_context_manager(self):
        """Uso como context manager."""
        add_health_response(responses)

        with APIClient(base_url=TEST_BASE_URL) as client:
            result = client.get_health()
            assert result['status'] == 'healthy'


class TestAPIClientChangePassword:
    """Testes para endpoints de troca de senha."""

    @responses.activate
    def test_change_password(self, api_client_with_token):
        """Troca de senha com sucesso."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/change-password',
            json=success_response(),
            status=200
        )

        result = api_client_with_token.change_password(
            current_password='OldPass123',
            new_password='NewPass456'
        )

        assert result['success'] is True

    @responses.activate
    def test_change_password_required(self, api_client):
        """Troca de senha obrigatoria."""
        responses.add(
            responses.POST,
            f'{TEST_BASE_URL}/auth/change-password-required',
            json=login_success_response(),
            status=200
        )

        result = api_client.change_password_required(
            password_change_token='change-token-123',
            new_password='NewPass456'
        )

        assert result['success'] is True
        assert api_client.session_token == TEST_SESSION_TOKEN
