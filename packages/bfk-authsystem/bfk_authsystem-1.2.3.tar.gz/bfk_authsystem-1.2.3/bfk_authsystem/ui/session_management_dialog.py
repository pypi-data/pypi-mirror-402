"""
BFK AuthSystem - Session Management Dialog

Dialog para gerenciar sessões ativas do usuário.
"""

from typing import Optional, List, Dict
from datetime import datetime

try:
    from PyQt5.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QScrollArea, QWidget, QMessageBox
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .base_dialog import BaseDialog
from ..models import AppConfig, SessionInfo


class SessionManagementDialog(BaseDialog):
    """
    Dialog para gerenciar sessões ativas.

    Permite:
    - Visualizar todas as sessões ativas
    - Revogar sessões individuais
    - Revogar todas as sessões (exceto atual)

    Signals:
        session_revoked: Emitido quando uma sessão é revogada (session_id)
        all_sessions_revoked: Emitido quando todas as sessões são revogadas
    """

    session_revoked = None  # pyqtSignal(int)
    all_sessions_revoked = None  # pyqtSignal()

    def __init__(
        self,
        parent=None,
        app_config: AppConfig = None,
        sessions: List[SessionInfo] = None,
        title: str = "Gerenciar Sessões"
    ):
        """
        Inicializa o dialog.

        Args:
            parent: Widget pai
            app_config: Configuração da aplicação
            sessions: Lista de sessões ativas
            title: Título do dialog
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 necessário")

        from PyQt5.QtCore import pyqtSignal
        self.session_revoked = pyqtSignal(int)
        self.all_sessions_revoked = pyqtSignal()

        self.sessions = sessions or []
        self._revoked_sessions: List[int] = []
        self._revoke_all = False

        super().__init__(parent, app_config, title)
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Título
        layout.addWidget(self.create_title_label("Sessões Ativas"))
        layout.addWidget(self.create_subtitle_label(
            f"{len(self.sessions)} sessão(ões) encontrada(s)"
        ))

        layout.addSpacing(10)

        # Área de scroll para sessões
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
        """)

        sessions_widget = QWidget()
        self.sessions_layout = QVBoxLayout(sessions_widget)
        self.sessions_layout.setSpacing(10)
        self.sessions_layout.setContentsMargins(10, 10, 10, 10)

        # Criar items de sessão
        for session in self.sessions:
            session_item = self._create_session_item(session)
            self.sessions_layout.addWidget(session_item)

        self.sessions_layout.addStretch()
        scroll.setWidget(sessions_widget)
        layout.addWidget(scroll)

        # Botão revogar todas
        if len(self.sessions) > 1:
            revoke_all_btn = QPushButton("Revogar Todas as Outras Sessões")
            revoke_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #b71c1c;
                }
            """)
            revoke_all_btn.setCursor(Qt.PointingHandCursor)
            revoke_all_btn.clicked.connect(self._on_revoke_all)
            layout.addWidget(revoke_all_btn)

        layout.addSpacing(5)

        # Botão fechar
        close_btn = self.create_primary_button("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        # Rodape
        layout.addSpacing(15)
        layout.addLayout(self.create_footer())

    def _create_session_item(self, session: SessionInfo) -> QWidget:
        """Cria widget para uma sessão."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)

        # Info da sessão
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Dispositivo
        device = QLabel(session.device_info or "Dispositivo desconhecido")
        device.setStyleSheet("font-weight: bold; font-size: 13px;")
        info_layout.addWidget(device)

        # Detalhes
        details_parts = []
        if session.ip_address:
            details_parts.append(f"IP: {session.ip_address}")
        if session.last_activity:
            if isinstance(session.last_activity, datetime):
                details_parts.append(
                    f"Última atividade: {session.last_activity.strftime('%d/%m/%Y %H:%M')}"
                )
            else:
                details_parts.append(f"Última atividade: {session.last_activity}")

        if details_parts:
            details = QLabel(" | ".join(details_parts))
            details.setStyleSheet("color: #666666; font-size: 11px;")
            info_layout.addWidget(details)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Indicador ou botão de revogar
        if session.is_current:
            current_label = QLabel("Sessão Atual")
            current_label.setStyleSheet("""
                color: white;
                background-color: #4caf50;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            """)
            layout.addWidget(current_label)
        else:
            revoke_btn = QPushButton("Revogar")
            revoke_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff5722;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 15px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e64a19;
                }
            """)
            revoke_btn.setCursor(Qt.PointingHandCursor)
            revoke_btn.clicked.connect(
                lambda checked, sid=session.id, btn=revoke_btn, frm=frame:
                    self._on_revoke_session(sid, btn, frm)
            )
            layout.addWidget(revoke_btn)

        return frame

    def _on_revoke_session(self, session_id: int, button: QPushButton, frame: QFrame):
        """Handler para revogar uma sessão."""
        reply = QMessageBox.question(
            self,
            "Confirmar Revogação",
            "Deseja revogar esta sessão?\n\n"
            "O dispositivo será desconectado imediatamente.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._revoked_sessions.append(session_id)
            button.setText("Revogada")
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #9e9e9e;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 15px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
            frame.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 10px;
                    opacity: 0.7;
                }
            """)

    def _on_revoke_all(self):
        """Handler para revogar todas as sessões."""
        other_sessions = [s for s in self.sessions if not s.is_current]
        count = len(other_sessions)

        reply = QMessageBox.warning(
            self,
            "Confirmar Revogação",
            f"Deseja revogar TODAS as {count} outras sessões?\n\n"
            "Todos os outros dispositivos serão desconectados imediatamente.\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._revoke_all = True
            for session in other_sessions:
                self._revoked_sessions.append(session.id)
            self.accept()

    def get_revoked_sessions(self) -> List[int]:
        """
        Retorna IDs das sessões revogadas.

        Returns:
            Lista de IDs das sessões marcadas para revogação
        """
        return self._revoked_sessions

    def get_revoke_all(self) -> bool:
        """
        Retorna se todas as sessões devem ser revogadas.

        Returns:
            True se o usuário solicitou revogar todas
        """
        return self._revoke_all


def show_session_management_dialog(
    app_config: AppConfig = None,
    sessions: List[SessionInfo] = None,
    parent=None
) -> Optional[Dict]:
    """
    Mostra dialog de gerenciamento de sessões.

    Args:
        app_config: Configuração da aplicação
        sessions: Lista de sessões ativas
        parent: Widget pai

    Returns:
        Dict com 'revoked_sessions' e 'revoke_all', ou None se cancelado
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 necessário")

    from PyQt5.QtWidgets import QDialog

    dialog = SessionManagementDialog(
        parent=parent,
        app_config=app_config,
        sessions=sessions
    )

    if dialog.exec_() == QDialog.Accepted:
        return {
            'revoked_sessions': dialog.get_revoked_sessions(),
            'revoke_all': dialog.get_revoke_all()
        }

    return None
