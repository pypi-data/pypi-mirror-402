"""
BFK AuthSystem - Login Dialog

Janela de login com usuário/senha.
"""

from typing import Optional, Tuple

try:
    from PyQt5.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QCheckBox, QSpacerItem, QSizePolicy
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .base_dialog import BaseDialog
from ..models import AppConfig


class LoginDialog(BaseDialog):
    """
    Dialog de login.

    Signals:
        login_success: Emitido quando login é bem-sucedido (username, password)
        forgot_password: Emitido quando usuário clica em "Esqueci senha"

    Exemplo:
        dialog = LoginDialog(app_config=config)
        if dialog.exec_() == QDialog.Accepted:
            username, password = dialog.get_credentials()
    """

    # Sinais devem ser definidos como atributos de classe
    if PYQT_AVAILABLE:
        login_success = pyqtSignal(str, str)
        forgot_password = pyqtSignal()

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        title: str = None,
        show_remember: bool = True,
        show_forgot_password: bool = True,
        allow_email: bool = True,
        server_url: str = None
    ):
        """
        Inicializa o dialog de login.

        Args:
            parent: Widget pai
            app_config: Configuração da aplicação
            title: Título do dialog
            show_remember: Mostrar checkbox "Lembrar-me"
            show_forgot_password: Mostrar link "Esqueci senha"
            allow_email: Permitir login com email
            server_url: URL do servidor (para recuperacao de senha)
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 é necessário. Instale com: pip install PyQt5")

        self.show_remember = show_remember
        self.show_forgot_password = show_forgot_password
        self.allow_email = allow_email
        self.server_url = server_url or 'https://authsystem.bfk.eng.br/api/v1'

        super().__init__(parent, app_config, title or "Login")

        self._username = ""
        self._password = ""
        self._remember = False
        self._mfa_required = False

        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Titulo
        title = self.create_title_label(self.app_config.display_name)
        layout.addWidget(title)

        # Subtitulo
        subtitle_text = "Entre com suas credenciais"
        if self.allow_email:
            subtitle_text = "Entre com seu usuário ou email"
        subtitle = self.create_subtitle_label(subtitle_text)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Campo de usuário
        username_label = QLabel("Usuário" + (" ou Email" if self.allow_email else ""))
        layout.addWidget(username_label)

        self.username_input = self.create_input(
            placeholder="Digite seu usuário" + (" ou email" if self.allow_email else "")
        )
        layout.addWidget(self.username_input)

        # Campo de senha
        password_label = QLabel("Senha")
        layout.addWidget(password_label)

        self.password_input = self.create_input(placeholder="Digite sua senha", password=True)
        layout.addWidget(self.password_input)

        # Mensagem de erro
        self.error_label = self.create_error_label()
        layout.addWidget(self.error_label)

        # Checkbox "Lembrar-me" e link "Esqueci senha"
        options_layout = QHBoxLayout()

        if self.show_remember:
            self.remember_checkbox = QCheckBox("Lembrar-me")
            options_layout.addWidget(self.remember_checkbox)
        else:
            options_layout.addStretch()

        if self.show_forgot_password:
            self.forgot_button = self.create_link_button("Esqueci minha senha")
            self.forgot_button.clicked.connect(self._on_forgot_password)
            options_layout.addWidget(self.forgot_button)

        layout.addLayout(options_layout)

        layout.addSpacing(10)

        # Botoes
        buttons_layout = QHBoxLayout()

        self.cancel_button = self.create_secondary_button("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.login_button = self.create_primary_button("Entrar")
        self.login_button.setProperty("original_text", "Entrar")
        self.login_button.clicked.connect(self._on_login)
        self.login_button.setDefault(True)
        buttons_layout.addWidget(self.login_button)

        layout.addLayout(buttons_layout)

        # Rodape
        layout.addSpacing(20)
        layout.addLayout(self.create_footer())

        # Conectar Enter nos campos
        self.username_input.returnPressed.connect(self._focus_password)
        self.password_input.returnPressed.connect(self._on_login)

    def _focus_password(self):
        """Move foco para campo de senha."""
        self.password_input.setFocus()

    def _on_login(self):
        """Handler do botao de login."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Validação
        if not username:
            self.show_error(self.error_label, "Digite seu usuário")
            self.username_input.setFocus()
            return

        if not password:
            self.show_error(self.error_label, "Digite sua senha")
            self.password_input.setFocus()
            return

        self.hide_error(self.error_label)

        # Salvar valores
        self._username = username
        self._password = password
        self._remember = self.remember_checkbox.isChecked() if self.show_remember else False

        self.accept()

    def _on_forgot_password(self):
        """Handler do link esqueci senha."""
        # Emitir sinal para quem estiver ouvindo
        if hasattr(self, 'forgot_password') and self.forgot_password:
            self.forgot_password.emit()

        # Mostrar dialog de recuperacao de senha
        from .forgot_password_dialog import show_forgot_password_dialog
        from PyQt5.QtWidgets import QMessageBox

        email = show_forgot_password_dialog(app_config=self.app_config, parent=self)
        if email:
            try:
                # Chamar API para enviar email de recuperacao
                from ..api_client import APIClient

                api = APIClient(base_url=self.server_url)
                response = api.request_password_reset(email)

                if response.get('success'):
                    QMessageBox.information(
                        self,
                        "Email Enviado",
                        "Se o email estiver cadastrado, voce recebera instrucoes para redefinir sua senha."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Erro",
                        response.get('message', 'Erro ao solicitar recuperacao de senha')
                    )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"Erro ao conectar com o servidor: {str(e)}"
                )

    def get_credentials(self) -> Tuple[str, str]:
        """
        Retorna as credenciais inseridas.

        Returns:
            Tupla (username, password)
        """
        return self._username, self._password

    def get_remember(self) -> bool:
        """Retorna se "Lembrar-me" foi marcado."""
        return self._remember

    def set_error(self, message: str):
        """Define mensagem de erro."""
        self.show_error(self.error_label, message)

    def set_loading(self, loading: bool):
        """Define estado de loading."""
        super().set_loading(
            loading,
            button=self.login_button,
            inputs=[self.username_input, self.password_input]
        )
        self.cancel_button.setEnabled(not loading)
        if self.show_forgot_password:
            self.forgot_button.setEnabled(not loading)


def show_login_dialog(
    app_config: AppConfig = None,
    parent=None,
    server_url: str = None
) -> Optional[Tuple[str, str]]:
    """
    Mostra dialog de login e retorna credenciais.

    Args:
        app_config: Configuracao da aplicacao
        parent: Widget pai
        server_url: URL do servidor (para recuperacao de senha)

    Returns:
        Tupla (username, password) ou None se cancelado
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 é necessário. Instale com: pip install PyQt5")

    from PyQt5.QtWidgets import QDialog

    dialog = LoginDialog(parent=parent, app_config=app_config, server_url=server_url)

    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_credentials()

    return None
