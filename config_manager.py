import json
import logging
import os
import sys
import winreg
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Valores padrão
DEFAULTS: dict[str, Any] = {
    "monitored_folder":        "",
    "auto_start_monitoring":   True,
    "start_with_windows":      False,
    "save_report_on_exit":     True,
    "notifications_enabled":   True,
    "track_by_extension":      True,
    "ignore_patterns":         [".git", "__pycache__", ".tmp", "~$", ".DS_Store"],
    "max_history_sessions":    100,
    "theme":                   "dark",
    "language":                "pt-BR",
}

APP_NAME      = "FolderMonitor"
REGISTRY_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"


class ConfigManager:
    """
    Gerenciador de configurações persistentes.
    Thread-safe: usa gravação atômica via arquivo temporário.
    """

    def __init__(self) -> None:
        self.app_dir: Path = Path(os.getenv("APPDATA", "~")) / APP_NAME
        self.app_dir.mkdir(parents=True, exist_ok=True)

        self.config_file:  Path = self.app_dir / "config.json"
        self.reports_dir:  Path = self.app_dir / "reports"
        self.sessions_file: Path = self.app_dir / "sessions.json"
        self.log_file:     Path = self.app_dir / "app.log"

        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self._data: dict[str, Any] = DEFAULTS.copy()
        self._load()

    # Persistência
    def _load(self) -> None:
        if not self.config_file.exists():
            return
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Mescla com padrões para garantir novas chaves
            self._data.update({k: v for k, v in saved.items() if k in DEFAULTS})
        except Exception as e:
            logger.warning(f"Falha ao carregar configurações: {e}")

    def save(self) -> None:
        try:
            tmp = self.config_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            tmp.replace(self.config_file)  # Gravação atômica
        except Exception as e:
            logger.error(f"Falha ao salvar configurações: {e}")

    # Acesso genérico
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def update(self, data: dict[str, Any]) -> None:
        self._data.update(data)
        self.save()

    # Atalhos para propriedades frequentes
    @property
    def monitored_folder(self) -> str:
        return self._data["monitored_folder"]

    @monitored_folder.setter
    def monitored_folder(self, value: str) -> None:
        self.set("monitored_folder", value)

    @property
    def notifications_enabled(self) -> bool:
        return bool(self._data.get("notifications_enabled", True))

    @property
    def save_report_on_exit(self) -> bool:
        return bool(self._data.get("save_report_on_exit", True))

    @property
    def track_by_extension(self) -> bool:
        return bool(self._data.get("track_by_extension", True))

    @property
    def ignore_patterns(self) -> list[str]:
        return list(self._data.get("ignore_patterns", []))

    # Inicialização automática com o Windows
    def set_startup_with_windows(self, enable: bool) -> bool:
        """
        Adiciona ou remove o programa da chave de registro de inicialização.
        Retorna True em caso de sucesso.
        """
        try:
            exe_path = _get_exe_path()
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY,
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
            )
            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass  # Já não existia
            winreg.CloseKey(key)
            self.set("start_with_windows", enable)
            return True
        except Exception as e:
            logger.error(f"Falha ao configurar inicialização automática: {e}")
            return False

    def is_startup_registered(self) -> bool:
        """Verifica se o app está registrado para inicialização com o Windows."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY,
                0,
                winreg.KEY_QUERY_VALUE,
            )
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False


def _get_exe_path() -> str:
    """Retorna o caminho do executável atual (compatível com PyInstaller)."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return str(Path(sys.argv[0]).resolve())