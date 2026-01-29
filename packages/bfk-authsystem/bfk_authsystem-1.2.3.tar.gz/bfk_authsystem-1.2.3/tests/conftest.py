"""
Configuracao e fixtures para testes pytest do cliente.
"""
import pytest
import responses
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Adicionar path do cliente
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from bfk_authsystem.api_client import APIClient
from bfk_authsystem.validator import LicenseValidator
from bfk_authsystem.retry_handler import RetryConfig
from bfk_authsystem.circuit_breaker import CircuitBreakerConfig
from bfk_authsystem.exceptions import (
    AuthSystemError,
    AuthenticationError,
    NetworkError,
    ServerError
)


# Configuracoes de teste
TEST_BASE_URL = 'http://test-server.local/api/v1'
TEST_APP_CODE = 'TESTAPP'
TEST_USERNAME = 'testuser'
TEST_PASSWORD = 'Test123!@#'
TEST_EMAIL = 'test@example.com'
TEST_MFA_TOKEN = '123456'
TEST_SESSION_TOKEN = 'test-session-token-12345'
TEST_REFRESH_TOKEN = 'test-refresh-token-67890'
TEST_LICENSE_KEY = 'BFK-TEST-1234-5678'
TEST_MACHINE_ID = 'test-machine-id-abcdef'


@pytest.fixture
def retry_config():
    """Configuracao de retry para testes (rapido)."""
    return RetryConfig(
        max_retries=2,
        base_delay=0.1,
        max_delay=0.5,
        backoff_factor=2.0,
        jitter=False
    )


@pytest.fixture
def circuit_config():
    """Configuracao de circuit breaker para testes."""
    return CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=1,
        recovery_timeout=1.0
    )


@pytest.fixture
def api_client(retry_config, circuit_config):
    """Cliente API configurado para testes."""
    client = APIClient(
        base_url=TEST_BASE_URL,
        timeout=5.0,
        retry_config=retry_config,
        circuit_config=circuit_config,
        verify_ssl=False
    )
    yield client
    client.close()


@pytest.fixture
def api_client_with_token(api_client):
    """Cliente API com token de sessao."""
    api_client.session_token = TEST_SESSION_TOKEN
    return api_client


@pytest.fixture
def mock_hardware():
    """Mock para funcoes de hardware."""
    with patch('bfk_authsystem.validator.get_hardware_info') as mock:
        mock.return_value = (
            TEST_MACHINE_ID,
            {
                'cpu': 'Intel Core i7',
                'motherboard': 'ASUS',
                'disk': 'Samsung SSD'
            },
            {
                'hostname': 'TEST-PC',
                'os_info': 'Windows 10 Pro'
            }
        )
        yield mock


@pytest.fixture
def license_validator(mock_hardware, retry_config, circuit_config):
    """Validador de licenca para testes."""
    validator = LicenseValidator(
        server_url=TEST_BASE_URL,
        app_code=TEST_APP_CODE,
        timeout=5.0,
        retry_config=retry_config,
        circuit_config=circuit_config,
        verify_ssl=False,
        cache_enabled=False
    )
    yield validator
    validator.close()


# Respostas mock comuns
def success_response(data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Cria resposta de sucesso."""
    response = {'success': True}
    if data:
        response.update(data)
    return response


def error_response(code: str, message: str = None) -> Dict[str, Any]:
    """Cria resposta de erro."""
    return {
        'success': False,
        'code': code,
        'message': message or f'Erro: {code}'
    }


def login_success_response() -> Dict[str, Any]:
    """Resposta de login com sucesso."""
    return {
        'success': True,
        'session_token': TEST_SESSION_TOKEN,
        'refresh_token': TEST_REFRESH_TOKEN,
        'user': {
            'id': 1,
            'username': TEST_USERNAME,
            'email': TEST_EMAIL,
            'full_name': 'Test User'
        }
    }


def mfa_required_response() -> Dict[str, Any]:
    """Resposta de MFA requerido."""
    return {
        'success': False,
        'code': 'MFA_REQUIRED',
        'mfa_required': True,
        'message': 'Codigo MFA necessario'
    }


def mfa_setup_required_response() -> Dict[str, Any]:
    """Resposta de MFA setup requerido."""
    return {
        'success': False,
        'code': 'MFA_SETUP_REQUIRED',
        'mfa_setup_required': True,
        'mfa_setup_token': 'setup-token-123',
        'message': 'Configuracao de MFA obrigatoria'
    }


def license_verify_success_response() -> Dict[str, Any]:
    """Resposta de verificacao de licenca com sucesso."""
    return {
        'success': True,
        'valid': True,
        'message': 'Licenca valida',
        'license': {
            'license_key': TEST_LICENSE_KEY,
            'user': TEST_USERNAME,
            'app_name': 'Test App',
            'expires_at': '2025-12-31T23:59:59',
            'is_active': True
        },
        'machine': {
            'registered': True,
            'hostname': 'TEST-PC',
            'machine_id': TEST_MACHINE_ID
        },
        'requires_reauth': False,
        'days_since_auth': 0,
        'application': {
            'app_code': TEST_APP_CODE,
            'app_name': 'Test App',
            'mfa_required': True,
            'reauth_days': 30
        }
    }


def license_key_required_response() -> Dict[str, Any]:
    """Resposta de chave de licenca requerida."""
    return {
        'success': False,
        'valid': False,
        'code': 'LICENSE_KEY_REQUIRED',
        'first_run': True,
        'message': 'Informe a chave de licenca recebida por email'
    }


def health_response() -> Dict[str, Any]:
    """Resposta de health check."""
    return {
        'status': 'healthy',
        'database': 'connected',
        'timestamp': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def mock_responses():
    """Ativa mock de responses."""
    with responses.RequestsMock() as rsps:
        yield rsps


def add_login_response(rsps, status=200, body=None):
    """Adiciona mock de resposta de login."""
    rsps.add(
        responses.POST,
        f'{TEST_BASE_URL}/auth/login',
        json=body or login_success_response(),
        status=status
    )


def add_health_response(rsps, status=200, body=None):
    """Adiciona mock de resposta de health."""
    rsps.add(
        responses.GET,
        f'{TEST_BASE_URL}/health',
        json=body or health_response(),
        status=status
    )


def add_license_verify_response(rsps, status=200, body=None):
    """Adiciona mock de resposta de verificacao de licenca."""
    rsps.add(
        responses.POST,
        f'{TEST_BASE_URL}/license/verify',
        json=body or license_verify_success_response(),
        status=status
    )
