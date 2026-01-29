"""
BFK AuthSystem - License Key Dialog

Janela para entrada da chave de licenca na primeira execucao.
"""

import re
from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QSpacerItem, QSizePolicy
    )
    from PyQt5.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .base_dialog import BaseDialog
from ..models import AppConfig


class LicenseKeyDialog(BaseDialog):
    """
    Dialog para entrada da chave de licenca.

    Usado na primeira execucao do aplicativo quando o servidor
    retorna LICENSE_KEY_REQUIRED.

    Exemplo:
        dialog = LicenseKeyDialog(app_config=config)
        if dialog.exec_() == QDialog.Accepted:
            license_key = dialog.get_license_key()
    """

    # Padrao da chave: BFK-XXXX-XXXX-XXXX
    LICENSE_KEY_PATTERN = r'^BFK-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        title: str = None,
        message: str = None
    ):
        """
        Inicializa o dialog de chave de licenca.

        Args:
            parent: Widget pai
            app_config: Configuracao da aplicacao
            title: Titulo do dialog
            message: Mensagem personalizada
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 e necessario. Instale com: pip install PyQt5")

        self._message = message or "Informe a chave de licenca recebida por email"

        super().__init__(parent, app_config, title or "Ativacao de Licenca")

        self._license_key = ""

        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Titulo
        title = self.create_title_label("Ativacao de Licenca")
        layout.addWidget(title)

        # Subtitulo
        subtitle = self.create_subtitle_label("Primeira execucao detectada")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # Mensagem explicativa
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #555555; font-size: 13px;")
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)

        layout.addSpacing(20)

        # Campo de chave de licenca
        key_label = QLabel("Chave de Licenca")
        layout.addWidget(key_label)

        self.key_input = self.create_input(placeholder="BFK-XXXX-XXXX-XXXX")
        self.key_input.setMaxLength(19)  # BFK-XXXX-XXXX-XXXX = 19 chars
        layout.addWidget(self.key_input)

        # Formato esperado
        format_label = QLabel("Formato: BFK-XXXX-XXXX-XXXX")
        format_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(format_label)

        # Mensagem de erro
        self.error_label = self.create_error_label()
        layout.addWidget(self.error_label)

        layout.addSpacing(10)

        # Botoes
        buttons_layout = QHBoxLayout()

        self.cancel_button = self.create_secondary_button("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.confirm_button = self.create_primary_button("Ativar")
        self.confirm_button.setProperty("original_text", "Ativar")
        self.confirm_button.clicked.connect(self._on_confirm)
        self.confirm_button.setDefault(True)
        buttons_layout.addWidget(self.confirm_button)

        layout.addLayout(buttons_layout)

        # Rodape
        layout.addSpacing(20)
        layout.addLayout(self.create_footer())

        # Conectar Enter no campo
        self.key_input.returnPressed.connect(self._on_confirm)

        # Auto-formatar enquanto digita
        self.key_input.textChanged.connect(self._format_key)

    def _format_key(self, text: str):
        """Formata a chave enquanto digita."""
        # Remove caracteres invalidos e converte para maiusculo
        clean = re.sub(r'[^A-Za-z0-9]', '', text.upper())

        # Adiciona prefixo BFK se necessario
        if clean and not clean.startswith('BFK'):
            if len(clean) <= 3:
                if 'BFK'.startswith(clean):
                    clean = clean
                else:
                    clean = 'BFK' + clean
            else:
                clean = 'BFK' + clean

        # Formata com hifens
        formatted = ''
        # Divide em partes: BFK, XXXX, XXXX, XXXX
        if len(clean) <= 3:
            formatted = clean
        else:
            formatted = clean[:3] + '-'
            remaining = clean[3:]
            for i, char in enumerate(remaining):
                if i > 0 and i % 4 == 0 and i < 12:
                    formatted += '-'
                formatted += char

        # Limita tamanho
        if len(formatted) > 19:
            formatted = formatted[:19]

        # Atualiza campo sem disparar evento
        if formatted != text:
            cursor_pos = self.key_input.cursorPosition()
            self.key_input.blockSignals(True)
            self.key_input.setText(formatted)
            # Ajusta posicao do cursor
            new_pos = min(cursor_pos + (len(formatted) - len(text)), len(formatted))
            self.key_input.setCursorPosition(new_pos)
            self.key_input.blockSignals(False)

    def _validate_key(self, key: str) -> bool:
        """Valida formato da chave."""
        return bool(re.match(self.LICENSE_KEY_PATTERN, key))

    def _on_confirm(self):
        """Handler do botao de confirmar."""
        key = self.key_input.text().strip().upper()

        # Validacao
        if not key:
            self.show_error(self.error_label, "Digite a chave de licenca")
            self.key_input.setFocus()
            return

        if not self._validate_key(key):
            self.show_error(self.error_label, "Formato de chave invalido")
            self.key_input.setFocus()
            return

        self.hide_error(self.error_label)

        # Salvar valor
        self._license_key = key

        self.accept()

    def get_license_key(self) -> str:
        """
        Retorna a chave de licenca inserida.

        Returns:
            Chave de licenca
        """
        return self._license_key

    def set_error(self, message: str):
        """Define mensagem de erro."""
        self.show_error(self.error_label, message)

    def set_loading(self, loading: bool):
        """Define estado de loading."""
        super().set_loading(
            loading,
            button=self.confirm_button,
            inputs=[self.key_input]
        )
        self.cancel_button.setEnabled(not loading)


def show_license_key_dialog(
    app_config: AppConfig = None,
    parent=None,
    message: str = None
) -> Optional[str]:
    """
    Mostra dialog de chave de licenca e retorna a chave.

    Args:
        app_config: Configuracao da aplicacao
        parent: Widget pai
        message: Mensagem personalizada

    Returns:
        Chave de licenca ou None se cancelado
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 e necessario. Instale com: pip install PyQt5")

    from PyQt5.QtWidgets import QDialog

    dialog = LicenseKeyDialog(
        parent=parent,
        app_config=app_config,
        message=message
    )

    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_license_key()

    return None
