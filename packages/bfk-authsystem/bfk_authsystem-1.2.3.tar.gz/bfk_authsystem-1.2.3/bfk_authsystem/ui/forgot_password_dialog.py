"""
BFK AuthSystem - Forgot Password Dialog

Dialog para solicitar recuperação de senha.
"""

from typing import Optional
import re

try:
    from PyQt5.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton
    )
    from PyQt5.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .base_dialog import BaseDialog
from ..models import AppConfig


class ForgotPasswordDialog(BaseDialog):
    """
    Dialog para solicitar recuperação de senha.

    Solicita o email do usuário para enviar instruções de reset.
    """

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        title: str = "Recuperar Senha"
    ):
        """
        Inicializa o dialog.

        Args:
            parent: Widget pai
            app_config: Configuração da aplicação
            title: Título do dialog
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        super().__init__(parent, app_config, title)

        self._email = ""
        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Título
        layout.addWidget(self.create_title_label("Recuperar Senha"))
        layout.addWidget(self.create_subtitle_label(
            "Digite seu email para receber instruções de recuperação"
        ))

        layout.addSpacing(20)

        # Campo de email
        email_label = QLabel("Email")
        layout.addWidget(email_label)

        self.email_input = self.create_input(
            placeholder="Digite seu email cadastrado"
        )
        layout.addWidget(self.email_input)

        # Mensagem de erro
        self.error_label = self.create_error_label()
        layout.addWidget(self.error_label)

        # Informação
        info_label = QLabel(
            "Você receberá um email com instruções para redefinir sua senha."
        )
        info_label.setStyleSheet("color: #666666; font-size: 11px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addSpacing(10)

        # Botões
        buttons = QHBoxLayout()

        cancel = self.create_secondary_button("Cancelar")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        self.submit_btn = self.create_primary_button("Enviar")
        self.submit_btn.setProperty("original_text", "Enviar")
        self.submit_btn.clicked.connect(self._on_submit)
        buttons.addWidget(self.submit_btn)

        layout.addLayout(buttons)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

        # Enter para confirmar
        self.email_input.returnPressed.connect(self._on_submit)

    def _on_submit(self):
        """Handler do botão enviar."""
        email = self.email_input.text().strip()

        # Validar email
        if not email:
            self.show_error(self.error_label, "Digite seu email")
            self.email_input.setFocus()
            return

        # Validação básica de formato de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            self.show_error(self.error_label, "Email inválido")
            self.email_input.setFocus()
            return

        self.hide_error(self.error_label)
        self._email = email
        self.accept()

    def get_email(self) -> str:
        """
        Retorna o email inserido.

        Returns:
            Email do usuário
        """
        return self._email

    def set_error(self, message: str):
        """Define mensagem de erro."""
        self.show_error(self.error_label, message)

    def set_loading(self, loading: bool):
        """Define estado de loading."""
        super().set_loading(
            loading,
            button=self.submit_btn,
            inputs=[self.email_input]
        )


def show_forgot_password_dialog(
    app_config: AppConfig = None,
    parent=None
) -> Optional[str]:
    """
    Mostra dialog de recuperação de senha.

    Args:
        app_config: Configuração da aplicação
        parent: Widget pai

    Returns:
        Email inserido ou None se cancelado
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")

    from PyQt5.QtWidgets import QDialog

    dialog = ForgotPasswordDialog(
        parent=parent,
        app_config=app_config
    )

    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_email()

    return None
