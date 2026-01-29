# BFK AuthSystem - Guia de Integracao

## Visao Geral

O BFK AuthSystem e um sistema de autenticacao e licenciamento para aplicacoes desktop e web.

**URL Base:** `https://authsystem.bfk.eng.br/api/v1`
**Formato:** JSON
**Autenticacao:** Bearer Token (JWT)

---

## Indice

1. [Instalacao](#instalacao)
2. [Inicio Rapido](#inicio-rapido)
3. [Fluxo de Autenticacao](#fluxo-de-autenticacao)
4. [Endpoints Principais](#endpoints-principais)
5. [SDK Python Completo](#sdk-python-completo)
6. [UI Dialogs (PyQt5)](#ui-dialogs-pyqt5)
7. [Modelos de Dados](#modelos-de-dados)
8. [Tratamento de Erros](#tratamento-de-erros)
9. [Modo Offline](#modo-offline)
10. [Recursos Avancados](#recursos-avancados)
11. [SDKs Outros](#sdks-outros)
12. [Contato](#contato)

---

## Instalacao

### Python SDK

```bash
# Instalacao basica
pip install bfk-authsystem

# Com UI (dialogs PyQt5)
pip install bfk-authsystem[ui]

# Com coleta de hardware avancada
pip install bfk-authsystem[hardware]

# Instalacao completa
pip install bfk-authsystem[full]
```

### TestPyPI (Desenvolvimento)

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ bfk-authsystem[full]
```

### Requisitos

- Python >= 3.8
- requests >= 2.31.0
- cryptography >= 41.0.0
- PyQt5 >= 5.15.0 (opcional, para UI)
- psutil >= 5.9.0 (opcional, para hardware)

---

## Inicio Rapido

### Verificacao Basica

```python
from bfk_authsystem import LicenseValidator

# Criar validador
validator = LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP'
)

# Verificar licenca
result = validator.verify(username='usuario', password='senha')

if result.valid:
    print('Licenca valida!')
    print(f'Dias ate reautenticacao: {result.days_until_reauth}')
else:
    print(f'Erro: {result.message}')
```

### Com UI (PyQt5)

```python
from bfk_authsystem import LicenseValidator
from bfk_authsystem.ui import show_login_dialog, PYQT_AVAILABLE

if not PYQT_AVAILABLE:
    print("PyQt5 nao instalado. Use: pip install bfk-authsystem[ui]")
    exit(1)

validator = LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP'
)

# Obter configuracao da aplicacao (cores, logo, etc)
config = validator.get_app_config()

# Mostrar dialog de login personalizado
credentials = show_login_dialog(app_config=config)
if credentials:
    username, password = credentials
    result = validator.verify(username=username, password=password)
```

---

## Fluxo de Autenticacao

```
+------------------+     +------------------+     +------------------+
|   Aplicacao      | --> |  /license/verify | --> |    Resposta      |
+------------------+     +------------------+     +------------------+
        |                        |                        |
        |  username + password   |                        |
        |  + hardware_info       |                        |
        |  + license_key (1a vez)|                        |
        |                        |                        |
        |                        v                        |
        |                 +-------------+                 |
        |                 | Validacoes  |                 |
        |                 +-------------+                 |
        |                        |                        |
        |            +-----------+-----------+            |
        |            |           |           |            |
        |            v           v           v            |
        |      [Sucesso]   [MFA Req]   [Erro]            |
        |            |           |           |            |
        |            v           v           v            |
        |      session_token  Solicitar   Exibir         |
        |      refresh_token  codigo MFA  mensagem       |
        |            |           |                        |
        +------------+-----------+------------------------+
```

### Cenarios de Resposta

| Cenario | Codigo | Dialog UI |
|---------|--------|-----------|
| Sucesso | 200 | - |
| MFA Requerido | `MFA_REQUIRED` | `MFAVerifyDialog` |
| Troca de Senha Obrigatoria | `PASSWORD_CHANGE_REQUIRED` | `ForceChangePasswordDialog` |
| Licenca Requerida | `LICENSE_KEY_REQUIRED` | `LicenseKeyDialog` |
| Credenciais Invalidas | `INVALID_CREDENTIALS` | `LoginDialog` (com erro) |
| Hardware Diferente | `HARDWARE_MISMATCH` | `StatusDialog` |
| Setup MFA Obrigatorio | `MFA_SETUP_REQUIRED` | `MFASetupDialog` |

---

## Endpoints Principais

### POST /license/verify

Endpoint principal para verificacao de licenca e autenticacao.

**Request:**
```json
{
  "username": "string",
  "password": "string",
  "license_key": "string (opcional apos ativacao)",
  "mfa_token": "string (se MFA habilitado)",
  "app_code": "string",
  "machine_id": "string",
  "hardware_components": {
    "motherboard": "string",
    "cpu": "string",
    "disk": "string",
    "system": "string"
  },
  "hostname": "string",
  "os_info": "string"
}
```

**Response (Sucesso):**
```json
{
  "success": true,
  "valid": true,
  "message": "Licenca valida",
  "session_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "expires_in": 1800,
  "license": {
    "license_key": "BFK-XXXX-XXXX-XXXX",
    "user": "Nome do Usuario",
    "app_name": "Nome da App"
  },
  "requires_reauth": false,
  "days_until_reauth": 25,
  "application": {
    "app_code": "MINHA_APP",
    "app_name": "Minha Aplicacao",
    "session_timeout_minutes": 30
  }
}
```

### POST /auth/login

Login padrao (sem verificacao de licenca).

**Request:**
```json
{
  "username": "string",
  "password": "string",
  "mfa_token": "string (opcional)"
}
```

### POST /auth/refresh

Renovar token de sessao.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

### POST /auth/change-password-required

Troca de senha obrigatoria (primeiro login).

**Request:**
```json
{
  "password_change_token": "string",
  "new_password": "string"
}
```

### GET /app/config/get

Obter configuracao da aplicacao (cores, logo, etc).

**Query Parameters:**
- `app_code`: Codigo da aplicacao

**Response:**
```json
{
  "success": true,
  "config": {
    "app_code": "MINHA_APP",
    "app_name": "Minha Aplicacao",
    "display_name": "Minha App v1.0",
    "company_name": "Empresa",
    "support_email": "suporte@empresa.com",
    "logo_base64": "iVBORw0KGgo...",
    "colors": {
      "primary": "#2196f3",
      "secondary": "#f44336"
    },
    "session_timeout_minutes": 30
  }
}
```

### GET /health

Verificar saude do sistema.

---

## SDK Python Completo

### LicenseValidator

Classe principal para validacao de licencas.

```python
from bfk_authsystem import LicenseValidator

validator = LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP',
    timeout=30.0,              # Timeout em segundos
    max_offline_days=7,        # Dias maximos em modo offline
    verify_ssl=True,           # Verificar certificado SSL
    cache_enabled=True         # Habilitar cache local
)

# Propriedades
validator.machine_id          # ID unico da maquina
validator.hostname            # Nome do computador
validator.os_info             # Informacoes do SO
validator.is_online           # Conexao com servidor
validator.current_user        # Usuario atual (apos login)
validator.app_config          # Configuracao da aplicacao
```

### Metodos Principais

```python
# Verificar licenca (principal para desktop)
result = validator.verify(
    username='usuario',
    password='senha',
    mfa_token='123456'  # Se MFA habilitado
)

# Login com UI completo (RECOMENDADO - v1.2.0+)
if validator.login_with_ui():
    print("Autenticado!")

# Exibir status da licenca (v1.2.0+)
validator.show_status(parent=main_window)

# Autenticar (retorna tokens)
tokens = validator.authenticate(username, password, mfa_token)

# Logout
validator.logout()

# Renovar sessao
tokens = validator.refresh_session()

# Obter configuracao da aplicacao
config = validator.get_app_config()

# Troca de senha obrigatoria
tokens = validator.change_password_required(
    password_change_token='token_recebido',
    new_password='nova_senha'
)

# Troca de senha normal
success = validator.change_password(
    current_password='senha_atual',
    new_password='nova_senha'
)
```

### MFA (Autenticacao de Dois Fatores)

```python
# Iniciar setup de MFA
mfa_info = validator.setup_mfa()
print(f'Secret: {mfa_info.secret}')
print(f'QR Code Base64: {mfa_info.qr_code}')

# Habilitar MFA com token do app autenticador
recovery_codes = validator.enable_mfa(token='123456')
print(f'Recovery codes: {recovery_codes}')

# Verificar MFA
success = validator.verify_mfa(token='123456')

# Desabilitar MFA
success = validator.disable_mfa(token='123456')
```

### Gerenciamento de Sessoes

```python
# Listar sessoes ativas
sessions = validator.get_active_sessions()
for s in sessions:
    print(f'{s.device_info} - {s.ip_address}')
    if s.is_current:
        print('  (sessao atual)')

# Revogar uma sessao
validator.revoke_session(session_id=123)

# Revogar todas as outras sessoes
count = validator.revoke_all_sessions()
print(f'{count} sessoes revogadas')
```

---

## UI Dialogs (PyQt5)

A biblioteca inclui dialogs prontos para todos os cenarios de autenticacao.

### Instalacao

```bash
pip install bfk-authsystem[ui]
```

### Dialogs Disponiveis

```python
from bfk_authsystem.ui import (
    PYQT_AVAILABLE,

    # Login
    LoginDialog,
    show_login_dialog,

    # MFA
    MFAVerifyDialog,
    MFASetupDialog,
    MFARecoveryCodesDialog,
    show_mfa_verify_dialog,

    # Licenca
    LicenseKeyDialog,
    show_license_key_dialog,

    # Senha
    ChangePasswordDialog,
    show_change_password_dialog,
    ForceChangePasswordDialog,
    show_force_change_password_dialog,
    ForgotPasswordDialog,
    show_forgot_password_dialog,

    # Recovery Codes
    RecoveryCodesDialog,
    show_recovery_codes_dialog,
    RegenerateRecoveryCodesDialog,
    show_regenerate_codes_dialog,

    # Sessoes
    SessionManagementDialog,
    show_session_management_dialog,

    # Status
    StatusDialog,
    show_status_dialog,
)
```

### Exemplo: Login Dialog

```python
from bfk_authsystem.ui import show_login_dialog

# Modo simples
credentials = show_login_dialog(app_config=config)
if credentials:
    username, password = credentials
    print(f'Usuario: {username}')

# Modo avancado
from bfk_authsystem.ui import LoginDialog
from PyQt5.QtWidgets import QDialog

dialog = LoginDialog(app_config=config)
if dialog.exec_() == QDialog.Accepted:
    username, password = dialog.get_credentials()
```

### Exemplo: MFA Dialog

```python
from bfk_authsystem.ui import show_mfa_verify_dialog

token = show_mfa_verify_dialog(app_config=config)
if token:
    result = validator.verify(username, password, mfa_token=token)
```

### Exemplo: License Key Dialog

```python
from bfk_authsystem.ui import show_license_key_dialog

license_key = show_license_key_dialog(app_config=config)
if license_key:
    # Reenviar verificacao com a chave
    result = validator.verify(username, password, license_key=license_key)
```

### Exemplo: Force Change Password

```python
from bfk_authsystem.ui import show_force_change_password_dialog

new_password = show_force_change_password_dialog(app_config=config)
if new_password:
    tokens = validator.change_password_required(
        password_change_token=result.password_change_token,
        new_password=new_password
    )
```

### Exemplo: Status Dialog (v1.2.0+)

```python
from bfk_authsystem.ui import show_status_dialog

# Via metodo do validator (recomendado)
validator.show_status(parent=main_window)

# Ou diretamente via funcao
show_status_dialog(
    app_config=config,
    user_info=user_info,
    license_info=license_info,
    sessions=sessions,
    days_offline=0,
    is_offline=False,
    days_until_reauth=25,
    parent=main_window
)
```

### Fluxo de Primeiro Acesso (Usuario Novo)

Usuarios novos devem passar por um fluxo obrigatorio:

1. **Login inicial** -> Servidor retorna `PASSWORD_CHANGE_REQUIRED`
2. **Trocar senha** -> `change_password_required()` retorna `mfa_setup_required: True`
3. **Obter QR code** -> `setup_mfa_required()` retorna `secret` e `qr_code`
4. **Mostrar QR** -> Usuario escaneia com Google Authenticator
5. **Confirmar MFA** -> `confirm_mfa_required()` retorna `auth_token` e recovery codes
6. **Mostrar recovery codes** -> Usuario salva em local seguro
7. **Validar licenca** -> `verify(auth_token=auth_token, license_key=...)` retorna `session_token`
8. **Acesso liberado**

**IMPORTANTE:** O fluxo foi refatorado para seguranca. O `session_token` so e emitido apos
TODOS os requisitos serem cumpridos (senha, MFA, licenca).

### Metodo Recomendado: login_with_ui()

A partir da versao 1.2.0, use `login_with_ui()` para autenticacao com UI:

```python
from bfk_authsystem import LicenseValidator

validator = LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP'
)

# Uma unica linha para todo o fluxo!
if validator.login_with_ui():
    print("Autenticado com sucesso!")
    # Iniciar aplicacao
else:
    print("Login cancelado")
    exit(0)
```

Este metodo trata automaticamente:
- Verificacao de sessao no cache (nao pede login se ainda valida)
- Login (username/password) - so se necessario
- Troca de senha obrigatoria
- Configuracao de MFA (SEMPRE obrigatorio)
- Exibicao de recovery codes
- Solicitacao de license_key (primeira execucao)

**Revalidacao:** O login so e solicitado novamente apos expirar o periodo
de reautenticacao configurado pelo admin (padrao 30 dias).

### Exibir Status da Licenca (v1.2.0+)

Para exibir informacoes da licenca (menu "Sobre a Licenca"), use o metodo `show_status()`:

```python
def show_license_info(self):
    """Exibe informacoes sobre a licenca atual."""
    try:
        validator = LicenseValidator(
            server_url='https://authsystem.bfk.eng.br/api/v1',
            app_code='MINHA_APP',
            cache_enabled=True
        )

        # Basta chamar show_status() - dados sao recuperados do cache automaticamente
        validator.show_status(parent=self.main_window)

    except Exception as e:
        QMessageBox.warning(
            self.main_window,
            "Informacoes de Licenca",
            f"Nao foi possivel obter informacoes da licenca:\n{e}"
        )
```

O metodo `show_status()` exibe:
- Informacoes do usuario (username, email, nome)
- Status da licenca (chave, status, revalidacao)
- Dias ate proxima reautenticacao (com cores: verde > 7d, laranja 3-7d, vermelho <= 3d)
- Sessoes ativas (opcional)
- Modo online/offline

**Funcionamento interno (v1.2.0+):**

1. `verify()` agora salva automaticamente `session_token` e `refresh_token` no cache
2. Ao criar um novo `LicenseValidator`, ele recupera tokens e dados do cache automaticamente
3. `show_status()` usa os dados recuperados sem necessidade de chamadas adicionais

Isso permite criar um novo validator em qualquer parte da aplicacao e ter acesso aos dados da sessao.

### Fluxo Manual (Para Casos Especiais)

O metodo `login_with_ui()` e recomendado para a maioria dos casos. O fluxo manual abaixo
demonstra como implementar a autenticacao completa sem usar o metodo simplificado.

**IMPORTANTE:** A partir da versao 1.2.0, `confirm_mfa_required()` retorna `auth_token`
(token temporario), NAO `session_token`. O `session_token` so e emitido apos validacao
completa via `/license/verify`.

```python
from bfk_authsystem import LicenseValidator
from bfk_authsystem.ui import (
    PYQT_AVAILABLE,
    show_login_dialog,
    show_mfa_verify_dialog,
    show_mfa_setup_dialog,
    show_license_key_dialog,
    show_force_change_password_dialog,
    show_recovery_codes_dialog,
)
from bfk_authsystem.models import MFASetupInfo
from PyQt5.QtWidgets import QMessageBox

if not PYQT_AVAILABLE:
    print("UI nao disponivel")
    exit(1)

validator = LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP'
)

config = validator.get_app_config()
auth_token = None  # Token temporario apos MFA (v1.2.0+)

# Loop de autenticacao
while True:
    credentials = show_login_dialog(app_config=config)
    if not credentials:
        exit(0)  # Usuario cancelou

    username, password = credentials
    result = validator.verify(username=username, password=password)

    # Tratar resposta
    if result.valid:
        break  # Sucesso!

    if result.error_code == 'MFA_REQUIRED':
        token = show_mfa_verify_dialog(app_config=config)
        if token:
            result = validator.verify(username, password, mfa_token=token)
            if result.valid:
                break

    elif result.error_code == 'LICENSE_KEY_REQUIRED':
        license_key = show_license_key_dialog(app_config=config)
        if license_key:
            # Se temos auth_token (apos MFA setup), usar ele
            if auth_token:
                result = validator.verify(auth_token=auth_token, license_key=license_key)
            else:
                result = validator.verify(username, password, license_key=license_key)
            if result.valid:
                break

    elif result.error_code == 'PASSWORD_CHANGE_REQUIRED':
        new_password = show_force_change_password_dialog(app_config=config)
        if new_password:
            response = validator.change_password_required(
                password_change_token=result.password_change_token,
                new_password=new_password
            )

            # Apos trocar senha, MFA SEMPRE e obrigatorio
            if response.get('mfa_setup_required'):
                mfa_setup_token = response.get('mfa_setup_token')

                # Obter QR code
                mfa_data = validator.setup_mfa_required(mfa_setup_token)
                mfa_info = MFASetupInfo(
                    secret=mfa_data.get('secret'),
                    qr_code=mfa_data.get('qr_code')
                )

                # Mostrar dialog de setup MFA
                mfa_code = show_mfa_setup_dialog(app_config=config, mfa_info=mfa_info)
                if mfa_code:
                    # confirm_mfa_required retorna Dict com auth_token (v1.2.0+)
                    mfa_result = validator.confirm_mfa_required(
                        mfa_setup_token=mfa_setup_token,
                        mfa_code=mfa_code
                    )

                    if mfa_result:
                        recovery_codes = mfa_result.get('recovery_codes', [])
                        auth_token = mfa_result.get('auth_token')

                        if recovery_codes:
                            show_recovery_codes_dialog(
                                app_config=config,
                                recovery_codes=recovery_codes
                            )

                        # IMPORTANTE: Nao termina aqui! Continua para license_key
                        # O loop continuara e solicitara license_key
                        continue
            else:
                QMessageBox.information(None, "Sucesso", "Senha alterada. Faca login novamente.")
                continue

    elif result.error_code == 'MFA_SETUP_REQUIRED':
        # Usuario ja autenticou mas precisa configurar MFA
        mfa_setup_token = result.mfa_setup_token
        mfa_data = validator.setup_mfa_required(mfa_setup_token)
        mfa_info = MFASetupInfo(
            secret=mfa_data.get('secret'),
            qr_code=mfa_data.get('qr_code')
        )
        mfa_code = show_mfa_setup_dialog(app_config=config, mfa_info=mfa_info)
        if mfa_code:
            # confirm_mfa_required retorna Dict com auth_token (v1.2.0+)
            mfa_result = validator.confirm_mfa_required(
                mfa_setup_token=mfa_setup_token,
                mfa_code=mfa_code
            )

            if mfa_result:
                recovery_codes = mfa_result.get('recovery_codes', [])
                auth_token = mfa_result.get('auth_token')

                if recovery_codes:
                    show_recovery_codes_dialog(
                        app_config=config,
                        recovery_codes=recovery_codes
                    )

                # IMPORTANTE: Continua para license_key
                continue

print("Autenticado com sucesso!")
print(f"Usuario: {validator.current_user.full_name if validator.current_user else username}")
```

---

## Modelos de Dados

### ValidationResult

```python
from bfk_authsystem import ValidationResult

result.valid              # bool: Licenca valida
result.message            # str: Mensagem descritiva
result.requires_action    # RequiredAction: Acao necessaria
result.days_offline       # int: Dias em modo offline
result.days_until_reauth  # int: Dias ate reautenticacao
result.days_since_auth    # int: Dias desde ultima auth
result.app_config         # AppConfig: Configuracao da app
result.license_info       # LicenseInfo: Info da licenca
result.machine_info       # MachineInfo: Info da maquina
result.error_code         # str: Codigo de erro
result.is_offline         # bool: Verificacao offline
result.mfa_setup_token    # str: Token para setup MFA
result.password_change_token  # str: Token para troca de senha
result.schedule_info      # dict: Restricoes de horario (v1.1.0+)
result.auth_token         # str: Token temporario para continuar fluxo (v1.2.0+)
```

### RequiredAction

```python
from bfk_authsystem import RequiredAction

RequiredAction.NONE            # Nenhuma acao
RequiredAction.CHANGE_PASSWORD # Trocar senha
RequiredAction.SETUP_MFA       # Configurar MFA
RequiredAction.VERIFY_MFA      # Verificar MFA
RequiredAction.REAUTH          # Reautenticar
```

### AppConfig

```python
from bfk_authsystem import AppConfig

config.app_code           # str: Codigo da app
config.app_name           # str: Nome interno
config.display_name       # str: Nome de exibicao
config.company_name       # str: Nome da empresa
config.support_email      # str: Email de suporte
config.primary_color      # str: Cor primaria (hex)
config.secondary_color    # str: Cor secundaria
config.accent_color       # str: Cor de destaque
config.logo_url           # str: URL do logo
config.welcome_message    # str: Mensagem de boas-vindas
config.reauth_days        # int: Dias para reauth
config.mfa_required       # bool: MFA obrigatorio
```

### LicenseInfo

```python
from bfk_authsystem import LicenseInfo, LicenseStatus

license.license_key       # str: Chave da licenca
license.user              # str: Nome do usuario
license.email             # str: Email
license.app_name          # str: Nome da app
license.status            # LicenseStatus: Status
license.expires_at        # datetime: Expiracao
license.is_valid          # bool: Se esta valida
license.is_lifetime       # bool: Se e vitalicia
```

### UserInfo

```python
from bfk_authsystem import UserInfo

user.id                   # int: ID
user.username             # str: Username
user.email                # str: Email
user.full_name            # str: Nome completo
user.is_active            # bool: Ativo
user.is_admin             # bool: Admin
user.mfa_enabled          # bool: MFA habilitado
user.force_password_change # bool: Deve trocar senha
```

### SessionInfo

```python
from bfk_authsystem import SessionInfo

session.id                # int: ID da sessao
session.device_info       # str: Info do dispositivo
session.ip_address        # str: IP
session.created_at        # datetime: Criacao
session.last_activity     # datetime: Ultima atividade
session.is_current        # bool: Sessao atual
```

### AuthTokens

```python
from bfk_authsystem import AuthTokens

tokens.session_token      # str: Token de sessao
tokens.refresh_token      # str: Token de refresh
tokens.expires_at         # datetime: Expiracao
tokens.recovery_codes     # List[str]: Codigos de recuperacao (opcional, apos MFA setup)
```

### MFASetupInfo

```python
from bfk_authsystem import MFASetupInfo

mfa.secret                # str: Chave secreta TOTP
mfa.qr_code               # str: QR Code em base64
mfa.provisioning_uri      # str: URI para apps
```

---

## Tratamento de Erros

### Excecoes

```python
from bfk_authsystem import (
    # Base
    AuthSystemError,          # Erro generico

    # Autenticacao
    AuthenticationError,      # Credenciais invalidas
    MFARequiredError,         # MFA necessario
    MFASetupRequiredError,    # Setup MFA obrigatorio
    PasswordChangeRequiredError, # Troca de senha obrigatoria
    ReauthenticationRequiredError, # Reautenticacao necessaria

    # Licenca
    LicenseError,             # Erro de licenca
    LicenseExpiredError,      # Licenca expirada
    LicenseNotFoundError,     # Licenca nao encontrada
    MachineLimitError,        # Limite de maquinas

    # Rede
    NetworkError,             # Erro de conexao
    ServerError,              # Erro no servidor
    TimeoutError,             # Timeout
    CircuitBreakerOpenError,  # Circuit breaker aberto

    # Cache
    CacheError,               # Erro de cache
    CacheExpiredError,        # Cache expirado
    CacheCorruptedError,      # Cache corrompido

    # Outros
    ConfigurationError,       # Erro de configuracao
    HardwareError,            # Erro de hardware
    ValidationError,          # Erro de validacao
)
```

### Exemplo de Tratamento

```python
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
    result = validator.verify(username='user', password='pass')

    if result.valid:
        print('Sucesso!')
    else:
        # Tratar por codigo de erro
        if result.error_code == 'MFA_REQUIRED':
            # Solicitar MFA
            pass
        elif result.error_code == 'LICENSE_KEY_REQUIRED':
            # Solicitar chave
            pass
        elif result.error_code == 'PASSWORD_CHANGE_REQUIRED':
            # Troca de senha
            pass

except AuthenticationError as e:
    print(f'Credenciais invalidas: {e}')

except MFARequiredError as e:
    print('MFA necessario')

except LicenseNotFoundError as e:
    print('Licenca nao encontrada')

except NetworkError as e:
    print(f'Erro de conexao: {e}')

except CircuitBreakerOpenError as e:
    print('Servidor temporariamente indisponivel')

except PasswordChangeRequiredError as e:
    print('Troca de senha obrigatoria')
```

### Codigos de Erro

| Codigo | Descricao | Acao |
|--------|-----------|------|
| `INVALID_CREDENTIALS` | Usuario ou senha incorretos | Solicitar novamente |
| `MFA_REQUIRED` | Codigo MFA necessario | Mostrar MFAVerifyDialog |
| `MFA_INVALID` | Codigo MFA invalido | Solicitar novo codigo |
| `MFA_SETUP_REQUIRED` | Setup MFA obrigatorio | Mostrar MFASetupDialog |
| `PASSWORD_CHANGE_REQUIRED` | Troca de senha obrigatoria | Mostrar ForceChangePasswordDialog |
| `LICENSE_KEY_REQUIRED` | Chave de licenca necessaria | Mostrar LicenseKeyDialog |
| `INVALID_LICENSE_KEY` | Chave invalida | Verificar chave |
| `LICENSE_INACTIVE` | Licenca desativada | Contatar admin |
| `HARDWARE_MISMATCH` | Hardware nao reconhecido | Contatar admin |
| `ACCOUNT_LOCKED` | Conta bloqueada | Aguardar |
| `USER_INACTIVE` | Usuario inativo | Contatar admin |
| `APP_NOT_FOUND` | Aplicacao nao existe | Verificar app_code |
| `APP_INACTIVE` | Aplicacao desativada | Contatar admin |
| `SCHEDULE_RESTRICTED` | Fora do horario permitido | Aguardar horario (v1.1.0+) |

---

## Modo Offline

A biblioteca suporta modo offline com cache local criptografado.

### Configuracao

```python
validator = LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP',
    max_offline_days=7,    # Dias maximos em modo offline
    cache_enabled=True     # Habilitar cache
)
```

### Funcionamento

1. Apos autenticacao online bem-sucedida, dados sao salvos em cache
2. Se servidor inacessivel, cache e usado automaticamente
3. Cache expira apos `max_offline_days` dias
4. Dados sao criptografados localmente

### Verificacao Offline

```python
result = validator.verify(username='user', password='pass')

if result.is_offline:
    print(f'Modo offline ({result.days_offline} dias)')
    print(f'Dias restantes: {result.days_until_reauth}')
```

---

## Restricoes de Horario (v1.1.0+)

Licencas podem ter restricoes de horario configuradas pelo administrador.

### Verificando Restricoes

```python
result = validator.verify(username='usuario', password='senha')

if result.valid:
    # Verificar se ha restricoes
    if result.schedule_info and result.schedule_info.get('has_restrictions'):
        info = result.schedule_info
        print(f"Fuso: {info.get('timezone')}")
        print(f"Dias restritos: {info.get('restricted_days')}")

        for dia, horarios in info.get('schedule', {}).items():
            print(f"  {dia}: {horarios}")
    else:
        print("Uso liberado 24h")

elif result.error_code == 'SCHEDULE_RESTRICTED':
    # Bloqueado por horario
    print(f"Bloqueado: {result.message}")
    info = result.schedule_info
    if info:
        print(f"Proximo horario: {info.get('next_interval')}")
```

### Estrutura de schedule_info

```python
{
    "has_restrictions": True,              # Se tem restricoes
    "timezone": "America/Sao_Paulo",       # Fuso horario
    "restricted_days": [                   # Dias com restricao
        "Segunda-feira",
        "Terca-feira"
    ],
    "total_restricted_days": 2,
    "schedule": {                          # Horarios permitidos
        "Segunda-feira": "08:00-12:00, 14:00-18:00",
        "Terca-feira": "08:00-12:00"
    }
}
```

### Notas

- Dias sem restricao = uso liberado 24h
- Cada dia pode ter ate 2 intervalos de horario
- Se `has_restrictions` for `False`, licenca sem restricoes
- Restricoes sao configuradas por licenca (individual por usuario)

---

## Recursos Avancados

### Retry com Backoff Exponencial

```python
from bfk_authsystem import LicenseValidator
from bfk_authsystem.retry_handler import RetryConfig

retry_config = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0
)

validator = LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP',
    retry_config=retry_config
)
```

### Circuit Breaker

Protege contra falhas em cascata.

```python
from bfk_authsystem import LicenseValidator
from bfk_authsystem.circuit_breaker import CircuitBreakerConfig

circuit_config = CircuitBreakerConfig(
    failure_threshold=5,     # Falhas ate abrir
    success_threshold=2,     # Sucessos para fechar
    timeout=60.0             # Tempo em half-open
)

validator = LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP',
    circuit_config=circuit_config
)
```

### Context Manager

```python
with LicenseValidator(
    server_url='https://authsystem.bfk.eng.br/api/v1',
    app_code='MINHA_APP'
) as validator:
    result = validator.verify(username, password)
    # Conexoes fechadas automaticamente
```

### Coleta de Hardware

```python
from bfk_authsystem import (
    get_hardware_info,
    get_hardware_components,
    generate_machine_id,
    get_system_info
)

# Machine ID unico
machine_id, components, system = get_hardware_info()
print(f'Machine ID: {machine_id}')
print(f'Components: {components}')
print(f'System: {system}')
```

---

## SDKs Outros

### C# (.NET)

```csharp
var client = new BfkAuthClient(
    "https://authsystem.bfk.eng.br/api/v1",
    "MINHA_APP"
);

var result = await client.VerifyLicenseAsync(
    username: "usuario",
    password: "senha",
    licenseKey: "BFK-XXXX-XXXX-XXXX"
);

if (result.Success)
{
    Console.WriteLine($"Licenca valida! Usuario: {result.License.User}");
}
```

**Arquivo:** `docs/sdk/csharp/BfkAuthClient.cs`

### TypeScript

```typescript
const client = new BfkAuthClient(
    "https://authsystem.bfk.eng.br/api/v1",
    "MINHA_APP"
);

const result = await client.verifyLicense(
    "usuario",
    "senha",
    "BFK-XXXX-XXXX-XXXX"
);

if (result.success) {
    console.log(`Licenca valida! Usuario: ${result.license.user}`);
}
```

**Arquivo:** `docs/sdk/typescript/bfk-auth.ts`

---

## Contato

**Suporte:** suporte@bfk.eng.br
**Documentacao:** https://authsystem.bfk.eng.br/docs
**API Health:** https://authsystem.bfk.eng.br/api/v1/health
