"""
Testes para exceptions.py - Excecoes customizadas.
"""
import pytest

from bfk_authsystem.exceptions import (
    AuthSystemError,
    AuthenticationError,
    MFAError,
    MFARequiredError,
    MFASetupRequiredError,
    LicenseError,
    LicenseExpiredError,
    LicenseNotFoundError,
    MachineLimitError,
    NetworkError,
    ServerError,
    TimeoutError,
    CircuitBreakerOpenError,
    CacheError,
    CacheExpiredError,
    CacheCorruptedError,
    ConfigurationError,
    HardwareError,
    ValidationError,
    PasswordChangeRequiredError,
    ReauthenticationRequiredError,
    ERROR_CODE_MAP,
    raise_for_error_code
)


class TestAuthSystemError:
    """Testes para excecao base."""

    def test_basic_error(self):
        """Erro basico com mensagem."""
        error = AuthSystemError("Erro de teste")

        assert error.message == "Erro de teste"
        assert error.code == "UNKNOWN_ERROR"
        assert error.details == {}
        assert str(error) == "[UNKNOWN_ERROR] Erro de teste"

    def test_error_with_code(self):
        """Erro com codigo customizado."""
        error = AuthSystemError("Erro", code="CUSTOM_ERROR")

        assert error.code == "CUSTOM_ERROR"
        assert str(error) == "[CUSTOM_ERROR] Erro"

    def test_error_with_details(self):
        """Erro com detalhes."""
        error = AuthSystemError("Erro", details={'field': 'value'})

        assert error.details == {'field': 'value'}

    def test_error_repr(self):
        """Representacao do erro."""
        error = AuthSystemError("Erro", code="TEST")

        assert "AuthSystemError" in repr(error)
        assert "Erro" in repr(error)
        assert "TEST" in repr(error)


class TestAuthenticationError:
    """Testes para erros de autenticacao."""

    def test_default_values(self):
        """Valores padrao."""
        error = AuthenticationError()

        assert error.message == "Falha na autenticacao"
        assert error.code == "AUTH_FAILED"

    def test_custom_message(self):
        """Mensagem customizada."""
        error = AuthenticationError("Credenciais invalidas")

        assert error.message == "Credenciais invalidas"

    def test_is_auth_system_error(self):
        """E subclasse de AuthSystemError."""
        error = AuthenticationError()

        assert isinstance(error, AuthSystemError)


class TestMFAErrors:
    """Testes para erros de MFA."""

    def test_mfa_error(self):
        """Erro MFA basico."""
        error = MFAError()

        assert error.code == "MFA_ERROR"

    def test_mfa_required_error(self):
        """Erro MFA required."""
        error = MFARequiredError()

        assert error.code == "MFA_REQUIRED"
        assert isinstance(error, MFAError)

    def test_mfa_setup_required_error(self):
        """Erro MFA setup required."""
        error = MFASetupRequiredError()

        assert error.code == "MFA_SETUP_REQUIRED"
        assert isinstance(error, MFAError)


class TestLicenseErrors:
    """Testes para erros de licenca."""

    def test_license_error(self):
        """Erro de licenca basico."""
        error = LicenseError()

        assert error.code == "LICENSE_ERROR"

    def test_license_expired_error(self):
        """Erro de licenca expirada."""
        error = LicenseExpiredError()

        assert error.code == "LICENSE_EXPIRED"
        assert isinstance(error, LicenseError)

    def test_license_not_found_error(self):
        """Erro de licenca nao encontrada."""
        error = LicenseNotFoundError()

        assert error.code == "NO_LICENSE"
        assert isinstance(error, LicenseError)

    def test_machine_limit_error(self):
        """Erro de limite de maquinas."""
        error = MachineLimitError()

        assert error.code == "MACHINE_LIMIT"
        assert isinstance(error, LicenseError)


class TestNetworkErrors:
    """Testes para erros de rede."""

    def test_network_error(self):
        """Erro de rede basico."""
        error = NetworkError()

        assert error.code == "NETWORK_ERROR"

    def test_server_error(self):
        """Erro de servidor."""
        error = ServerError()

        assert error.code == "SERVER_ERROR"
        assert isinstance(error, NetworkError)

    def test_timeout_error(self):
        """Erro de timeout."""
        error = TimeoutError()

        assert error.code == "TIMEOUT"
        assert isinstance(error, NetworkError)


class TestCircuitBreakerOpenError:
    """Testes para erro de circuit breaker."""

    def test_default_retry_after(self):
        """Retry after padrao."""
        error = CircuitBreakerOpenError()

        assert error.retry_after == 60
        assert error.details['retry_after'] == 60

    def test_custom_retry_after(self):
        """Retry after customizado."""
        error = CircuitBreakerOpenError(retry_after=30)

        assert error.retry_after == 30


class TestCacheErrors:
    """Testes para erros de cache."""

    def test_cache_error(self):
        """Erro de cache basico."""
        error = CacheError()

        assert error.code == "CACHE_ERROR"

    def test_cache_expired_error(self):
        """Erro de cache expirado."""
        error = CacheExpiredError()

        assert error.code == "CACHE_EXPIRED"
        assert isinstance(error, CacheError)

    def test_cache_corrupted_error(self):
        """Erro de cache corrompido."""
        error = CacheCorruptedError()

        assert error.code == "CACHE_CORRUPTED"
        assert isinstance(error, CacheError)


class TestOtherErrors:
    """Testes para outros tipos de erro."""

    def test_configuration_error(self):
        """Erro de configuracao."""
        error = ConfigurationError()

        assert error.code == "CONFIG_ERROR"

    def test_hardware_error(self):
        """Erro de hardware."""
        error = HardwareError()

        assert error.code == "HARDWARE_ERROR"

    def test_validation_error(self):
        """Erro de validacao."""
        error = ValidationError()

        assert error.code == "VALIDATION_ERROR"

    def test_password_change_required_error(self):
        """Erro de troca de senha obrigatoria."""
        error = PasswordChangeRequiredError()

        assert error.code == "PASSWORD_CHANGE_REQUIRED"

    def test_reauth_required_error(self):
        """Erro de reautenticacao obrigatoria."""
        error = ReauthenticationRequiredError(days_since_auth=35)

        assert error.code == "REAUTH_REQUIRED"
        assert error.days_since_auth == 35
        assert error.details['days_since_auth'] == 35


class TestErrorCodeMap:
    """Testes para mapeamento de codigos de erro."""

    def test_all_codes_mapped(self):
        """Todos os codigos principais estao mapeados."""
        expected_codes = [
            'AUTH_FAILED',
            'INVALID_CREDENTIALS',
            'MFA_REQUIRED',
            'MFA_SETUP_REQUIRED',
            'NO_LICENSE',
            'LICENSE_EXPIRED',
            'MACHINE_LIMIT',
            'NETWORK_ERROR',
            'SERVER_ERROR',
            'TIMEOUT',
            'CACHE_ERROR',
            'CONFIG_ERROR'
        ]

        for code in expected_codes:
            assert code in ERROR_CODE_MAP, f"Codigo {code} nao mapeado"

    def test_mapped_classes_are_correct(self):
        """Classes mapeadas sao corretas."""
        assert ERROR_CODE_MAP['AUTH_FAILED'] == AuthenticationError
        assert ERROR_CODE_MAP['MFA_REQUIRED'] == MFARequiredError
        assert ERROR_CODE_MAP['NO_LICENSE'] == LicenseNotFoundError
        assert ERROR_CODE_MAP['SERVER_ERROR'] == ServerError


class TestRaiseForErrorCode:
    """Testes para funcao raise_for_error_code."""

    def test_raise_known_code(self):
        """Levanta excecao conhecida."""
        with pytest.raises(AuthenticationError):
            raise_for_error_code('AUTH_FAILED')

    def test_raise_unknown_code(self):
        """Levanta AuthSystemError para codigo desconhecido."""
        with pytest.raises(AuthSystemError):
            raise_for_error_code('UNKNOWN_CODE')

    def test_raise_with_message(self):
        """Mensagem customizada."""
        try:
            raise_for_error_code('AUTH_FAILED', message='Erro customizado')
        except AuthenticationError as e:
            assert e.message == 'Erro customizado'

    def test_raise_with_details(self):
        """Detalhes adicionais."""
        try:
            raise_for_error_code('AUTH_FAILED', details={'user': 'test'})
        except AuthenticationError as e:
            assert e.details == {'user': 'test'}
