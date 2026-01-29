"""
BFK AuthSystem - Change Password Dialog

Dialog para alteração de senha.
"""

from typing import Optional, Tuple

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


class ChangePasswordDialog(BaseDialog):
    """
    Dialog para alterar senha.

    Campos:
    - Senha atual
    - Nova senha
    - Confirmar nova senha
    """

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        title: str = "Alterar Senha",
        require_current: bool = True
    ):
        """
        Inicializa o dialog.

        Args:
            parent: Widget pai
            app_config: Configuração da aplicação
            title: Título do dialog
            require_current: Se deve solicitar senha atual
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        self.require_current = require_current
        super().__init__(parent, app_config, title)

        self._current_password = ""
        self._new_password = ""

        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Titulo
        layout.addWidget(self.create_title_label("Alterar Senha"))
        layout.addWidget(self.create_subtitle_label(
            "Digite sua nova senha"
        ))

        layout.addSpacing(20)

        # Senha atual
        if self.require_current:
            current_label = QLabel("Senha Atual")
            layout.addWidget(current_label)

            self.current_input = self.create_input(
                placeholder="Digite sua senha atual",
                password=True
            )
            layout.addWidget(self.current_input)

        # Nova senha
        new_label = QLabel("Nova Senha")
        layout.addWidget(new_label)

        self.new_input = self.create_input(
            placeholder="Digite a nova senha",
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
            "A senha deve ter pelo menos 8 caracteres"
        )
        requirements.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(requirements)

        # Mensagem de erro
        self.error_label = self.create_error_label()
        layout.addWidget(self.error_label)

        layout.addSpacing(10)

        # Botoes
        buttons = QHBoxLayout()

        cancel = self.create_secondary_button("Cancelar")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        self.save_btn = self.create_primary_button("Salvar")
        self.save_btn.setProperty("original_text", "Salvar")
        self.save_btn.clicked.connect(self._on_save)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

        # Enter para confirmar
        self.confirm_input.returnPressed.connect(self._on_save)

    def _on_save(self):
        """Handler do botao salvar."""
        # Validar senha atual
        if self.require_current:
            current = self.current_input.text()
            if not current:
                self.show_error(self.error_label, "Digite sua senha atual")
                self.current_input.setFocus()
                return
            self._current_password = current

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

        if new_password != confirm:
            self.show_error(self.error_label, "As senhas não conferem")
            self.confirm_input.setFocus()
            return

        self.hide_error(self.error_label)
        self._new_password = new_password
        self.accept()

    def get_passwords(self) -> Tuple[str, str]:
        """
        Retorna as senhas inseridas.

        Returns:
            Tupla (senha_atual, nova_senha)
        """
        return self._current_password, self._new_password

    def set_error(self, message: str):
        """Define mensagem de erro."""
        self.show_error(self.error_label, message)

    def set_loading(self, loading: bool):
        """Define estado de loading."""
        inputs = [self.new_input, self.confirm_input]
        if self.require_current:
            inputs.insert(0, self.current_input)

        super().set_loading(
            loading,
            button=self.save_btn,
            inputs=inputs
        )


def show_change_password_dialog(
    app_config: AppConfig = None,
    parent=None,
    require_current: bool = True
) -> Optional[Tuple[str, str]]:
    """
    Mostra dialog de alteração de senha.

    Args:
        app_config: Configuracao da aplicacao
        parent: Widget pai
        require_current: Se deve solicitar senha atual

    Returns:
        Tupla (senha_atual, nova_senha) ou None se cancelado
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")

    from PyQt5.QtWidgets import QDialog

    dialog = ChangePasswordDialog(
        parent=parent,
        app_config=app_config,
        require_current=require_current
    )

    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_passwords()

    return None
