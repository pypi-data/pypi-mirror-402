"""
BFK AuthSystem - UI Components

Componentes de interface grafica (PyQt5) para dialogs de autenticacao.

Requer PyQt5 instalado:
    pip install PyQt5

Uso:
    from bfk_authsystem.ui import LoginDialog, show_login_dialog

    # Modo simples
    credentials = show_login_dialog(app_config=config)
    if credentials:
        username, password = credentials

    # Modo avancado
    dialog = LoginDialog(app_config=config)
    if dialog.exec_() == QDialog.Accepted:
        username, password = dialog.get_credentials()
"""

# Verificar disponibilidade do PyQt5
try:
    from PyQt5.QtWidgets import QDialog
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# Imports condicionais - so importa se PyQt5 disponivel
if PYQT_AVAILABLE:
    # Base dialog
    from .base_dialog import BaseDialog

    # Login dialog
    from .login_dialog import LoginDialog, show_login_dialog

    # MFA dialogs
    from .mfa_dialog import (
        MFAVerifyDialog,
        MFASetupDialog,
        MFARecoveryCodesDialog,
        show_mfa_verify_dialog,
        show_mfa_setup_dialog
    )

    # Change password dialog
    from .change_password_dialog import (
        ChangePasswordDialog,
        show_change_password_dialog
    )

    # Force change password dialog (primeiro login)
    from .force_change_password_dialog import (
        ForceChangePasswordDialog,
        show_force_change_password_dialog
    )

    # Status dialog
    from .status_dialog import (
        StatusDialog,
        show_status_dialog
    )

    # Recovery codes dialog
    from .recovery_codes_dialog import (
        RecoveryCodesDialog,
        show_recovery_codes_dialog
    )

    # Forgot password dialog
    from .forgot_password_dialog import (
        ForgotPasswordDialog,
        show_forgot_password_dialog
    )

    # Session management dialog
    from .session_management_dialog import (
        SessionManagementDialog,
        show_session_management_dialog
    )

    # Regenerate codes dialog
    from .regenerate_codes_dialog import (
        RegenerateRecoveryCodesDialog,
        show_regenerate_codes_dialog
    )

    # License key dialog
    from .license_key_dialog import (
        LicenseKeyDialog,
        show_license_key_dialog
    )

    __all__ = [
        # Disponibilidade
        'PYQT_AVAILABLE',

        # Base
        'BaseDialog',

        # Login
        'LoginDialog',
        'show_login_dialog',

        # MFA
        'MFAVerifyDialog',
        'MFASetupDialog',
        'MFARecoveryCodesDialog',
        'show_mfa_verify_dialog',
        'show_mfa_setup_dialog',

        # Change Password
        'ChangePasswordDialog',
        'show_change_password_dialog',

        # Force Change Password
        'ForceChangePasswordDialog',
        'show_force_change_password_dialog',

        # Status
        'StatusDialog',
        'show_status_dialog',

        # Recovery Codes
        'RecoveryCodesDialog',
        'show_recovery_codes_dialog',

        # Forgot Password
        'ForgotPasswordDialog',
        'show_forgot_password_dialog',

        # Session Management
        'SessionManagementDialog',
        'show_session_management_dialog',

        # Regenerate Codes
        'RegenerateRecoveryCodesDialog',
        'show_regenerate_codes_dialog',

        # License Key
        'LicenseKeyDialog',
        'show_license_key_dialog',
    ]
else:
    # PyQt5 nao disponivel - apenas exportar flag
    __all__ = ['PYQT_AVAILABLE']
