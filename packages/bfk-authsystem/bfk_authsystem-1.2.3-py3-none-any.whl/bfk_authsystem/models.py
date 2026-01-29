"""
BFK AuthSystem - Modelos de Dados

Dataclasses para representar dados retornados pela API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class RequiredAction(Enum):
    """Ações que podem ser requeridas após verificação."""
    NONE = "none"
    CHANGE_PASSWORD = "change_password"
    SETUP_MFA = "setup_mfa"
    VERIFY_MFA = "verify_mfa"
    REAUTH = "reauth"


class LicenseStatus(Enum):
    """Status possíveis de uma licença."""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


@dataclass
class AppConfig:
    """
    Configuração de uma aplicação.

    Attributes:
        app_code: Código único da aplicação
        app_name: Nome interno da aplicação
        display_name: Nome de exibição para usuários
        company_name: Nome da empresa
        support_email: Email de suporte
        primary_color: Cor primária (hex)
        secondary_color: Cor secundária (hex)
        accent_color: Cor de destaque (hex)
        logo_url: URL do logo (opcional)
        welcome_message: Mensagem de boas-vindas
        reauth_days: Dias para reautenticação
        mfa_required: Se MFA é obrigatório
    """
    app_code: str
    app_name: str
    display_name: str
    company_name: str
    support_email: str
    primary_color: str = "#1976D2"
    secondary_color: str = "#424242"
    accent_color: str = "#FF5722"
    logo_url: Optional[str] = None
    welcome_message: str = ""
    reauth_days: int = 30
    mfa_required: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'AppConfig':
        """Cria AppConfig a partir de dicionario da API."""
        return cls(
            app_code=data.get('app_code', ''),
            app_name=data.get('app_name', ''),
            display_name=data.get('display_name', data.get('app_name', '')),
            company_name=data.get('company_name', ''),
            support_email=data.get('support_email', ''),
            primary_color=data.get('primary_color', data.get('colors', {}).get('primary', '#1976D2')),
            secondary_color=data.get('secondary_color', data.get('colors', {}).get('secondary', '#424242')),
            accent_color=data.get('accent_color', data.get('colors', {}).get('accent', '#FF5722')),
            logo_url=data.get('logo_url'),
            welcome_message=data.get('welcome_message', ''),
            reauth_days=data.get('reauth_days', 30),
            mfa_required=data.get('mfa_required', False)
        )

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            'app_code': self.app_code,
            'app_name': self.app_name,
            'display_name': self.display_name,
            'company_name': self.company_name,
            'support_email': self.support_email,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'logo_url': self.logo_url,
            'welcome_message': self.welcome_message,
            'reauth_days': self.reauth_days,
            'mfa_required': self.mfa_required
        }


@dataclass
class MachineInfo:
    """
    Informações da máquina registrada.

    Attributes:
        id: ID no banco de dados
        machine_id: Hash único da máquina
        hostname: Nome do computador
        os_info: Informações do sistema operacional
        registered_at: Data de registro
        last_verification: Última verificação
        hardware_components: Componentes de hardware
    """
    id: int
    machine_id: str
    hostname: str
    os_info: str
    registered_at: datetime
    last_verification: datetime
    hardware_components: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'MachineInfo':
        """Cria MachineInfo a partir de dicionario da API."""
        registered_at = data.get('registered_at')
        if isinstance(registered_at, str):
            registered_at = datetime.fromisoformat(registered_at.replace('Z', '+00:00'))
        elif registered_at is None:
            registered_at = datetime.now()

        last_verification = data.get('last_verification')
        if isinstance(last_verification, str):
            last_verification = datetime.fromisoformat(last_verification.replace('Z', '+00:00'))
        elif last_verification is None:
            last_verification = datetime.now()

        return cls(
            id=data.get('id', 0),
            machine_id=data.get('machine_id', ''),
            hostname=data.get('hostname', ''),
            os_info=data.get('os_info', ''),
            registered_at=registered_at,
            last_verification=last_verification,
            hardware_components=data.get('hardware_components', {})
        )

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'hostname': self.hostname,
            'os_info': self.os_info,
            'registered_at': self.registered_at.isoformat(),
            'last_verification': self.last_verification.isoformat(),
            'hardware_components': self.hardware_components
        }


@dataclass
class LicenseInfo:
    """
    Informações da licença.

    Attributes:
        license_key: Chave da licença
        user: Nome do usuário
        email: Email do usuário
        app_name: Nome da aplicação
        status: Status da licença
        expires_at: Data de revalidação (None = licença vitalícia)
    """
    license_key: str
    user: str
    email: str
    app_name: str
    status: LicenseStatus = LicenseStatus.ACTIVE
    expires_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'LicenseInfo':
        """Cria LicenseInfo a partir de dicionario da API."""
        expires_at = data.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))

        status_str = data.get('status', 'active')
        try:
            status = LicenseStatus(status_str)
        except ValueError:
            status = LicenseStatus.ACTIVE

        return cls(
            license_key=data.get('license_key', ''),
            user=data.get('user', data.get('username', '')),
            email=data.get('email', ''),
            app_name=data.get('app_name', ''),
            status=status,
            expires_at=expires_at
        )

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            'license_key': self.license_key,
            'user': self.user,
            'email': self.email,
            'app_name': self.app_name,
            'status': self.status.value,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @property
    def is_valid(self) -> bool:
        """Verifica se a licença está válida."""
        if self.status != LicenseStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    @property
    def is_lifetime(self) -> bool:
        """Verifica se a licença é vitalícia."""
        return self.expires_at is None


@dataclass
class ValidationResult:
    """
    Resultado da verificação de licença.

    Attributes:
        valid: Se a licença é válida
        message: Mensagem descritiva
        requires_action: Ação requerida
        days_offline: Dias em modo offline
        days_until_reauth: Dias até reautenticação
        days_since_auth: Dias desde última autenticação
        app_config: Configuração da aplicação
        license_info: Informações da licença
        machine_info: Informações da máquina
        error_code: Código de erro (se houver)
        is_offline: Se a verificação foi offline
        mfa_setup_token: Token para setup de MFA obrigatorio
        password_change_token: Token para troca de senha obrigatoria
        hardware_validation_token: Token JWT RS256 para validacao offline de hardware
        schedule_info: Informacoes sobre restricoes de horario da licenca
        auth_token: Token temporario para continuar fluxo (ex: apos MFA valido)
    """
    valid: bool
    message: str
    requires_action: RequiredAction = RequiredAction.NONE
    days_offline: int = 0
    days_until_reauth: int = 30
    days_since_auth: int = 0
    app_config: Optional[AppConfig] = None
    license_info: Optional[LicenseInfo] = None
    machine_info: Optional[MachineInfo] = None
    error_code: Optional[str] = None
    is_offline: bool = False
    mfa_setup_token: Optional[str] = None
    password_change_token: Optional[str] = None
    hardware_validation_token: Optional[str] = None
    schedule_info: Optional[Dict[str, Any]] = None
    auth_token: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'ValidationResult':
        """Cria ValidationResult a partir de dicionario da API."""
        # Determinar acao requerida
        requires_action = RequiredAction.NONE
        requires_action_str = data.get('requires_action', 'none')
        if data.get('requires_reauth'):
            requires_action = RequiredAction.REAUTH
        elif requires_action_str:
            try:
                requires_action = RequiredAction(requires_action_str)
            except ValueError:
                requires_action = RequiredAction.NONE

        # Parse app_config
        app_config = None
        if 'application' in data:
            app_config = AppConfig.from_dict(data['application'])
        elif 'app_config' in data:
            app_config = AppConfig.from_dict(data['app_config'])

        # Parse license_info
        license_info = None
        if 'license' in data:
            license_info = LicenseInfo.from_dict(data['license'])

        # Parse machine_info
        machine_info = None
        if 'machine' in data and data['machine']:
            machine_info = MachineInfo.from_dict(data['machine'])

        return cls(
            valid=data.get('valid', False),
            message=data.get('message', ''),
            requires_action=requires_action,
            days_offline=data.get('days_offline', 0),
            days_until_reauth=data.get('days_until_reauth', 30),
            days_since_auth=data.get('days_since_auth', 0),
            app_config=app_config,
            license_info=license_info,
            machine_info=machine_info,
            error_code=data.get('code'),
            is_offline=data.get('is_offline', False),
            mfa_setup_token=data.get('mfa_setup_token'),
            password_change_token=data.get('password_change_token'),
            hardware_validation_token=data.get('hardware_validation_token'),
            schedule_info=data.get('schedule_info'),
            auth_token=data.get('auth_token')
        )

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            'valid': self.valid,
            'message': self.message,
            'requires_action': self.requires_action.value,
            'days_offline': self.days_offline,
            'days_until_reauth': self.days_until_reauth,
            'days_since_auth': self.days_since_auth,
            'app_config': self.app_config.to_dict() if self.app_config else None,
            'license_info': self.license_info.to_dict() if self.license_info else None,
            'machine_info': self.machine_info.to_dict() if self.machine_info else None,
            'error_code': self.error_code,
            'is_offline': self.is_offline,
            'mfa_setup_token': self.mfa_setup_token,
            'password_change_token': self.password_change_token,
            'hardware_validation_token': self.hardware_validation_token,
            'schedule_info': self.schedule_info,
            'auth_token': self.auth_token
        }


@dataclass
class SessionInfo:
    """
    Informações de uma sessão de usuário.

    Attributes:
        id: ID da sessão
        device_info: Informações do dispositivo
        ip_address: Endereço IP
        created_at: Data de criação
        last_activity: Última atividade
        is_current: Se é a sessão atual
    """
    id: int
    device_info: str
    ip_address: str
    created_at: datetime
    last_activity: datetime
    is_current: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'SessionInfo':
        """Cria SessionInfo a partir de dicionario da API."""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.now()

        last_activity = data.get('last_activity')
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
        elif last_activity is None:
            last_activity = datetime.now()

        return cls(
            id=data.get('id', 0),
            device_info=data.get('device_info', data.get('device', '')),
            ip_address=data.get('ip_address', data.get('ip', '')),
            created_at=created_at,
            last_activity=last_activity,
            is_current=data.get('is_current', False)
        )

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            'id': self.id,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_current': self.is_current
        }


@dataclass
class UserInfo:
    """
    Informações do usuário.

    Attributes:
        id: ID do usuário
        username: Nome de usuário
        email: Email
        full_name: Nome completo
        is_active: Se está ativo
        is_admin: Se é administrador
        mfa_enabled: Se MFA está habilitado
        force_password_change: Se deve trocar senha
        created_at: Data de criação
    """
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool = True
    is_admin: bool = False
    mfa_enabled: bool = False
    force_password_change: bool = False
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'UserInfo':
        """Cria UserInfo a partir de dicionario da API."""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        return cls(
            id=data.get('id', 0),
            username=data.get('username', ''),
            email=data.get('email', ''),
            full_name=data.get('full_name', ''),
            is_active=data.get('is_active', True),
            is_admin=data.get('is_admin', False),
            mfa_enabled=data.get('mfa_enabled', False),
            force_password_change=data.get('force_password_change', False),
            created_at=created_at
        )

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'mfa_enabled': self.mfa_enabled,
            'force_password_change': self.force_password_change,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class AuthTokens:
    """
    Tokens de autenticacao.

    Attributes:
        session_token: Token de sessao para requisicoes (pode ser None em fluxos incompletos)
        refresh_token: Token para renovar sessao (pode ser None em fluxos incompletos)
        expires_at: Quando o session_token expira
        recovery_codes: Codigos de recuperacao MFA (retornados apos setup MFA)
    """
    session_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    recovery_codes: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'AuthTokens':
        """
        Cria AuthTokens a partir de dict.

        Se nao houver session_token na resposta, retorna objeto com valores None.
        Isso e normal em fluxos onde ainda nao ha autenticacao completa.

        Args:
            data: Dict com dados da resposta

        Returns:
            AuthTokens (pode ter todos os campos None se nao houver tokens)
        """
        expires_at = data.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))

        return cls(
            session_token=data.get('session_token'),
            refresh_token=data.get('refresh_token'),
            expires_at=expires_at,
            recovery_codes=data.get('recovery_codes')
        )

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            'session_token': self.session_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'recovery_codes': self.recovery_codes
        }


@dataclass
class MFASetupInfo:
    """
    Informações para configuração de MFA.

    Attributes:
        secret: Chave secreta TOTP
        qr_code: QR Code em base64
        provisioning_uri: URI para apps autenticadores
    """
    secret: str
    qr_code: str
    provisioning_uri: str

    @classmethod
    def from_dict(cls, data: dict) -> 'MFASetupInfo':
        """Cria MFASetupInfo a partir de dicionario da API."""
        return cls(
            secret=data.get('secret', ''),
            qr_code=data.get('qr_code', ''),
            provisioning_uri=data.get('provisioning_uri', data.get('uri', ''))
        )

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            'secret': self.secret,
            'qr_code': self.qr_code,
            'provisioning_uri': self.provisioning_uri
        }
