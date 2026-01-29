"""
BFK AuthSystem - Exemplos de Uso (Python)

Instalacao:
    pip install bfk-authsystem           # Basico
    pip install bfk-authsystem[ui]       # Com PyQt5
    pip install bfk-authsystem[full]     # Completo

Documentacao completa: docs/API_INTEGRATION.md
"""

# =============================================================================
# EXEMPLO 1: Verificacao Basica (sem UI)
# =============================================================================

from bfk_authsystem import LicenseValidator

def exemplo_basico():
    """Verificacao simples de licenca."""
    validator = LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP'
    )

    result = validator.verify(username='usuario', password='senha')

    if result.valid:
        print('Licenca valida!')
        print(f'Dias ate reautenticacao: {result.days_until_reauth}')
    else:
        print(f'Erro: {result.message} ({result.error_code})')


# =============================================================================
# EXEMPLO 2: Com UI - login_with_ui() (RECOMENDADO v1.2.0+)
# =============================================================================

def exemplo_com_ui():
    """Verificacao com UI usando login_with_ui() - metodo recomendado."""
    from bfk_authsystem import LicenseValidator
    from bfk_authsystem.ui import PYQT_AVAILABLE

    if not PYQT_AVAILABLE:
        print("PyQt5 nao instalado. Use: pip install bfk-authsystem[ui]")
        return False

    validator = LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP'
    )

    # Uma unica linha para todo o fluxo de autenticacao!
    # Trata automaticamente:
    # - Login (username/password)
    # - Troca de senha obrigatoria
    # - Configuracao de MFA (obrigatorio)
    # - Exibicao de recovery codes
    # - Solicitacao de license_key (primeira execucao)
    if validator.login_with_ui():
        print("Autenticado com sucesso!")
        return True
    else:
        print("Login cancelado")
        return False


# =============================================================================
# EXEMPLO 2B: Exibir Status da Licenca (v1.2.0+)
# =============================================================================

def exemplo_show_status():
    """Exibe informacoes da licenca (menu Sobre a Licenca).

    A partir da v1.2.0, um novo LicenseValidator recupera automaticamente
    os tokens e dados do cache. Nao e necessario chamar refresh_session()
    ou verify() antes de show_status().
    """
    from bfk_authsystem import LicenseValidator

    try:
        validator = LicenseValidator(
            server_url='https://authsystem.bfk.eng.br/api/v1',
            app_code='MINHA_APP',
            cache_enabled=True
        )

        # Dados sao recuperados do cache automaticamente
        validator.show_status()

    except Exception as e:
        print(f"Nao foi possivel obter informacoes da licenca: {e}")


# =============================================================================
# EXEMPLO 3: Tratamento de Erros
# =============================================================================

def exemplo_tratamento_erros():
    """Tratamento completo de excecoes."""
    from bfk_authsystem import (
        LicenseValidator,
        AuthenticationError,
        MFARequiredError,
        LicenseNotFoundError,
        NetworkError,
        CircuitBreakerOpenError,
        PasswordChangeRequiredError,
    )

    validator = LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP'
    )

    try:
        result = validator.verify(username='usuario', password='senha')

        if result.valid:
            print('Sucesso!')
        else:
            # Tratar por codigo
            if result.error_code == 'MFA_REQUIRED':
                print('Solicitar codigo MFA')
            elif result.error_code == 'LICENSE_KEY_REQUIRED':
                print('Solicitar chave de licenca')
            elif result.error_code == 'PASSWORD_CHANGE_REQUIRED':
                print('Troca de senha obrigatoria')

    except AuthenticationError:
        print('Credenciais invalidas')
    except MFARequiredError:
        print('MFA necessario')
    except LicenseNotFoundError:
        print('Licenca nao encontrada')
    except NetworkError:
        print('Erro de conexao')
    except CircuitBreakerOpenError:
        print('Servidor temporariamente indisponivel')


# =============================================================================
# EXEMPLO 4: Modo Offline
# =============================================================================

def exemplo_modo_offline():
    """Verificacao com suporte a modo offline."""
    from bfk_authsystem import LicenseValidator

    validator = LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP',
        max_offline_days=7,    # Dias maximos offline
        cache_enabled=True     # Habilitar cache
    )

    result = validator.verify(username='usuario', password='senha')

    if result.is_offline:
        print(f'Modo offline ({result.days_offline} dias)')
        print(f'Dias restantes: {result.days_until_reauth}')
    elif result.valid:
        print('Verificacao online bem-sucedida')


# =============================================================================
# EXEMPLO 4B: Restricoes de Horario (v1.1.0+)
# =============================================================================

def exemplo_restricoes_horario():
    """Verificar restricoes de horario da licenca."""
    from bfk_authsystem import LicenseValidator

    validator = LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP'
    )

    result = validator.verify(username='usuario', password='senha')

    if result.valid:
        # Verificar se ha restricoes de horario
        if result.schedule_info and result.schedule_info.get('has_restrictions'):
            info = result.schedule_info
            print(f"Fuso horario: {info.get('timezone')}")
            print(f"Dias com restricao: {info.get('total_restricted_days')}")

            # Horarios permitidos por dia
            for dia, horarios in info.get('schedule', {}).items():
                print(f"  {dia}: {horarios}")
        else:
            print("Sem restricoes de horario - uso liberado 24h")
    elif result.error_code == 'SCHEDULE_RESTRICTED':
        # Acesso bloqueado por horario
        print(f"Acesso bloqueado: {result.message}")
        info = result.schedule_info
        if info:
            print(f"Horarios permitidos: {info.get('allowed_intervals')}")
            print(f"Proximo intervalo: {info.get('next_interval')}")


# =============================================================================
# EXEMPLO 5: MFA (Autenticacao de Dois Fatores)
# =============================================================================

def exemplo_mfa():
    """Configuracao e uso de MFA."""
    from bfk_authsystem import LicenseValidator

    validator = LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP'
    )

    # Autenticar primeiro
    validator.authenticate(username='usuario', password='senha')

    # Iniciar setup MFA
    mfa_info = validator.setup_mfa()
    print(f'Secret: {mfa_info.secret}')
    print(f'QR Code (base64): {mfa_info.qr_code[:50]}...')

    # Habilitar com token do app autenticador
    token = input('Digite o codigo do app autenticador: ')
    recovery_codes = validator.enable_mfa(token=token)
    print(f'Recovery codes: {recovery_codes}')


# =============================================================================
# EXEMPLO 6: Gerenciamento de Sessoes
# =============================================================================

def exemplo_sessoes():
    """Listar e revogar sessoes."""
    from bfk_authsystem import LicenseValidator

    validator = LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP'
    )

    # Autenticar
    validator.authenticate(username='usuario', password='senha')

    # Listar sessoes ativas
    sessions = validator.get_active_sessions()
    for s in sessions:
        status = '(atual)' if s.is_current else ''
        print(f'{s.device_info} - {s.ip_address} {status}')

    # Revogar todas as outras sessoes
    count = validator.revoke_all_sessions()
    print(f'{count} sessoes revogadas')


# =============================================================================
# EXEMPLO 7: Context Manager
# =============================================================================

def exemplo_context_manager():
    """Uso com context manager (fecha conexoes automaticamente)."""
    from bfk_authsystem import LicenseValidator

    with LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP'
    ) as validator:
        result = validator.verify(username='usuario', password='senha')
        if result.valid:
            print('OK')
    # Conexoes fechadas automaticamente


# =============================================================================
# EXEMPLO 8: Configuracao Avancada
# =============================================================================

def exemplo_configuracao_avancada():
    """Configuracao com retry e circuit breaker."""
    from bfk_authsystem import LicenseValidator
    from bfk_authsystem.retry_handler import RetryConfig
    from bfk_authsystem.circuit_breaker import CircuitBreakerConfig

    retry_config = RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0
    )

    circuit_config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0
    )

    validator = LicenseValidator(
        server_url='https://authsystem.bfk.eng.br/api/v1',
        app_code='MINHA_APP',
        timeout=30.0,
        max_offline_days=7,
        retry_config=retry_config,
        circuit_config=circuit_config,
        verify_ssl=True,
        cache_enabled=True
    )

    result = validator.verify(username='usuario', password='senha')
    print(f'Valido: {result.valid}')


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Exemplos de uso do BFK AuthSystem")
    print("=" * 50)
    print()
    print("Escolha um exemplo:")
    print("1. Verificacao basica")
    print("2. Com UI - login_with_ui() (RECOMENDADO)")
    print("2b. Exibir status da licenca")
    print("3. Tratamento de erros")
    print("4. Modo offline")
    print("4b. Restricoes de horario")
    print("5. MFA")
    print("6. Gerenciamento de sessoes")
    print("7. Context manager")
    print("8. Configuracao avancada")
    print()

    opcao = input("Opcao: ")

    exemplos = {
        '1': exemplo_basico,
        '2': exemplo_com_ui,
        '2b': exemplo_show_status,
        '3': exemplo_tratamento_erros,
        '4': exemplo_modo_offline,
        '4b': exemplo_restricoes_horario,
        '5': exemplo_mfa,
        '6': exemplo_sessoes,
        '7': exemplo_context_manager,
        '8': exemplo_configuracao_avancada,
    }

    if opcao in exemplos:
        exemplos[opcao]()
    else:
        print("Opcao invalida")
