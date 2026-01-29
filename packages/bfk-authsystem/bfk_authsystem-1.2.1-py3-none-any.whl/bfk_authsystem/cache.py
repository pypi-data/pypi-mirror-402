"""
BFK AuthSystem - Cache Local

Gerencia cache criptografado para tokens e verificacoes offline.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from .exceptions import CacheError, CacheExpiredError, CacheCorruptedError


logger = logging.getLogger(__name__)


@dataclass
class CachedVerification:
    """
    Dados de verificacao em cache.

    Attributes:
        valid: Se a licenca e valida
        username: Nome do usuario
        license_key: Chave da licenca
        app_code: Codigo da aplicacao
        machine_id: ID da maquina
        last_verification: Timestamp da ultima verificacao
        reauth_days: Dias para reautenticacao
        days_since_auth: Dias desde ultima autenticacao
        app_config: Configuracao da aplicacao (JSON string)
        hardware_validation_token: Token JWT RS256 para validacao offline de hardware
    """
    valid: bool
    username: str
    license_key: str
    app_code: str
    machine_id: str
    last_verification: str  # ISO format
    reauth_days: int
    days_since_auth: int
    app_config: str  # JSON string
    hardware_validation_token: str = ""  # Token JWT RS256

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'CachedVerification':
        """Cria a partir de dicionario."""
        # Suporte a cache antigo sem hardware_validation_token
        if 'hardware_validation_token' not in data:
            data['hardware_validation_token'] = ""
        return cls(**data)


@dataclass
class CachedTokens:
    """
    Tokens em cache.

    Attributes:
        session_token: Token de sessao
        refresh_token: Token de refresh
        created_at: Quando os tokens foram salvos
    """
    session_token: str
    refresh_token: str
    created_at: str  # ISO format

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'CachedTokens':
        """Cria a partir de dicionario."""
        return cls(**data)


class CacheManager:
    """
    Gerenciador de cache local criptografado.

    O cache armazena:
    - Tokens de sessao e refresh
    - Resultado da ultima verificacao
    - Configuracao da aplicacao

    Os dados sao criptografados usando AES-256 (via Fernet)
    com chave derivada do machine_id.

    Exemplo:
        cache = CacheManager(app_code='MYAPP', machine_id='abc123')
        cache.save_verification(verification_data)
        cached = cache.load_verification()
    """

    CACHE_DIR_NAME = '.bfk_authsystem'
    CACHE_FILE_SUFFIX = '_cache.enc'
    SALT_LENGTH = 16
    KEY_ITERATIONS = 100000

    def __init__(
        self,
        app_code: str,
        machine_id: str,
        cache_dir: Path = None,
        max_offline_days: int = 7
    ):
        """
        Inicializa o gerenciador de cache.

        Args:
            app_code: Codigo da aplicacao
            machine_id: ID da maquina (usado para derivar chave)
            cache_dir: Diretorio do cache (padrao: ~/.bfk_authsystem)
            max_offline_days: Dias maximos em modo offline
        """
        self.app_code = app_code
        self.machine_id = machine_id
        self.max_offline_days = max_offline_days

        # Diretorio do cache
        if cache_dir:
            self._cache_dir = Path(cache_dir)
        else:
            self._cache_dir = Path.home() / self.CACHE_DIR_NAME

        # Criar diretorio se nao existir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Arquivo de cache
        self._cache_file = self._cache_dir / f"{app_code.lower()}{self.CACHE_FILE_SUFFIX}"

        # Chave de criptografia (derivada do machine_id)
        self._key: Optional[bytes] = None
        self._salt: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None

    def _get_salt_file(self) -> Path:
        """Retorna caminho do arquivo de salt."""
        return self._cache_dir / f"{self.app_code.lower()}_salt.bin"

    def _load_or_create_salt(self) -> bytes:
        """Carrega ou cria salt para derivacao de chave."""
        salt_file = self._get_salt_file()

        if salt_file.exists():
            try:
                self._salt = salt_file.read_bytes()
                if len(self._salt) == self.SALT_LENGTH:
                    return self._salt
            except Exception:
                pass

        # Criar novo salt
        self._salt = os.urandom(self.SALT_LENGTH)
        try:
            salt_file.write_bytes(self._salt)
        except Exception as e:
            logger.warning(f"Nao foi possivel salvar salt: {e}")

        return self._salt

    def _derive_key(self) -> bytes:
        """
        Deriva chave de criptografia do machine_id.

        Returns:
            Chave de 32 bytes para Fernet
        """
        if self._key is not None:
            return self._key

        salt = self._load_or_create_salt()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.KEY_ITERATIONS,
        )

        # Usar machine_id como senha
        key_material = self.machine_id.encode('utf-8')
        derived = kdf.derive(key_material)

        # Fernet requer base64 encoding
        self._key = base64.urlsafe_b64encode(derived)
        return self._key

    def _get_fernet(self) -> Fernet:
        """Retorna instancia do Fernet."""
        if self._fernet is None:
            key = self._derive_key()
            self._fernet = Fernet(key)
        return self._fernet

    def _encrypt(self, data: dict) -> bytes:
        """
        Criptografa dados.

        Args:
            data: Dicionario para criptografar

        Returns:
            Dados criptografados
        """
        fernet = self._get_fernet()
        json_data = json.dumps(data, ensure_ascii=False)
        return fernet.encrypt(json_data.encode('utf-8'))

    def _decrypt(self, encrypted: bytes) -> dict:
        """
        Descriptografa dados.

        Args:
            encrypted: Dados criptografados

        Returns:
            Dicionario descriptografado

        Raises:
            CacheCorruptedError: Se dados estiverem corrompidos
        """
        try:
            fernet = self._get_fernet()
            decrypted = fernet.decrypt(encrypted)
            return json.loads(decrypted.decode('utf-8'))
        except InvalidToken:
            raise CacheCorruptedError(
                "Cache corrompido ou chave invalida",
                code="CACHE_CORRUPTED"
            )
        except json.JSONDecodeError:
            raise CacheCorruptedError(
                "Cache contem dados invalidos",
                code="CACHE_CORRUPTED"
            )

    def _read_cache(self) -> Optional[dict]:
        """
        Le cache do disco.

        Returns:
            Dicionario com dados ou None se nao existir
        """
        if not self._cache_file.exists():
            return None

        try:
            encrypted = self._cache_file.read_bytes()
            return self._decrypt(encrypted)
        except CacheCorruptedError:
            # Remover cache corrompido
            self.clear()
            raise
        except Exception as e:
            logger.error(f"Erro ao ler cache: {e}")
            return None

    def _write_cache(self, data: dict):
        """
        Escreve cache no disco.

        Args:
            data: Dados para salvar
        """
        try:
            encrypted = self._encrypt(data)
            self._cache_file.write_bytes(encrypted)
        except Exception as e:
            raise CacheError(
                f"Falha ao salvar cache: {e}",
                code="CACHE_WRITE_ERROR"
            )

    def save_verification(
        self,
        valid: bool,
        username: str,
        license_key: str,
        reauth_days: int = 30,
        days_since_auth: int = 0,
        app_config: dict = None,
        hardware_validation_token: str = ""
    ):
        """
        Salva resultado de verificacao no cache.

        Args:
            valid: Se a licenca e valida
            username: Nome do usuario
            license_key: Chave da licenca
            reauth_days: Dias para reautenticacao
            days_since_auth: Dias desde ultima autenticacao
            app_config: Configuracao da aplicacao
            hardware_validation_token: Token JWT RS256 para validacao offline
        """
        verification = CachedVerification(
            valid=valid,
            username=username,
            license_key=license_key,
            app_code=self.app_code,
            machine_id=self.machine_id,
            last_verification=datetime.now().isoformat(),
            reauth_days=reauth_days,
            days_since_auth=days_since_auth,
            app_config=json.dumps(app_config or {}),
            hardware_validation_token=hardware_validation_token
        )

        cache_data = self._read_cache() or {}
        cache_data['verification'] = verification.to_dict()

        self._write_cache(cache_data)
        logger.debug(f"Verificacao salva no cache para {self.app_code}")

    def load_verification(self) -> Optional[CachedVerification]:
        """
        Carrega verificacao do cache.

        Returns:
            CachedVerification ou None

        Raises:
            CacheExpiredError: Se o cache expirou
        """
        cache_data = self._read_cache()
        if not cache_data or 'verification' not in cache_data:
            return None

        verification = CachedVerification.from_dict(cache_data['verification'])

        # Verificar se a maquina e a mesma
        if verification.machine_id != self.machine_id:
            logger.warning("Machine ID diferente no cache")
            return None

        # Verificar expiracao
        last_verif = datetime.fromisoformat(verification.last_verification)
        days_offline = (datetime.now() - last_verif).days

        if days_offline > self.max_offline_days:
            raise CacheExpiredError(
                f"Cache expirado ({days_offline} dias offline)",
                code="CACHE_EXPIRED",
                details={'days_offline': days_offline}
            )

        return verification

    def save_tokens(self, session_token: str, refresh_token: str):
        """
        Salva tokens no cache.

        Args:
            session_token: Token de sessao
            refresh_token: Token de refresh
        """
        tokens = CachedTokens(
            session_token=session_token,
            refresh_token=refresh_token,
            created_at=datetime.now().isoformat()
        )

        cache_data = self._read_cache() or {}
        cache_data['tokens'] = tokens.to_dict()

        self._write_cache(cache_data)
        logger.debug(f"Tokens salvos no cache para {self.app_code}")

    def load_tokens(self) -> Optional[CachedTokens]:
        """
        Carrega tokens do cache.

        Returns:
            CachedTokens ou None
        """
        cache_data = self._read_cache()
        if not cache_data or 'tokens' not in cache_data:
            return None

        return CachedTokens.from_dict(cache_data['tokens'])

    def clear_tokens(self):
        """Remove apenas tokens do cache."""
        cache_data = self._read_cache() or {}
        if 'tokens' in cache_data:
            del cache_data['tokens']
            self._write_cache(cache_data)
            logger.debug("Tokens removidos do cache")

    def clear(self):
        """Remove todo o cache."""
        try:
            if self._cache_file.exists():
                self._cache_file.unlink()
            logger.debug(f"Cache limpo para {self.app_code}")
        except Exception as e:
            logger.warning(f"Erro ao limpar cache: {e}")

    def get_days_offline(self) -> int:
        """
        Calcula dias desde a ultima verificacao.

        Returns:
            Numero de dias offline, ou -1 se nao houver cache
        """
        try:
            verification = self.load_verification()
            if verification:
                last_verif = datetime.fromisoformat(verification.last_verification)
                return (datetime.now() - last_verif).days
        except CacheExpiredError:
            pass
        return -1

    def is_offline_valid(self) -> bool:
        """
        Verifica se o cache offline ainda e valido.

        Returns:
            True se pode operar offline
        """
        try:
            verification = self.load_verification()
            if verification and verification.valid:
                days = self.get_days_offline()
                return 0 <= days <= self.max_offline_days
        except CacheExpiredError:
            pass
        return False

    @property
    def cache_exists(self) -> bool:
        """Verifica se o arquivo de cache existe."""
        return self._cache_file.exists()

    @property
    def cache_path(self) -> Path:
        """Retorna caminho do arquivo de cache."""
        return self._cache_file
