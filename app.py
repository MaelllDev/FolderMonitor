import logging
import os
import queue
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Optional

from config_manager import ConfigManager
from monitor import FolderMonitor
from reports import ReportManager
from settings_win import SettingsWindow
from stats_win import StatsWindow
from tray_handler import TrayHandler

logger = logging.getLogger(__name__)


class FolderMonitorApp:
    """Classe central que integra todos os módulos do aplicativo."""

    VERSION = "1.0.0"

    def __init__(self) -> None:
        # Configurações
        self.config         = ConfigManager()
        self.report_manager = ReportManager(self.config)

        # Estado da sessão
        self.monitor:       Optional[FolderMonitor] = None
        self.session_start: Optional[datetime]      = None

        # Tkinter root (oculto, apenas para event loop)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("FolderMonitor")
        # Impede que o app feche ao destruir janelas secundárias
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        # Fila de ações entre threads
        self._ui_queue: queue.Queue[dict] = queue.Queue()

        # Sub-janelas (criadas sob demanda)
        self._stats_win    = StatsWindow(self)
        self._settings_win = SettingsWindow(self)

        # Bandeja do sistema
        self.tray = TrayHandler(self)
        self.tray.run()

        # Auto-iniciar monitoramento
        folder = self.config.monitored_folder
        if folder and Path(folder).is_dir() and self.config.get("auto_start_monitoring", True):
            self._start_monitoring(folder)
        elif not folder:
            # Se nenhuma pasta configurada, abre configurações após iniciar
            self.root.after(800, lambda: self.request("show_settings"))

        # Inicia polling da fila
        self.root.after(120, self._poll_queue)

    # Event loop
    def run(self) -> None:
        """Inicia o mainloop do tkinter (bloqueia até fechar)."""
        logger.info(f"FolderMonitor v{self.VERSION} iniciado.")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt recebido no mainloop")
            self._quit()
        finally:
            logger.info("root.mainloop retornou")

    def request(self, action: str, **kwargs) -> None:
        """
        Thread-safe: enfileira uma ação para execução no thread do tkinter.
        Pode ser chamado de qualquer thread.
        """
        logger.info(f"Request queued: {action} from {threading.current_thread().name}")
        self._ui_queue.put({"action": action, **kwargs})

    def _poll_queue(self) -> None:
        """Consome a fila de ações no thread principal."""
        try:
            while True:
                try:
                    msg = self._ui_queue.get_nowait()
                    self._dispatch(msg)
                except queue.Empty:
                    break
        except Exception as e:
            logger.error(f"Erro no poll da fila: {e}")
        finally:
            self.root.after(120, self._poll_queue)

    def _dispatch(self, msg: dict) -> None:
        """Mapeia ação para método."""
        action = msg.pop("action", None)
        handler_map = {
            "show_stats":     self._show_stats,
            "show_settings":  self._show_settings,
            "open_folder":    self._open_folder,
            "pause":          self._pause,
            "resume":         self._resume,
            "reset":          self._reset,
            "save_report":    self._save_report,
            "apply_settings": lambda: self._apply_settings(**msg),
            "quit":           self._quit,
        }
        fn = handler_map.get(action)
        logger.info(f"Dispatching action: {action} on {threading.current_thread().name}")
        if fn:
            try:
                fn()
            except Exception as e:
                logger.error(f"Erro ao executar ação '{action}': {e}")
        else:
            logger.warning(f"Ação desconhecida: {action}")

    # Monitoramento
    def _start_monitoring(self, folder: str) -> None:
        if self.monitor and self.monitor.is_running:
            self.monitor.stop()

        try:
            self.monitor = FolderMonitor(
                folder_path=folder,
                ignore_patterns=self.config.ignore_patterns,
                track_extensions=self.config.track_by_extension,
            )
            self.monitor.start()
            self.session_start = datetime.now()

            self.tray.set_state("active", f"FolderMonitor — {Path(folder).name}")
            if self.config.notifications_enabled:
                self.tray.notify(
                    f"Monitorando: {folder}",
                    "FolderMonitor iniciado ✅",
                )
            logger.info(f"Monitoramento iniciado: {folder}")
        except Exception as e:
            logger.error(f"Falha ao iniciar monitoramento: {e}")
            messagebox.showerror(
                "Erro",
                f"Não foi possível iniciar o monitoramento:\n{e}",
            )

    def _stop_monitoring(self) -> None:
        if self.monitor and self.monitor.is_running:
            self.monitor.stop()
            self.tray.set_state("paused", "FolderMonitor — Inativo")
            if self.config.notifications_enabled:
                self.tray.notify("Monitoramento encerrado.", "FolderMonitor")

    # Ações do menu
    def _show_stats(self) -> None:
        self._stats_win.open()

    def _show_settings(self) -> None:
        self._settings_win.open()

    def _open_folder(self) -> None:
        folder = self.config.monitored_folder
        if folder and Path(folder).is_dir():
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")
        else:
            messagebox.showwarning("Pasta não definida",
                                   "Nenhuma pasta monitorada configurada.")

    def _pause(self) -> None:
        if self.monitor and not self.monitor.is_paused:
            self.monitor.pause()
            self.tray.set_state("paused", "FolderMonitor — Pausado")
            if self.config.notifications_enabled:
                self.tray.notify("Monitoramento pausado ⏸", "FolderMonitor")

    def _resume(self) -> None:
        if self.monitor and self.monitor.is_paused:
            self.monitor.resume()
            folder_name = Path(self.config.monitored_folder).name if self.config.monitored_folder else ""
            self.tray.set_state("active", f"FolderMonitor — {folder_name}")
            if self.config.notifications_enabled:
                self.tray.notify("Monitoramento retomado ▶", "FolderMonitor")

    def _reset(self) -> None:
        if self.monitor:
            self.monitor.reset_stats()
        self.session_start = datetime.now()
        if self.config.notifications_enabled:
            self.tray.notify("Contadores zerados 🔄", "FolderMonitor")

    def _save_report(self) -> None:
        if not self.session_start:
            messagebox.showinfo("Sem dados", "Nenhuma sessão ativa para gerar relatório.")
            return

        stats  = self.get_stats()
        folder = self.config.monitored_folder
        path   = self.report_manager.save_report(stats, folder, self.session_start)

        if path:
            if self.config.notifications_enabled:
                self.tray.notify(f"Relatório salvo: {path.name}", "FolderMonitor 💾")
            # Salva no histórico também
            self.report_manager.save_session(stats, folder, self.session_start)

            if messagebox.askyesno(
                "Relatório salvo",
                f"Relatório salvo em:\n{path}\n\nDeseja abrir o arquivo?",
            ):
                os.startfile(str(path))
        else:
            messagebox.showerror("Erro", "Falha ao salvar o relatório.")

    def _apply_settings(self, **kwargs) -> None:
        """Aplica as configurações recebidas da janela de configurações."""
        old_folder = self.config.monitored_folder
        new_folder = kwargs.get("monitored_folder", "")

        # Atualiza config
        self.config.update(kwargs)

        # Se a pasta mudou, reinicia o monitoramento
        if new_folder and new_folder != old_folder:
            self._stop_monitoring()
            self._start_monitoring(new_folder)
        elif new_folder and self.monitor is None:
            self._start_monitoring(new_folder)

        logger.info("Configurações aplicadas.")

    # Encerramento
    def _quit(self) -> None:
        logger.info(f"Encerrando FolderMonitor... (thread={threading.current_thread().name})")

        # Salva relatório se configurado
        if self.config.save_report_on_exit and self.session_start:
            stats  = self.get_stats()
            folder = self.config.monitored_folder
            if stats.get("total", 0) > 0:
                self.report_manager.save_report(stats, folder, self.session_start)
                self.report_manager.save_session(stats, folder, self.session_start)

        # Para monitoramento
        self._stop_monitoring()

        # Para bandeja
        self.tray.stop()

        # Para tkinter
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    # Utilitários
    def get_stats(self) -> dict:
        """Retorna estatísticas atuais de forma segura."""
        if self.monitor:
            return self.monitor.stats
        return {
            "created": 0, "deleted": 0, "modified": 0,
            "renamed": 0, "total": 0, "by_extension": {},
        }