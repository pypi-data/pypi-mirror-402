"""
BFK AuthSystem - Force Change Password Dialog

Dialog para troca de senha obrigatoria (primeiro login ou reset por admin).
"""

from typing import Optional

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


class ForceChangePasswordDialog(BaseDialog):
    """
    Dialog para troca de senha obrigatoria.

    Usado quando o servidor retorna PASSWORD_CHANGE_REQUIRED.
    Nao solicita senha atual, apenas nova senha.
    """

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        title: str = "Troca de Senha Obrigatória",
        message: str = None
    ):
        """
        Inicializa o dialog.

        Args:
            parent: Widget pai
            app_config: Configuracao da aplicacao
            title: Titulo do dialog
            message: Mensagem customizada (opcional)
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        self._message = message or "Você precisa definir uma nova senha para continuar."
        super().__init__(parent, app_config, title)

        self._new_password = ""

        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Titulo
        layout.addWidget(self.create_title_label("Troca de Senha Obrigatória"))
        layout.addWidget(self.create_subtitle_label(self._message))

        layout.addSpacing(20)

        # Nova senha
        new_label = QLabel("Nova Senha")
        layout.addWidget(new_label)

        self.new_input = self.create_input(
            placeholder="Digite sua nova senha",
            password=True
        )
        layout.addWidget(self.new_input)

        # Confirmar nova senha
        confirm_label = QLabel("Confirmar Nova Senha")
        layout.addWidget(confirm_label)

        self.confirm_input = self.create_input(
            placeholder="Confirme a nova senha",
            password=True
        )
        layout.addWidget(self.confirm_input)

        # Requisitos de senha
        requirements = QLabel(
            "A senha deve ter pelo menos 8 caracteres, incluindo "
            "maiúsculas, minúsculas e números."
        )
        requirements.setStyleSheet("color: #666666; font-size: 11px;")
        requirements.setWordWrap(True)
        layout.addWidget(requirements)

        # Mensagem de erro
        self.error_label = self.create_error_label()
        layout.addWidget(self.error_label)

        layout.addSpacing(10)

        # Botao
        self.save_btn = self.create_primary_button("Alterar Senha")
        self.save_btn.setProperty("original_text", "Alterar Senha")
        self.save_btn.clicked.connect(self._on_save)
        layout.addWidget(self.save_btn)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

        # Enter para confirmar
        self.confirm_input.returnPressed.connect(self._on_save)
        self.new_input.returnPressed.connect(lambda: self.confirm_input.setFocus())

    def _on_save(self):
        """Handler do botao salvar."""
        # Validar nova senha
        new_password = self.new_input.text()
        confirm = self.confirm_input.text()

        if not new_password:
            self.show_error(self.error_label, "Digite a nova senha")
            self.new_input.setFocus()
            return

        if len(new_password) < 8:
            self.show_error(self.error_label, "Senha deve ter pelo menos 8 caracteres")
            self.new_input.setFocus()
            return

        # Verificar complexidade basica
        has_upper = any(c.isupper() for c in new_password)
        has_lower = any(c.islower() for c in new_password)
        has_digit = any(c.isdigit() for c in new_password)

        if not (has_upper and has_lower and has_digit):
            self.show_error(
                self.error_label,
                "Senha deve conter maiúsculas, minúsculas e números"
            )
            self.new_input.setFocus()
            return

        if new_password != confirm:
            self.show_error(self.error_label, "As senhas não conferem")
            self.confirm_input.setFocus()
            return

        self.hide_error(self.error_label)
        self._new_password = new_password
        self.accept()

    def get_new_password(self) -> str:
        """
        Retorna a nova senha inserida.

        Returns:
            Nova senha
        """
        return self._new_password

    def set_error(self, message: str):
        """Define mensagem de erro."""
        self.show_error(self.error_label, message)

    def set_loading(self, loading: bool):
        """Define estado de loading."""
        super().set_loading(
            loading,
            button=self.save_btn,
            inputs=[self.new_input, self.confirm_input]
        )


def show_force_change_password_dialog(
    app_config: AppConfig = None,
    parent=None,
    message: str = None
) -> Optional[str]:
    """
    Mostra dialog de troca de senha obrigatoria.

    Args:
        app_config: Configuracao da aplicacao
        parent: Widget pai
        message: Mensagem customizada

    Returns:
        Nova senha ou None se cancelado/fechado
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")

    from PyQt5.QtWidgets import QDialog

    dialog = ForceChangePasswordDialog(
        parent=parent,
        app_config=app_config,
        message=message
    )

    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_new_password()

    return None
