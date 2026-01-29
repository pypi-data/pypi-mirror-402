"""
BFK AuthSystem - Biblioteca Cliente Python

Biblioteca para integracao de aplicacoes desktop com o BFK AuthSystem.

Uso basico:
    from bfk_authsystem import LicenseValidator

    validator = LicenseValidator(
        server_url='https://api.example.com/api/v1',
        app_code='MYAPP'
    )

    result = validator.verify(username='user', password='pass')
    if result.valid:
        print('Licenca valida!')
"""

__version__ = '1.2.1'
__author__ = 'BFK'

# Classes principais
from .validator import LicenseValidator, create_validator

# Modelos de dados
from .models import (
    ValidationResult,
    RequiredAction,
    LicenseStatus,
    AppConfig,
    LicenseInfo,
    MachineInfo,
    SessionInfo,
    UserInfo,
    AuthTokens,
    MFASetupInfo
)

# Excecoes
from .exceptions import (
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
    ReauthenticationRequiredError
)

# Hardware
from .hardware import (
    get_hardware_info,
    get_hardware_components,
    generate_machine_id,
    get_system_info
)

# Componentes avancados (para uso customizado)
from .api_client import APIClient
from .cache import CacheManager
from .retry_handler import RetryHandler, RetryConfig, with_retry
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    get_circuit_breaker,
    circuit_protected
)

__all__ = [
    # Versao
    '__version__',

    # Classes principais
    'LicenseValidator',
    'create_validator',

    # Modelos
    'ValidationResult',
    'RequiredAction',
    'LicenseStatus',
    'AppConfig',
    'LicenseInfo',
    'MachineInfo',
    'SessionInfo',
    'UserInfo',
    'AuthTokens',
    'MFASetupInfo',

    # Excecoes
    'AuthSystemError',
    'AuthenticationError',
    'MFAError',
    'MFARequiredError',
    'MFASetupRequiredError',
    'LicenseError',
    'LicenseExpiredError',
    'LicenseNotFoundError',
    'MachineLimitError',
    'NetworkError',
    'ServerError',
    'TimeoutError',
    'CircuitBreakerOpenError',
    'CacheError',
    'CacheExpiredError',
    'CacheCorruptedError',
    'ConfigurationError',
    'HardwareError',
    'ValidationError',
    'PasswordChangeRequiredError',
    'ReauthenticationRequiredError',

    # Hardware
    'get_hardware_info',
    'get_hardware_components',
    'generate_machine_id',
    'get_system_info',

    # Componentes avancados
    'APIClient',
    'CacheManager',
    'RetryHandler',
    'RetryConfig',
    'with_retry',
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitState',
    'get_circuit_breaker',
    'circuit_protected',
]
