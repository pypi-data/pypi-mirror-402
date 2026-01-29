"""
BFK AuthSystem - Excecoes Customizadas

Hierarquia de excecoes para tratamento de erros da biblioteca cliente.
"""


class AuthSystemError(Exception):
    """
    Excecao base para todos os erros do AuthSystem.

    Attributes:
        message: Mensagem de erro descritiva
        code: Codigo de erro para identificacao programatica
        details: Detalhes adicionais do erro (opcional)
    """

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


class AuthenticationError(AuthSystemError):
    """
    Erro de autenticacao.

    Levantado quando:
    - Credenciais invalidas (username/senha)
    - Token de sessao invalido ou expirado
    - Refresh token invalido
    - Usuario inativo ou bloqueado
    """

    def __init__(self, message: str = "Falha na autenticacao",
                 code: str = "AUTH_FAILED", details: dict = None):
        super().__init__(message, code, details)


class MFAError(AuthSystemError):
    """
    Erro relacionado a autenticacao multi-fator.

    Levantado quando:
    - Token MFA invalido
    - MFA ja configurado/nao configurado
    - Recovery code invalido
    - Setup MFA falhou
    """

    def __init__(self, message: str = "Erro de MFA",
                 code: str = "MFA_ERROR", details: dict = None):
        super().__init__(message, code, details)


class MFARequiredError(MFAError):
    """
    MFA e obrigatorio para completar a autenticacao.

    Levantado quando o usuario tem MFA habilitado e precisa
    fornecer o token TOTP para completar o login.
    """

    def __init__(self, message: str = "Verificacao MFA necessaria",
                 code: str = "MFA_REQUIRED", details: dict = None):
        super().__init__(message, code, details)


class MFASetupRequiredError(MFAError):
    """
    Configuracao de MFA e obrigatoria.

    Levantado quando a aplicacao exige MFA mas o usuario
    ainda nao configurou.
    """

    def __init__(self, message: str = "Configuracao de MFA obrigatoria",
                 code: str = "MFA_SETUP_REQUIRED", details: dict = None):
        super().__init__(message, code, details)


class LicenseError(AuthSystemError):
    """
    Erro relacionado a licenca.

    Levantado quando:
    - Usuario nao tem licenca para a aplicacao
    - Licenca expirada
    - Licenca suspensa ou revogada
    - Limite de maquinas atingido
    """

    def __init__(self, message: str = "Erro de licenca",
                 code: str = "LICENSE_ERROR", details: dict = None):
        super().__init__(message, code, details)


class LicenseExpiredError(LicenseError):
    """Licenca expirou."""

    def __init__(self, message: str = "Licenca expirada",
                 code: str = "LICENSE_EXPIRED", details: dict = None):
        super().__init__(message, code, details)


class LicenseNotFoundError(LicenseError):
    """Usuario nao possui licenca para esta aplicacao."""

    def __init__(self, message: str = "Licenca nao encontrada",
                 code: str = "NO_LICENSE", details: dict = None):
        super().__init__(message, code, details)


class MachineLimitError(LicenseError):
    """Limite de maquinas da licenca atingido."""

    def __init__(self, message: str = "Limite de maquinas atingido",
                 code: str = "MACHINE_LIMIT", details: dict = None):
        super().__init__(message, code, details)


class NetworkError(AuthSystemError):
    """
    Erro de rede/conexao.

    Levantado quando:
    - Servidor inacessivel
    - Timeout de conexao
    - Erro de DNS
    - SSL/TLS falhou
    """

    def __init__(self, message: str = "Erro de conexao",
                 code: str = "NETWORK_ERROR", details: dict = None):
        super().__init__(message, code, details)


class ServerError(NetworkError):
    """
    Erro do servidor (5xx).

    Levantado quando o servidor retorna erro interno.
    """

    def __init__(self, message: str = "Erro interno do servidor",
                 code: str = "SERVER_ERROR", details: dict = None):
        super().__init__(message, code, details)


class TimeoutError(NetworkError):
    """Timeout na requisicao."""

    def __init__(self, message: str = "Timeout na requisicao",
                 code: str = "TIMEOUT", details: dict = None):
        super().__init__(message, code, details)


class CircuitBreakerOpenError(AuthSystemError):
    """
    Circuit breaker esta aberto.

    Levantado quando o circuit breaker detectou muitas falhas
    consecutivas e esta bloqueando requisicoes para proteger
    o sistema.

    Attributes:
        retry_after: Segundos ate tentar novamente
    """

    def __init__(self, message: str = "Servico temporariamente indisponivel",
                 code: str = "CIRCUIT_OPEN", retry_after: int = 60,
                 details: dict = None):
        self.retry_after = retry_after
        details = details or {}
        details['retry_after'] = retry_after
        super().__init__(message, code, details)


class CacheError(AuthSystemError):
    """
    Erro de cache local.

    Levantado quando:
    - Falha ao ler/escrever cache
    - Cache corrompido
    - Erro de criptografia
    - Permissao negada
    """

    def __init__(self, message: str = "Erro de cache",
                 code: str = "CACHE_ERROR", details: dict = None):
        super().__init__(message, code, details)


class CacheExpiredError(CacheError):
    """Cache expirou e precisa ser renovado."""

    def __init__(self, message: str = "Cache expirado",
                 code: str = "CACHE_EXPIRED", details: dict = None):
        super().__init__(message, code, details)


class CacheCorruptedError(CacheError):
    """Cache esta corrompido e sera recriado."""

    def __init__(self, message: str = "Cache corrompido",
                 code: str = "CACHE_CORRUPTED", details: dict = None):
        super().__init__(message, code, details)


class ConfigurationError(AuthSystemError):
    """
    Erro de configuracao.

    Levantado quando:
    - Configuracao invalida
    - Parametros obrigatorios ausentes
    - URL do servidor invalida
    - App code invalido
    """

    def __init__(self, message: str = "Erro de configuracao",
                 code: str = "CONFIG_ERROR", details: dict = None):
        super().__init__(message, code, details)


class HardwareError(AuthSystemError):
    """
    Erro ao coletar informacoes de hardware.

    Levantado quando:
    - Falha ao obter machine_id
    - WMI indisponivel (Windows)
    - Permissao insuficiente
    """

    def __init__(self, message: str = "Erro ao coletar hardware",
                 code: str = "HARDWARE_ERROR", details: dict = None):
        super().__init__(message, code, details)


class ValidationError(AuthSystemError):
    """
    Erro de validacao de dados.

    Levantado quando:
    - Dados de entrada invalidos
    - Formato incorreto
    - Valor fora do esperado
    """

    def __init__(self, message: str = "Dados invalidos",
                 code: str = "VALIDATION_ERROR", details: dict = None):
        super().__init__(message, code, details)


class PasswordChangeRequiredError(AuthSystemError):
    """
    Troca de senha obrigatoria.

    Levantado quando o usuario precisa trocar a senha
    antes de continuar usando o sistema.
    """

    def __init__(self, message: str = "Troca de senha obrigatoria",
                 code: str = "PASSWORD_CHANGE_REQUIRED", details: dict = None):
        super().__init__(message, code, details)


class ReauthenticationRequiredError(AuthSystemError):
    """
    Reautenticacao obrigatoria.

    Levantado quando o tempo desde a ultima autenticacao
    excedeu o limite configurado para a aplicacao.
    """

    def __init__(self, message: str = "Reautenticacao necessaria",
                 code: str = "REAUTH_REQUIRED", days_since_auth: int = 0,
                 details: dict = None):
        self.days_since_auth = days_since_auth
        details = details or {}
        details['days_since_auth'] = days_since_auth
        super().__init__(message, code, details)


# Mapeamento de codigos de erro da API para excecoes
ERROR_CODE_MAP = {
    'AUTH_FAILED': AuthenticationError,
    'INVALID_CREDENTIALS': AuthenticationError,
    'USER_INACTIVE': AuthenticationError,
    'SESSION_EXPIRED': AuthenticationError,
    'INVALID_TOKEN': AuthenticationError,
    'MFA_REQUIRED': MFARequiredError,
    'MFA_SETUP_REQUIRED': MFASetupRequiredError,
    'INVALID_MFA_TOKEN': MFAError,
    'MFA_ALREADY_ENABLED': MFAError,
    'MFA_NOT_ENABLED': MFAError,
    'NO_LICENSE': LicenseNotFoundError,
    'LICENSE_EXPIRED': LicenseExpiredError,
    'LICENSE_SUSPENDED': LicenseError,
    'LICENSE_INACTIVE': LicenseError,
    'MACHINE_LIMIT': MachineLimitError,
    'NETWORK_ERROR': NetworkError,
    'SERVER_ERROR': ServerError,
    'TIMEOUT': TimeoutError,
    'CIRCUIT_OPEN': CircuitBreakerOpenError,
    'CACHE_ERROR': CacheError,
    'CACHE_EXPIRED': CacheExpiredError,
    'CACHE_CORRUPTED': CacheCorruptedError,
    'CONFIG_ERROR': ConfigurationError,
    'HARDWARE_ERROR': HardwareError,
    'VALIDATION_ERROR': ValidationError,
    'PASSWORD_CHANGE_REQUIRED': PasswordChangeRequiredError,
    'REAUTH_REQUIRED': ReauthenticationRequiredError,
}


def raise_for_error_code(code: str, message: str = None, details: dict = None):
    """
    Levanta a excecao apropriada para um codigo de erro.

    Args:
        code: Codigo de erro retornado pela API
        message: Mensagem de erro (opcional)
        details: Detalhes adicionais (opcional)

    Raises:
        Excecao especifica para o codigo ou AuthSystemError
    """
    exception_class = ERROR_CODE_MAP.get(code, AuthSystemError)
    raise exception_class(
        message=message or f"Erro: {code}",
        code=code,
        details=details
    )
