"""
BFK AuthSystem - Regenerate Recovery Codes Dialog

Dialog para regenerar códigos de recuperação MFA.
"""

from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QFrame
    )
    from PyQt5.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .base_dialog import BaseDialog
from ..models import AppConfig


class RegenerateRecoveryCodesDialog(BaseDialog):
    """
    Dialog para regenerar códigos de recuperação MFA.

    Solicita a senha atual como confirmação antes de regenerar.
    Os códigos anteriores serão invalidados.
    """

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        title: str = "Regenerar Códigos"
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

        self._password = ""
        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Título
        layout.addWidget(self.create_title_label("Regenerar Códigos de Recuperação"))

        layout.addSpacing(10)

        # Aviso importante
        warning_frame = QFrame()
        warning_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border: 2px solid #ff9800;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        warning_layout = QVBoxLayout(warning_frame)
        warning_layout.setContentsMargins(15, 15, 15, 15)

        warning_title = QLabel("ATENÇÃO")
        warning_title.setStyleSheet("color: #e65100; font-weight: bold; font-size: 14px;")
        warning_title.setAlignment(Qt.AlignCenter)
        warning_layout.addWidget(warning_title)

        warning_text = QLabel(
            "Ao regenerar os códigos de recuperação:\n\n"
            "- Todos os códigos anteriores serão INVALIDADOS\n"
            "- Novos códigos serão gerados\n"
            "- Você deverá salvar os novos códigos em local seguro\n\n"
            "Esta ação não pode ser desfeita."
        )
        warning_text.setStyleSheet("color: #e65100;")
        warning_text.setAlignment(Qt.AlignLeft)
        warning_layout.addWidget(warning_text)

        layout.addWidget(warning_frame)

        layout.addSpacing(15)

        # Campo de senha
        password_label = QLabel("Digite sua senha para confirmar:")
        layout.addWidget(password_label)

        self.password_input = self.create_input(
            placeholder="Senha atual",
            password=True
        )
        layout.addWidget(self.password_input)

        # Mensagem de erro
        self.error_label = self.create_error_label()
        layout.addWidget(self.error_label)

        layout.addSpacing(10)

        # Botões
        buttons = QHBoxLayout()

        cancel = self.create_secondary_button("Cancelar")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        self.regenerate_btn = QPushButton("Regenerar Códigos")
        self.regenerate_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.regenerate_btn.setCursor(Qt.PointingHandCursor)
        self.regenerate_btn.setProperty("original_text", "Regenerar Códigos")
        self.regenerate_btn.clicked.connect(self._on_regenerate)
        buttons.addWidget(self.regenerate_btn)

        layout.addLayout(buttons)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

        # Enter para confirmar
        self.password_input.returnPressed.connect(self._on_regenerate)

    def _on_regenerate(self):
        """Handler do botão regenerar."""
        password = self.password_input.text()

        # Validar senha
        if not password:
            self.show_error(self.error_label, "Digite sua senha")
            self.password_input.setFocus()
            return

        self.hide_error(self.error_label)
        self._password = password
        self.accept()

    def get_password(self) -> str:
        """
        Retorna a senha inserida.

        Returns:
            Senha do usuário
        """
        return self._password

    def set_error(self, message: str):
        """Define mensagem de erro."""
        self.show_error(self.error_label, message)

    def set_loading(self, loading: bool):
        """Define estado de loading."""
        self.regenerate_btn.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
        if loading:
            self.regenerate_btn.setText("Aguarde...")
        else:
            self.regenerate_btn.setText(
                self.regenerate_btn.property("original_text") or "Regenerar Códigos"
            )


def show_regenerate_codes_dialog(
    app_config: AppConfig = None,
    parent=None
) -> Optional[str]:
    """
    Mostra dialog de regeneração de códigos.

    Args:
        app_config: Configuração da aplicação
        parent: Widget pai

    Returns:
        Senha inserida ou None se cancelado
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")

    from PyQt5.QtWidgets import QDialog

    dialog = RegenerateRecoveryCodesDialog(
        parent=parent,
        app_config=app_config
    )

    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_password()

    return None
