"""
BFK AuthSystem - Coleta de Informacoes de Hardware

Funcoes para gerar machine_id e coletar componentes de hardware.
"""

import hashlib
import platform
import socket
import subprocess
import os
import logging
from typing import Dict, Optional, Tuple

from .exceptions import HardwareError


logger = logging.getLogger(__name__)


def get_system_info() -> Dict[str, str]:
    """
    Coleta informacoes basicas do sistema.

    Returns:
        Dict com hostname, os_info, platform
    """
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "unknown"

    try:
        os_info = f"{platform.system()} {platform.release()}"
        if platform.system() == "Windows":
            os_info = f"Windows {platform.win32_ver()[0]}"
    except Exception:
        os_info = "Unknown OS"

    return {
        "hostname": hostname,
        "os_info": os_info,
        "platform": platform.system()
    }


def _run_command(command: list) -> str:
    """
    Executa comando e retorna saida.

    Args:
        command: Lista com comando e argumentos

    Returns:
        Saida do comando ou string vazia
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        return result.stdout.strip()
    except Exception as e:
        logger.debug(f"Comando falhou: {command}: {e}")
        return ""


def _get_windows_hardware() -> Dict[str, str]:
    """
    Coleta hardware usando WMIC no Windows.

    Returns:
        Dict com componentes de hardware
    """
    components = {}

    # CPU
    try:
        output = _run_command(["wmic", "cpu", "get", "name", "/value"])
        for line in output.split("\n"):
            if line.startswith("Name="):
                components["cpu"] = line.split("=", 1)[1].strip()
                break
    except Exception:
        pass

    # Motherboard
    try:
        output = _run_command(["wmic", "baseboard", "get", "manufacturer,product", "/value"])
        manufacturer = ""
        product = ""
        for line in output.split("\n"):
            if line.startswith("Manufacturer="):
                manufacturer = line.split("=", 1)[1].strip()
            elif line.startswith("Product="):
                product = line.split("=", 1)[1].strip()
        if manufacturer or product:
            components["motherboard"] = f"{manufacturer} {product}".strip()
    except Exception:
        pass

    # Disk (primeiro disco)
    try:
        output = _run_command(["wmic", "diskdrive", "get", "model", "/value"])
        for line in output.split("\n"):
            if line.startswith("Model="):
                components["disk"] = line.split("=", 1)[1].strip()
                break
    except Exception:
        pass

    # BIOS Serial (usado para identificacao unica)
    try:
        output = _run_command(["wmic", "bios", "get", "serialnumber", "/value"])
        for line in output.split("\n"):
            if line.startswith("SerialNumber="):
                serial = line.split("=", 1)[1].strip()
                if serial and serial.lower() not in ["to be filled by o.e.m.", "default string", ""]:
                    components["bios_serial"] = serial
                break
    except Exception:
        pass

    # UUID do sistema
    try:
        output = _run_command(["wmic", "csproduct", "get", "uuid", "/value"])
        for line in output.split("\n"):
            if line.startswith("UUID="):
                uuid_val = line.split("=", 1)[1].strip()
                if uuid_val and uuid_val != "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
                    components["system_uuid"] = uuid_val
                break
    except Exception:
        pass

    # MAC Address da primeira interface de rede
    try:
        output = _run_command(["wmic", "nic", "where", "NetEnabled=true", "get", "MACAddress", "/value"])
        for line in output.split("\n"):
            if line.startswith("MACAddress="):
                mac = line.split("=", 1)[1].strip()
                if mac:
                    components["mac_address"] = mac
                    break
    except Exception:
        pass

    return components


def _get_linux_hardware() -> Dict[str, str]:
    """
    Coleta hardware no Linux usando /sys, dmidecode ou lshw.

    Returns:
        Dict com componentes de hardware
    """
    components = {}

    # CPU
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    components["cpu"] = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass

    # Motherboard
    try:
        vendor = ""
        product = ""
        if os.path.exists("/sys/class/dmi/id/board_vendor"):
            with open("/sys/class/dmi/id/board_vendor", "r") as f:
                vendor = f.read().strip()
        if os.path.exists("/sys/class/dmi/id/board_name"):
            with open("/sys/class/dmi/id/board_name", "r") as f:
                product = f.read().strip()
        if vendor or product:
            components["motherboard"] = f"{vendor} {product}".strip()
    except Exception:
        pass

    # System UUID
    try:
        if os.path.exists("/sys/class/dmi/id/product_uuid"):
            with open("/sys/class/dmi/id/product_uuid", "r") as f:
                components["system_uuid"] = f.read().strip()
    except Exception:
        # Pode precisar de root
        try:
            output = _run_command(["sudo", "cat", "/sys/class/dmi/id/product_uuid"])
            if output:
                components["system_uuid"] = output
        except Exception:
            pass

    # Machine ID
    try:
        if os.path.exists("/etc/machine-id"):
            with open("/etc/machine-id", "r") as f:
                components["machine_id_file"] = f.read().strip()
    except Exception:
        pass

    # Disk
    try:
        output = _run_command(["lsblk", "-d", "-o", "MODEL", "-n"])
        if output:
            models = [m.strip() for m in output.split("\n") if m.strip()]
            if models:
                components["disk"] = models[0]
    except Exception:
        pass

    # MAC Address
    try:
        for iface in os.listdir("/sys/class/net"):
            if iface != "lo":
                addr_path = f"/sys/class/net/{iface}/address"
                if os.path.exists(addr_path):
                    with open(addr_path, "r") as f:
                        mac = f.read().strip()
                        if mac and mac != "00:00:00:00:00:00":
                            components["mac_address"] = mac.upper()
                            break
    except Exception:
        pass

    return components


def _get_mac_hardware() -> Dict[str, str]:
    """
    Coleta hardware no macOS.

    Returns:
        Dict com componentes de hardware
    """
    components = {}

    # CPU
    try:
        output = _run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
        if output:
            components["cpu"] = output
    except Exception:
        pass

    # Hardware UUID
    try:
        output = _run_command(["system_profiler", "SPHardwareDataType"])
        for line in output.split("\n"):
            if "Hardware UUID" in line:
                components["system_uuid"] = line.split(":", 1)[1].strip()
            elif "Model Identifier" in line:
                components["motherboard"] = line.split(":", 1)[1].strip()
    except Exception:
        pass

    # Serial Number
    try:
        output = _run_command(["system_profiler", "SPHardwareDataType"])
        for line in output.split("\n"):
            if "Serial Number" in line:
                components["bios_serial"] = line.split(":", 1)[1].strip()
                break
    except Exception:
        pass

    return components


def get_hardware_components() -> Dict[str, str]:
    """
    Coleta componentes de hardware da maquina.

    Returns:
        Dict com componentes (cpu, motherboard, disk, etc.)

    Raises:
        HardwareError: Se falhar ao coletar hardware
    """
    system = platform.system()

    try:
        if system == "Windows":
            components = _get_windows_hardware()
        elif system == "Linux":
            components = _get_linux_hardware()
        elif system == "Darwin":
            components = _get_mac_hardware()
        else:
            components = {}

        # Garantir que temos pelo menos alguns componentes
        if not components:
            # Fallback: usar hostname e plataforma
            components["hostname"] = socket.gethostname()
            components["platform"] = f"{system} {platform.release()}"

        return components

    except Exception as e:
        logger.error(f"Erro ao coletar hardware: {e}")
        raise HardwareError(
            f"Falha ao coletar informacoes de hardware: {e}",
            code="HARDWARE_ERROR"
        )


def generate_machine_id(components: Dict[str, str] = None) -> str:
    """
    Gera um ID unico para a maquina baseado no hardware.

    O machine_id e um hash SHA-256 dos componentes de hardware,
    garantindo unicidade e privacidade.

    Args:
        components: Componentes de hardware (opcional, sera coletado se nao fornecido)

    Returns:
        Hash SHA-256 hexadecimal (64 caracteres)

    Raises:
        HardwareError: Se falhar ao gerar machine_id
    """
    if components is None:
        components = get_hardware_components()

    try:
        # Ordenar componentes para garantir consistencia
        sorted_items = sorted(components.items())

        # Criar string de identificacao
        # Prioridade: system_uuid > bios_serial > mac_address > outros
        id_parts = []

        # Componentes de alta prioridade (mais estaveis)
        if "system_uuid" in components:
            id_parts.append(f"uuid:{components['system_uuid']}")
        if "bios_serial" in components:
            id_parts.append(f"bios:{components['bios_serial']}")
        if "machine_id_file" in components:
            id_parts.append(f"mid:{components['machine_id_file']}")

        # Componentes de media prioridade
        if "motherboard" in components:
            id_parts.append(f"mb:{components['motherboard']}")
        if "cpu" in components:
            id_parts.append(f"cpu:{components['cpu']}")

        # MAC address como fallback
        if "mac_address" in components:
            id_parts.append(f"mac:{components['mac_address']}")

        # Se nao temos nada, usar hostname (menos confiavel)
        if not id_parts:
            id_parts.append(f"host:{socket.gethostname()}")
            id_parts.append(f"platform:{platform.system()}")

        # Concatenar e gerar hash
        id_string = "|".join(id_parts)
        machine_id = hashlib.sha256(id_string.encode("utf-8")).hexdigest()

        logger.debug(f"Machine ID gerado: {machine_id[:16]}...")
        return machine_id

    except Exception as e:
        logger.error(f"Erro ao gerar machine_id: {e}")
        raise HardwareError(
            f"Falha ao gerar machine_id: {e}",
            code="HARDWARE_ERROR"
        )


def get_hardware_info() -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """
    Coleta todas as informacoes de hardware necessarias.

    Returns:
        Tupla (machine_id, hardware_components, system_info)

    Raises:
        HardwareError: Se falhar ao coletar informacoes
    """
    system_info = get_system_info()
    components = get_hardware_components()
    machine_id = generate_machine_id(components)

    return machine_id, components, system_info
