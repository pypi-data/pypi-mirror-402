"""
BFK AuthSystem - Recovery Codes Dialog

Dialog para exibir e salvar códigos de recuperação MFA.
"""

from typing import List

try:
    from PyQt5.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTextEdit, QFileDialog, QApplication, QFrame
    )
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .base_dialog import BaseDialog
from ..models import AppConfig


class RecoveryCodesDialog(BaseDialog):
    """
    Dialog para exibir códigos de recuperação MFA.

    Permite:
    - Visualizar os códigos
    - Copiar para área de transferência
    - Salvar em arquivo
    """

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        recovery_codes: List[str] = None
    ):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        self.recovery_codes = recovery_codes or []
        super().__init__(parent, app_config, "Códigos de Recuperação")
        self.setMinimumSize(500, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Título
        title = self.create_title_label("Códigos de Recuperação")
        layout.addWidget(title)

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

        warning_title = QLabel("IMPORTANTE")
        warning_title.setStyleSheet("color: #e65100; font-weight: bold; font-size: 14px;")
        warning_title.setAlignment(Qt.AlignCenter)
        warning_layout.addWidget(warning_title)

        warning_text = QLabel(
            "Guarde esses códigos em local seguro!\n"
            "Cada código só pode ser usado uma vez.\n"
            "Use-os caso perca acesso ao autenticador."
        )
        warning_text.setStyleSheet("color: #e65100;")
        warning_text.setAlignment(Qt.AlignCenter)
        warning_layout.addWidget(warning_text)

        layout.addWidget(warning_frame)

        # Área dos códigos
        codes_frame = QFrame()
        codes_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        codes_layout = QVBoxLayout(codes_frame)
        codes_layout.setContentsMargins(20, 20, 20, 20)

        codes_label = QLabel("Seus códigos de recuperação:")
        codes_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        codes_layout.addWidget(codes_label)

        self.codes_text = QTextEdit()
        self.codes_text.setReadOnly(True)
        self.codes_text.setFont(QFont("Consolas", 14))
        self.codes_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 15px;
                line-height: 1.8;
            }
        """)
        self.codes_text.setMinimumHeight(200)

        # Formatar códigos em duas colunas
        codes_formatted = self._format_codes()
        self.codes_text.setPlainText(codes_formatted)

        codes_layout.addWidget(self.codes_text)
        layout.addWidget(codes_frame)

        # Botões de ação
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)

        # Botão Copiar
        copy_btn = QPushButton("Copiar Códigos")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_codes)
        actions_layout.addWidget(copy_btn)

        # Botão Salvar
        save_btn = QPushButton("Salvar em Arquivo")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_codes)
        actions_layout.addWidget(save_btn)

        layout.addLayout(actions_layout)

        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # Botão Fechar
        close_btn = self.create_primary_button("Entendi, salvei meus códigos")
        close_btn.setMinimumHeight(45)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

    def _format_codes(self) -> str:
        """Formata os códigos para exibição."""
        if not self.recovery_codes:
            return "Nenhum código disponível"

        lines = []
        for i, code in enumerate(self.recovery_codes, 1):
            lines.append(f"  {i:2d}.  {code}")

        return "\n".join(lines)

    def _copy_codes(self):
        """Copia códigos para área de transferência."""
        clipboard = QApplication.clipboard()
        codes_text = "\n".join(self.recovery_codes)
        clipboard.setText(codes_text)
        self.status_label.setText("Códigos copiados!")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def _save_codes(self):
        """Salva códigos em arquivo."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Códigos de Recuperação",
            "codigos_recuperacao_mfa.txt",
            "Arquivo de Texto (*.txt)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 50 + "\n")
                    f.write("BFK AuthSystem - Códigos de Recuperação MFA\n")
                    f.write("=" * 50 + "\n\n")
                    f.write("IMPORTANTE: Guarde este arquivo em local seguro!\n")
                    f.write("Cada código só pode ser usado uma vez.\n\n")
                    f.write("-" * 50 + "\n")
                    for i, code in enumerate(self.recovery_codes, 1):
                        f.write(f"  {i:2d}.  {code}\n")
                    f.write("-" * 50 + "\n")

                self.status_label.setText(f"Salvo em: {filename}")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            except Exception as e:
                self.status_label.setText(f"Erro ao salvar: {e}")
                self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")


def show_recovery_codes_dialog(
    app_config: AppConfig = None,
    recovery_codes: List[str] = None,
    parent=None
) -> None:
    """
    Exibe dialog com códigos de recuperação.

    Args:
        app_config: Configuração da aplicação
        recovery_codes: Lista de códigos
        parent: Widget pai
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")

    dialog = RecoveryCodesDialog(
        parent=parent,
        app_config=app_config,
        recovery_codes=recovery_codes
    )
    dialog.exec_()
