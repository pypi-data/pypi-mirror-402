"""
BFK AuthSystem - Validador de Hardware (Cliente)

Verifica tokens JWT RS256 de validacao de hardware offline.
A chave publica RSA esta embebida neste arquivo para permitir
verificacao sem contatar o servidor.
"""

import hashlib
import logging
from typing import Dict, Tuple, Optional, Any
from datetime import datetime

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

logger = logging.getLogger(__name__)


# Chave publica RSA para verificacao de tokens JWT RS256
# Esta chave e gerada pelo servidor e distribuida com o cliente
# NAO PODE ser alterada - tokens assinados com a chave privada correspondente
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqCMid+CmzsW/iygQKI7n
MMNN/bMEyVqygAEZCFXZu8YUV4yBe6m0IbvrmKbNKjmPjfgaz+Ch0JV6FtIUJoQH
HvI2Y/fmCJBTDIwa3x8l0oKQKWfpl+lA34TlRYK72lE/qvt6HqaJ4Mkv6dd1rrkU
+5BOTR3ucyc/3bWc6b/jcjTlyarOV+rg6/qLxgzNhTNTrOYTcr6xV67t/X8tDrG7
1r/cFs3lPq/byR2Ws2pU1WUUypAYQEVKqymRmnEvAPZ1GQkz8X1rVNNqWiZOECBG
NvbKJFA8nWPeA6MXV37FFNhjVBOHoqg4eBLGwCjdFQYZFqbQ0+pGWxT6jvOpF7Z7
kQIDAQAB
-----END PUBLIC KEY-----"""


def generate_machine_id(hardware_components: Dict[str, str]) -> str:
    """
    Gera identificador unico da maquina baseado nos componentes de hardware.

    Identico ao metodo do servidor para garantir consistencia.

    Args:
        hardware_components: Dict com {motherboard, cpu, disk, system}

    Returns:
        str: Hash SHA-256 (64 caracteres hex)
    """
    ordered_keys = ['motherboard', 'cpu', 'disk', 'system']

    concat = ''
    for key in ordered_keys:
        value = hardware_components.get(key, '')
        normalized = str(value).upper().strip()
        concat += normalized + '|'

    return hashlib.sha256(concat.encode('utf-8')).hexdigest()


def verify_hardware_token(
    token: str,
    current_machine_id: str,
    current_components: Dict[str, str]
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Verifica token JWT de validacao de hardware offline.

    Validacoes realizadas:
    1. Assinatura RS256 valida (garante autenticidade)
    2. Token nao expirado
    3. machine_id corresponde ao atual
    4. hardware_hash corresponde aos componentes atuais

    Args:
        token: Token JWT a verificar
        current_machine_id: Machine ID atual da maquina
        current_components: Componentes de hardware atuais

    Returns:
        Tuple[bool, str, Optional[Dict]]: (is_valid, message, payload)
    """
    if not JWT_AVAILABLE:
        return False, "PyJWT nao instalado - pip install pyjwt", None

    if not token:
        return False, "Token nao fornecido", None

    try:
        # Decodificar e verificar assinatura RS256
        payload = jwt.decode(
            token,
            RSA_PUBLIC_KEY,
            algorithms=['RS256']
        )

        # Verificar tipo de token
        if payload.get('type') != 'hardware_validation':
            return False, "Tipo de token invalido", None

        # Verificar machine_id
        token_machine_id = payload.get('machine_id', '')
        if token_machine_id != current_machine_id:
            logger.warning(
                f"Machine ID diferente: token={token_machine_id[:16]}... "
                f"atual={current_machine_id[:16]}..."
            )
            return False, "Machine ID nao corresponde", None

        # Verificar hardware_hash
        stored_hash = payload.get('hardware_hash', '')
        current_hash = generate_machine_id(current_components)

        if stored_hash != current_hash:
            logger.warning("Hardware hash diferente do token")
            return False, "Hardware modificado desde emissao do token", None

        # Token valido
        return True, "Hardware validado com sucesso (offline)", payload

    except jwt.ExpiredSignatureError:
        return False, "Token expirado - reconecte ao servidor", None
    except jwt.InvalidSignatureError:
        # CRITICO: Assinatura invalida = token adulterado ou forjado
        logger.error("ALERTA: Assinatura JWT invalida - possivel tentativa de fraude")
        return False, "Assinatura invalida - token pode ter sido adulterado", None
    except jwt.DecodeError as e:
        logger.error(f"Erro ao decodificar token: {e}")
        return False, "Token malformado", None
    except Exception as e:
        logger.error(f"Erro na verificacao de hardware: {e}")
        return False, f"Erro na verificacao: {str(e)}", None


def get_token_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Extrai informacoes do token sem verificar assinatura.

    Util para debug e exibicao de informacoes ao usuario.
    NAO USAR para decisoes de seguranca.

    Args:
        token: Token JWT

    Returns:
        Dict com payload decodificado ou None se invalido
    """
    if not JWT_AVAILABLE:
        return None

    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        return payload
    except Exception:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Retorna data de expiracao do token.

    Args:
        token: Token JWT

    Returns:
        datetime de expiracao ou None
    """
    info = get_token_info(token)
    if info and 'exp' in info:
        try:
            return datetime.fromtimestamp(info['exp'])
        except Exception:
            pass
    return None


def is_token_expired(token: str) -> bool:
    """
    Verifica se o token esta expirado.

    Args:
        token: Token JWT

    Returns:
        True se expirado ou invalido
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return True
    return datetime.now() > expiry


def days_until_token_expiry(token: str) -> int:
    """
    Calcula dias ate expiracao do token.

    Args:
        token: Token JWT

    Returns:
        Dias ate expiracao (negativo se expirado, -999 se invalido)
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return -999

    delta = expiry - datetime.now()
    return delta.days
