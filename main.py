import logging
import sys
import threading
import traceback
import tkinter as tk
from tkinter import messagebox
from pathlib import Path


def _setup_logging(log_file: Path) -> None:
    """Configura logging para arquivo + console (apenas em modo dev)."""
    handlers: list[logging.Handler] = [
        logging.FileHandler(log_file, encoding="utf-8", mode="a"),
    ]
    # Em modo dev (não congelado), também loga no console
    if not getattr(sys, "frozen", False):
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def _handle_exception(exc_type, exc_value, exc_tb) -> None:
    """Handler global para exceções não capturadas."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.critical(f"Exceção não tratada:\n{tb_str}")

    try:
        messagebox.showerror(
            "FolderMonitor — Erro Crítico",
            f"Ocorreu um erro inesperado:\n\n{exc_value}\n\n"
            "Veja o arquivo app.log para detalhes.",
        )
    except Exception:
        pass


def main() -> None:
    # Importa aqui para garantir que logging esteja configurado antes
    from config_manager import ConfigManager
    from app import FolderMonitorApp

    # Config básica para obter o diretório de log antes do app iniciar
    _cfg_temp = ConfigManager()
    _setup_logging(_cfg_temp.log_file)

    # Handler global de exceções
    sys.excepthook = _handle_exception

    if hasattr(threading, 'excepthook'):
        def _thread_exception_handler(args):
            logging.getLogger('threading').error(
                'Exceção não tratada na thread %s',
                args.thread.name,
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )
        threading.excepthook = _thread_exception_handler

    logger = logging.getLogger("main")
    logger.info("=" * 60)
    logger.info("FolderMonitor iniciando...")
    logger.info("=" * 60)

    try:
        app = FolderMonitorApp()
        app.run()
    except Exception as e:
        logger.critical(f"Falha crítica na inicialização: {e}", exc_info=True)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "FolderMonitor — Erro Fatal",
                f"O aplicativo falhou ao iniciar:\n\n{e}",
            )
            root.destroy()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()