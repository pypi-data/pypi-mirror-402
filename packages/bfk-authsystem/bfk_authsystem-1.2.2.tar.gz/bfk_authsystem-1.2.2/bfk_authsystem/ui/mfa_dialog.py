"""
BFK AuthSystem - MFA Dialog

Dialogs para configuração e verificação de MFA.
"""

from typing import Optional, List
import base64

try:
    from PyQt5.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QTextEdit, QFrame
    )
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QPixmap
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .base_dialog import BaseDialog
from ..models import AppConfig, MFASetupInfo


class MFAVerifyDialog(BaseDialog):
    """
    Dialog para verificar token MFA.
    """

    def __init__(self, parent=None, app_config: AppConfig = None,
                 title: str = "Verificação MFA", allow_recovery: bool = True):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        self.allow_recovery = allow_recovery
        super().__init__(parent, app_config, title)
        self._token = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        layout.addWidget(self.create_title_label("Verificação em Duas Etapas"))
        layout.addWidget(self.create_subtitle_label("Digite o código do aplicativo autenticador"))
        layout.addSpacing(20)

        self.token_input = self.create_input(placeholder="000000")
        self.token_input.setMaxLength(8)
        self.token_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.token_input)

        self.error_label = self.create_error_label()
        layout.addWidget(self.error_label)

        if self.allow_recovery:
            recovery_btn = self.create_link_button("Usar código de recuperação")
            layout.addWidget(recovery_btn, alignment=Qt.AlignCenter)

        layout.addSpacing(10)
        buttons = QHBoxLayout()

        cancel = self.create_secondary_button("Cancelar")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        self.verify_btn = self.create_primary_button("Verificar")
        self.verify_btn.clicked.connect(self._on_verify)
        buttons.addWidget(self.verify_btn)

        layout.addLayout(buttons)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

        self.token_input.returnPressed.connect(self._on_verify)

    def _on_verify(self):
        token = self.token_input.text().strip()
        if not token or len(token) < 6:
            self.show_error(self.error_label, "Código inválido")
            return
        self._token = token
        self.accept()

    def get_token(self) -> str:
        return self._token

    def set_error(self, msg: str):
        self.show_error(self.error_label, msg)


class MFASetupDialog(BaseDialog):
    """Dialog para configurar MFA com QR code."""

    def __init__(self, parent=None, app_config: AppConfig = None,
                 mfa_info: MFASetupInfo = None, title: str = "Configurar MFA"):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        self.mfa_info = mfa_info
        super().__init__(parent, app_config, title)
        self._token = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        layout.addWidget(self.create_title_label("Configurar Autenticação"))
        layout.addWidget(self.create_subtitle_label(
            "Escaneie o QR code com seu aplicativo autenticador"
        ))

        # QR Code
        if self.mfa_info and self.mfa_info.qr_code:
            qr_label = QLabel()
            qr_label.setAlignment(Qt.AlignCenter)
            qr_data = self.mfa_info.qr_code
            if ',' in qr_data:
                qr_data = qr_data.split(',')[1]
            try:
                pixmap = QPixmap()
                pixmap.loadFromData(base64.b64decode(qr_data))
                qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
                layout.addWidget(qr_label, alignment=Qt.AlignCenter)
            except Exception:
                pass

        if self.mfa_info and self.mfa_info.secret:
            layout.addWidget(self.create_subtitle_label(f"Chave: {self.mfa_info.secret}"))

        layout.addSpacing(10)
        layout.addWidget(QLabel("Código de verificação:"))

        self.token_input = self.create_input(placeholder="000000")
        self.token_input.setMaxLength(6)
        layout.addWidget(self.token_input)

        self.error_label = self.create_error_label()
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        cancel = self.create_secondary_button("Cancelar")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        confirm = self.create_primary_button("Confirmar")
        confirm.clicked.connect(self._on_confirm)
        buttons.addWidget(confirm)

        layout.addLayout(buttons)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

        self.token_input.returnPressed.connect(self._on_confirm)

    def _on_confirm(self):
        token = self.token_input.text().strip()
        if len(token) != 6:
            self.show_error(self.error_label, "Digite um código de 6 dígitos")
            return
        self._token = token
        self.accept()

    def get_token(self) -> str:
        return self._token


class MFARecoveryCodesDialog(BaseDialog):
    """Dialog para exibir recovery codes."""

    def __init__(self, parent=None, app_config: AppConfig = None,
                 recovery_codes: List[str] = None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        self.recovery_codes = recovery_codes or []
        super().__init__(parent, app_config, "Códigos de Recuperação")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        layout.addWidget(self.create_title_label("Códigos de Recuperação"))

        warning = QLabel("IMPORTANTE: Guarde esses códigos em local seguro!")
        warning.setStyleSheet("color: #d32f2f; font-weight: bold;")
        warning.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning)

        codes_text = QTextEdit()
        codes_text.setReadOnly(True)
        codes_text.setPlainText("\n".join(self.recovery_codes))
        codes_text.setMaximumHeight(150)
        layout.addWidget(codes_text)

        close = self.create_primary_button("Entendi")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())


def show_mfa_verify_dialog(app_config: AppConfig = None, parent=None) -> Optional[str]:
    """Mostra dialog de verificação MFA."""
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")
    from PyQt5.QtWidgets import QDialog
    dialog = MFAVerifyDialog(parent=parent, app_config=app_config)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_token()
    return None


def show_mfa_setup_dialog(
    app_config: AppConfig = None,
    mfa_info: MFASetupInfo = None,
    parent=None
) -> Optional[str]:
    """
    Mostra dialog de configuracao MFA com QR code.

    Args:
        app_config: Configuracao visual da aplicacao (cores, logo)
        mfa_info: Dados do MFA (secret e qr_code base64)
        parent: Widget pai

    Returns:
        Codigo TOTP digitado pelo usuario ou None se cancelou
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")
    from PyQt5.QtWidgets import QDialog
    dialog = MFASetupDialog(parent=parent, app_config=app_config, mfa_info=mfa_info)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_token()
    return None
