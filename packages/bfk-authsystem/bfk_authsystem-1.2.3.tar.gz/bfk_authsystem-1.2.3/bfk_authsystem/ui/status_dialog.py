"""
BFK AuthSystem - Status Dialog

Dialog para exibir status da licença e informações do usuário.
"""

from typing import Optional, List
from datetime import datetime

try:
    from PyQt5.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QGridLayout, QScrollArea, QWidget,
        QMessageBox
    )
    from PyQt5.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .base_dialog import BaseDialog
from ..models import AppConfig, LicenseInfo, SessionInfo, UserInfo


class StatusDialog(BaseDialog):
    """
    Dialog para exibir status da licença.

    Mostra:
    - Informações do usuário
    - Status da licença
    - Sessões ativas
    """

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        user_info: UserInfo = None,
        license_info: LicenseInfo = None,
        sessions: List[SessionInfo] = None,
        days_offline: int = 0,
        is_offline: bool = False,
        days_until_reauth: int = 30
    ):
        """
        Inicializa o dialog.

        Args:
            parent: Widget pai
            app_config: Configuração da aplicação
            user_info: Informações do usuário
            license_info: Informações da licença
            sessions: Lista de sessões ativas
            days_offline: Dias em modo offline
            is_offline: Se está em modo offline
            days_until_reauth: Dias até reautenticação
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        self.user_info = user_info
        self.license_info = license_info
        self.sessions = sessions or []
        self.days_offline = days_offline
        self.is_offline = is_offline
        self.days_until_reauth = days_until_reauth

        super().__init__(parent, app_config, "Status da Licença")
        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Titulo
        layout.addWidget(self.create_title_label(self.app_config.display_name))

        # Status online/offline
        status_text = "Online" if not self.is_offline else f"Offline ({self.days_offline} dias)"
        status_color = "#4caf50" if not self.is_offline else "#ff9800"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)

        layout.addWidget(self.create_separator())

        # Informacoes do usuario
        if self.user_info:
            layout.addWidget(self._create_user_section())
            layout.addWidget(self.create_separator())

        # Informacoes da licenca
        if self.license_info:
            layout.addWidget(self._create_license_section())
            layout.addWidget(self.create_separator())

        # Sessoes ativas
        if self.sessions:
            layout.addWidget(self._create_sessions_section())
            layout.addWidget(self.create_separator())

        # Botao fechar
        close_btn = self.create_primary_button("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

    def _create_user_section(self) -> 'QWidget':
        """Cria seção de informações do usuário."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Usuário")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        row = 0
        if self.user_info.username:
            grid.addWidget(QLabel("Username:"), row, 0)
            grid.addWidget(QLabel(self.user_info.username), row, 1)
            row += 1

        if self.user_info.email:
            grid.addWidget(QLabel("Email:"), row, 0)
            grid.addWidget(QLabel(self.user_info.email), row, 1)
            row += 1

        if self.user_info.full_name:
            grid.addWidget(QLabel("Nome:"), row, 0)
            grid.addWidget(QLabel(self.user_info.full_name), row, 1)
            row += 1

        mfa_status = "Ativado" if self.user_info.mfa_enabled else "Desativado"
        grid.addWidget(QLabel("MFA:"), row, 0)
        mfa_label = QLabel(mfa_status)
        mfa_label.setStyleSheet(
            f"color: {'#4caf50' if self.user_info.mfa_enabled else '#666666'};"
        )
        grid.addWidget(mfa_label, row, 1)

        layout.addLayout(grid)
        return widget

    def _create_license_section(self) -> 'QWidget':
        """Cria seção de informações da licença."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Licença")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        row = 0

        # Chave da licenca (parcial)
        if self.license_info.license_key:
            key = self.license_info.license_key
            masked_key = key[:4] + "****" + key[-4:] if len(key) > 8 else key
            grid.addWidget(QLabel("Chave:"), row, 0)
            grid.addWidget(QLabel(masked_key), row, 1)
            row += 1

        # Status
        grid.addWidget(QLabel("Status:"), row, 0)
        status = self.license_info.status.value if self.license_info.status else "Ativo"
        status_label = QLabel(status.capitalize())
        status_label.setStyleSheet(
            f"color: {'#4caf50' if status == 'active' else '#d32f2f'};"
        )
        grid.addWidget(status_label, row, 1)
        row += 1

        # Revalidação
        if self.license_info.expires_at:
            grid.addWidget(QLabel("Revalidação:"), row, 0)
            exp_date = self.license_info.expires_at
            if isinstance(exp_date, datetime):
                exp_str = exp_date.strftime("%d/%m/%Y")
            else:
                exp_str = str(exp_date)
            grid.addWidget(QLabel(exp_str), row, 1)
            row += 1

        # Dias até reautenticação
        if self.days_until_reauth > 0:
            grid.addWidget(QLabel("Proxima reauth:"), row, 0)
            reauth_label = QLabel(f"{self.days_until_reauth} dias")
            if self.days_until_reauth <= 3:
                reauth_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            elif self.days_until_reauth <= 7:
                reauth_label.setStyleSheet("color: #ff9800;")
            else:
                reauth_label.setStyleSheet("color: #4caf50;")
            grid.addWidget(reauth_label, row, 1)
            row += 1

        layout.addLayout(grid)
        return widget

    def _create_sessions_section(self) -> 'QWidget':
        """Cria seção de sessões ativas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        title = QLabel(f"Sessões Ativas ({len(self.sessions)})")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Lista de sessoes
        for session in self.sessions[:5]:  # Limitar a 5 sessoes
            session_widget = self._create_session_item(session)
            layout.addWidget(session_widget)

        if len(self.sessions) > 5:
            more = QLabel(f"... e mais {len(self.sessions) - 5} sessões")
            more.setStyleSheet("color: #666666; font-size: 11px;")
            layout.addWidget(more)

        return widget

    def _create_session_item(self, session: SessionInfo) -> 'QWidget':
        """Cria item de sessão."""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)

        # Info da sessao
        info_layout = QVBoxLayout()

        device = QLabel(session.device_info or "Dispositivo desconhecido")
        device.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(device)

        details = []
        if session.ip_address:
            details.append(session.ip_address)
        if session.last_activity:
            if isinstance(session.last_activity, datetime):
                details.append(session.last_activity.strftime("%d/%m %H:%M"))
            else:
                details.append(str(session.last_activity))

        if details:
            detail_label = QLabel(" | ".join(details))
            detail_label.setStyleSheet("color: #666666; font-size: 11px;")
            info_layout.addWidget(detail_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Indicador de sessao atual
        if session.is_current:
            current = QLabel("(Atual)")
            current.setStyleSheet("color: #4caf50; font-weight: bold;")
            layout.addWidget(current)

        return widget


def show_status_dialog(
    app_config: AppConfig = None,
    user_info: UserInfo = None,
    license_info: LicenseInfo = None,
    sessions: List[SessionInfo] = None,
    days_offline: int = 0,
    is_offline: bool = False,
    days_until_reauth: int = 30,
    parent=None
) -> None:
    """
    Mostra dialog de status da licença.

    Args:
        app_config: Configuração da aplicação
        user_info: Informações do usuário
        license_info: Informações da licença
        sessions: Lista de sessões ativas
        days_offline: Dias em modo offline
        is_offline: Se está em modo offline
        days_until_reauth: Dias até reautenticação
        parent: Widget pai
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")

    dialog = StatusDialog(
        parent=parent,
        app_config=app_config,
        user_info=user_info,
        license_info=license_info,
        sessions=sessions,
        days_offline=days_offline,
        is_offline=is_offline,
        days_until_reauth=days_until_reauth
    )
    dialog.exec_()
