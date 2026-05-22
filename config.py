# config.py
import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "monitored_folder": "",
    "auto_start": False,
    "start_with_windows": False,
    "save_on_exit": True,
    "notification_on_start": True,
    "notification_on_stop": True,
    "theme": "dark",
    "language": "pt-BR",
    "max_history_sessions": 50,
    "ignore_patterns": [".git", "__pycache__", ".tmp", "~"]
}


CONFIG_PATH = Path(os.path.expanduser("~")) / ".adwa_config.json"


def load_config(path: Path = None):
    p = path or CONFIG_PATH
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if isinstance(cfg, dict):
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(cfg)
                    return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict, path: Path = None):
    p = path or CONFIG_PATH
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False
