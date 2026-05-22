import logging
import threading
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class _EventHandler(FileSystemEventHandler):
    """
    Handler interno leve:
    - Lock granular por operação de escrita
    - Ignora diretórios (só conta arquivos)
    - Filtra padrões indesejados
    - Rastreia por extensão (opcional)
    """

    def __init__(
        self,
        callback: Optional[Callable[[str, str], None]] = None,
        ignore_patterns: Optional[list[str]] = None,
        track_extensions: bool = True,
    ) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._callback = callback
        self._ignore = [p.lower() for p in (ignore_patterns or [])]
        self._track_ext = track_extensions
        self._paused = False

        # Contadores principais
        self._counts: dict[str, int] = {
            "created":  0,
            "deleted":  0,
            "modified": 0,
            "renamed":  0,
        }
        # Contadores por extensão: {"ext": {"created": N, ...}}
        self._by_ext: dict[str, dict[str, int]] = {}

    # Filtragem
    def _should_ignore(self, path: str) -> bool:
        pl = path.lower()
        return any(pat in pl for pat in self._ignore)

    @staticmethod
    def _get_ext(path: str) -> str:
        ext = Path(path).suffix.lower()
        return ext if ext else "(sem ext)"

    # Registro de evento
    def _record(self, event_type: str, path: str) -> None:
        if self._paused or self._should_ignore(path):
            return

        ext = self._get_ext(path) if self._track_ext else None

        with self._lock:
            self._counts[event_type] += 1
            if ext is not None:
                bucket = self._by_ext.setdefault(
                    ext,
                    {"created": 0, "deleted": 0, "modified": 0, "renamed": 0},
                )
                bucket[event_type] += 1

        if self._callback:
            try:
                self._callback(event_type, path)
            except Exception:
                pass  # Nunca deixar callback quebrar o observer

    # Eventos watchdog
    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._record("created", event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._record("deleted", event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._record("modified", event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._record("renamed", event.src_path)

    # Estado e reset
    def pause(self)  -> None: self._paused = True
    def resume(self) -> None: self._paused = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    def reset(self) -> None:
        with self._lock:
            for k in self._counts:
                self._counts[k] = 0
            self._by_ext.clear()

    @property
    def stats(self) -> dict:
        with self._lock:
            c = dict(self._counts)
            c["total"] = sum(c.values())
            c["by_extension"] = {
                ext: dict(vals) for ext, vals in self._by_ext.items()
            }
        return c


# 
class FolderMonitor:
    """
    Fachada pública para o monitoramento.
    Gerencia ciclo de vida do Observer e expõe API limpa para o App.
    """

    def __init__(
        self,
        folder_path: str,
        callback: Optional[Callable[[str, str], None]] = None,
        ignore_patterns: Optional[list[str]] = None,
        track_extensions: bool = True,
    ) -> None:
        self._folder_path = folder_path
        self._callback = callback
        self._ignore = ignore_patterns or []
        self._track_ext = track_extensions

        self._observer: Optional[Observer] = None
        self._handler: Optional[_EventHandler] = None
        self._running = False

    # Controle do Observer
    def start(self) -> None:
        """Inicia o monitoramento (Observer roda em thread própria)."""
        if self._running:
            return

        folder = Path(self._folder_path)
        if not folder.is_dir():
            raise FileNotFoundError(
                f"Pasta não encontrada ou inválida: {self._folder_path}"
            )

        self._handler = _EventHandler(
            callback=self._callback,
            ignore_patterns=self._ignore,
            track_extensions=self._track_ext,
        )
        self._observer = Observer()
        self._observer.schedule(self._handler, str(folder), recursive=True)
        self._observer.start()
        self._running = True
        logger.info(f"Monitoramento iniciado: {self._folder_path}")

    def stop(self) -> None:
        """Para o monitoramento de forma segura."""
        if self._observer and self._running:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._running = False
            logger.info("Monitoramento encerrado.")

    def pause(self) -> None:
        if self._handler:
            self._handler.pause()
            logger.debug("Monitoramento pausado.")

    def resume(self) -> None:
        if self._handler:
            self._handler.resume()
            logger.debug("Monitoramento retomado.")

    def reset_stats(self) -> None:
        if self._handler:
            self._handler.reset()

    # Propriedades
    @property
    def stats(self) -> dict:
        if self._handler:
            return self._handler.stats
        return {"created": 0, "deleted": 0, "modified": 0,
                "renamed": 0, "total": 0, "by_extension": {}}

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return bool(self._handler and self._handler.is_paused)

    @property
    def folder_path(self) -> str:
        return self._folder_path

    @folder_path.setter
    def folder_path(self, path: str) -> None:
        was_running = self._running
        was_paused  = self.is_paused
        if was_running:
            self.stop()
        self._folder_path = path
        if was_running:
            self.start()
            if was_paused:
                self.pause()