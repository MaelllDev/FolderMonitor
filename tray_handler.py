import logging
import threading
from typing import TYPE_CHECKING, Optional

import pystray
from pystray import Icon, Menu, MenuItem

from icon_gen import create_tray_icon

if TYPE_CHECKING:
    from app import FolderMonitorApp

logger = logging.getLogger(__name__)

APP_NAME = "FolderMonitor"


class TrayHandler:
    """
    Encapsula o ícone da bandeja e o menu de contexto.
    Roda em thread própria para não bloquear o loop principal.
    """

    def __init__(self, app: "FolderMonitorApp") -> None:
        self.app    = app
        self._icon: Optional[Icon] = None
        self._icons = {
            "active": create_tray_icon(64, "active"),
            "paused": create_tray_icon(64, "paused"),
        }

    # Inicialização
    def run(self) -> None:
        """Cria e executa o ícone da bandeja usando modo detachado."""
        menu = self._build_menu()
        self._icon = Icon(
            name=APP_NAME,
            icon=self._icons["active"],
            title=APP_NAME,
            menu=menu,
        )
        logger.info("Ícone da bandeja iniciado.")
        self._icon.run_detached()

    def _build_menu(self) -> Menu:
        """Constrói o menu de contexto com estado dinâmico."""
        return Menu(
            MenuItem(
                "📊  Ver Estatísticas",
                self._on_stats,
                default=True,  # Ação no duplo clique
            ),
            MenuItem(
                "📁  Abrir Pasta Monitorada",
                self._on_open_folder,
                enabled=lambda _: bool(self.app.config.monitored_folder),
            ),
            Menu.SEPARATOR,
            # Pausa / Retomar com estado dinâmico
            MenuItem(
                "⏸  Pausar",
                self._on_pause,
                enabled=lambda _: (
                    self.app.monitor is not None
                    and self.app.monitor.is_running
                    and not self.app.monitor.is_paused
                ),
            ),
            MenuItem(
                "▶  Continuar",
                self._on_resume,
                enabled=lambda _: (
                    self.app.monitor is not None
                    and self.app.monitor.is_paused
                ),
            ),
            Menu.SEPARATOR,
            MenuItem(
                "🔄  Resetar Contadores",
                self._on_reset,
            ),
            MenuItem(
                "💾  Salvar Relatório",
                self._on_save_report,
            ),
            Menu.SEPARATOR,
            MenuItem(
                "⚙  Configurações",
                self._on_settings,
            ),
            Menu.SEPARATOR,
            MenuItem(
                "✕  Fechar",
                self._on_quit,
            ),
        )

    # Callbacks do menu
    def _on_stats(self, icon, item=None) -> None:
        self.app.request("show_stats")

    def _on_open_folder(self, icon, item) -> None:
        self.app.request("open_folder")

    def _on_pause(self, icon, item) -> None:
        self.app.request("pause")

    def _on_resume(self, icon, item) -> None:
        self.app.request("resume")

    def _on_reset(self, icon, item) -> None:
        self.app.request("reset")

    def _on_save_report(self, icon, item) -> None:
        self.app.request("save_report")

    def _on_settings(self, icon, item) -> None:
        self.app.request("show_settings")

    def _on_quit(self, icon, item) -> None:
        logger.info("Menu da bandeja: Quit acionado")
        self.app.request("quit")

    # Controle do ícone
    def set_state(self, state: str, tooltip: str | None = None) -> None:
        """
        Atualiza o ícone e tooltip da bandeja.
        state: "active" | "paused"
        """
        if not self._icon:
            return
        try:
            img = self._icons.get(state, self._icons["active"])
            self._icon.icon  = img
            if tooltip:
                self._icon.title = tooltip
        except Exception as e:
            logger.warning(f"Falha ao atualizar ícone: {e}")

    def notify(self, message: str, title: str = APP_NAME) -> None:
        """Exibe notificação balloon na bandeja do Windows."""
        if not self._icon:
            return
        try:
            self._icon.notify(message, title)
        except Exception as e:
            logger.debug(f"Falha na notificação: {e}")

    def stop(self) -> None:
        """Para o ícone da bandeja."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass