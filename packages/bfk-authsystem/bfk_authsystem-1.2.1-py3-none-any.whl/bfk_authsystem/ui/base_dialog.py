"""
BFK AuthSystem - Base Dialog

Dialog base com personalização de cores da aplicação.
"""

from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QLineEdit, QFrame, QWidget,
        QSpacerItem, QSizePolicy
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # Stubs para quando PyQt5 nao esta disponivel
    QDialog = object

from ..models import AppConfig


class BaseDialog(QDialog if PYQT_AVAILABLE else object):
    """
    Dialog base com estilos personalizaveis.

    Fornece:
    - Estilizacao baseada em AppConfig
    - Layout consistente
    - Componentes reutilizaveis
    """

    def __init__(self, parent=None, app_config: AppConfig = None, title: str = ""):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 é necessário para usar dialogs. Instale com: pip install PyQt5")

        super().__init__(parent)

        self.app_config = app_config or AppConfig(
            app_code='DEFAULT',
            app_name='Application',
            display_name='Application',
            company_name='Company',
            support_email='support@example.com'
        )

        self.setWindowTitle(title or self.app_config.display_name)
        self.setModal(True)
        self.setMinimumWidth(400)

        # Aplicar estilos
        self._apply_styles()

    def _apply_styles(self):
        """Aplica estilos baseados na configuracao."""
        primary = self.app_config.primary_color
        secondary = self.app_config.secondary_color
        accent = self.app_config.accent_color

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}

            QLabel {{
                color: #333333;
            }}

            QLabel.title {{
                font-size: 18px;
                font-weight: bold;
                color: {primary};
            }}

            QLabel.subtitle {{
                font-size: 12px;
                color: #666666;
            }}

            QLabel.error {{
                color: #d32f2f;
                font-size: 12px;
            }}

            QLineEdit {{
                padding: 10px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
            }}

            QLineEdit:focus {{
                border-color: {primary};
            }}

            QLineEdit:disabled {{
                background-color: #eeeeee;
            }}

            QPushButton {{
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}

            QPushButton.primary {{
                background-color: {primary};
                color: white;
            }}

            QPushButton.primary:hover {{
                background-color: {self._darken_color(primary)};
            }}

            QPushButton.primary:pressed {{
                background-color: {self._darken_color(primary, 0.2)};
            }}

            QPushButton.primary:disabled {{
                background-color: #cccccc;
            }}

            QPushButton.secondary {{
                background-color: transparent;
                color: {secondary};
                border: 1px solid {secondary};
            }}

            QPushButton.secondary:hover {{
                background-color: #f0f0f0;
            }}

            QPushButton.link {{
                background-color: transparent;
                color: {primary};
                border: none;
                text-decoration: underline;
            }}

            QFrame.separator {{
                background-color: #dddddd;
            }}
        """)

    def _darken_color(self, hex_color: str, factor: float = 0.1) -> str:
        """Escurece uma cor hex."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))

        return f"#{r:02x}{g:02x}{b:02x}"

    def create_title_label(self, text: str) -> 'QLabel':
        """Cria label de titulo."""
        label = QLabel(text)
        label.setProperty("class", "title")
        label.setAlignment(Qt.AlignCenter)
        return label

    def create_subtitle_label(self, text: str) -> 'QLabel':
        """Cria label de subtitulo."""
        label = QLabel(text)
        label.setProperty("class", "subtitle")
        label.setAlignment(Qt.AlignCenter)
        return label

    def create_error_label(self) -> 'QLabel':
        """Cria label para mensagens de erro."""
        label = QLabel("")
        label.setProperty("class", "error")
        label.setAlignment(Qt.AlignCenter)
        label.hide()
        return label

    def create_input(self, placeholder: str = "", password: bool = False) -> 'QLineEdit':
        """Cria campo de input."""
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        if password:
            input_field.setEchoMode(QLineEdit.Password)
        return input_field

    def create_primary_button(self, text: str) -> 'QPushButton':
        """Cria botao primario."""
        button = QPushButton(text)
        button.setProperty("class", "primary")
        button.setCursor(Qt.PointingHandCursor)
        return button

    def create_secondary_button(self, text: str) -> 'QPushButton':
        """Cria botao secundario."""
        button = QPushButton(text)
        button.setProperty("class", "secondary")
        button.setCursor(Qt.PointingHandCursor)
        return button

    def create_link_button(self, text: str) -> 'QPushButton':
        """Cria botao estilo link."""
        button = QPushButton(text)
        button.setProperty("class", "link")
        button.setCursor(Qt.PointingHandCursor)
        return button

    def create_separator(self) -> 'QFrame':
        """Cria linha separadora."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setProperty("class", "separator")
        line.setFixedHeight(1)
        return line

    def create_spacer(self, vertical: bool = True) -> 'QSpacerItem':
        """Cria espacador."""
        if vertical:
            return QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        return QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

    def create_footer(self) -> 'QVBoxLayout':
        """Cria rodape padrao com informacoes do desenvolvedor."""
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(2)

        footer_title = QLabel("BFK AuthSystem")
        footer_title.setStyleSheet("color: #666666; font-size: 11px;")
        footer_title.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(footer_title)

        footer_dev = QLabel("Desenvolvido por: Bruno Francisco Kons")
        footer_dev.setStyleSheet("color: #999999; font-size: 9px;")
        footer_dev.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(footer_dev)

        return footer_layout

    def show_error(self, error_label: 'QLabel', message: str):
        """Mostra mensagem de erro."""
        error_label.setText(message)
        error_label.show()

    def hide_error(self, error_label: 'QLabel'):
        """Esconde mensagem de erro."""
        error_label.hide()
        error_label.setText("")

    def set_loading(self, loading: bool, button: 'QPushButton' = None, inputs: list = None):
        """Define estado de loading."""
        if button:
            button.setEnabled(not loading)
            if loading:
                button.setText("Aguarde...")
            else:
                button.setText(button.property("original_text") or "OK")

        if inputs:
            for input_field in inputs:
                input_field.setEnabled(not loading)
