import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Divisor visual para relatórios
_DIVIDER = "=" * 50


def _fmt_duration(seconds: float) -> str:
    """Formata segundos em '2h 14m 35s' ou '45m 12s'."""
    td = timedelta(seconds=int(seconds))
    h  = td.seconds // 3600
    m  = (td.seconds % 3600) // 60
    s  = td.seconds % 60
    if td.days:
        h += td.days * 24
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


class ReportManager:
    """
    Responsável por:
    - Gerar relatórios em .txt
    - Salvar histórico de sessões em sessions.json
    - Carregar histórico para exibição
    """

    def __init__(self, config: "ConfigManager") -> None:
        self.config = config

    # Geração de texto
    def build_report_text(
        self,
        stats: dict,
        folder: str,
        session_start: datetime,
        session_end: datetime | None = None,
    ) -> str:
        """Constrói o texto completo do relatório."""
        now      = session_end or datetime.now()
        duration = (now - session_start).total_seconds()

        lines = [
            _DIVIDER,
            "  FOLDER MONITOR — RELATÓRIO DE SESSÃO",
            _DIVIDER,
            f"  Data              : {now.strftime('%d/%m/%Y %H:%M:%S')}",
            f"  Pasta monitorada  : {folder or '(não definida)'}",
            f"  Duração da sessão : {_fmt_duration(duration)}",
            _DIVIDER,
            "  EVENTOS DETECTADOS",
            _DIVIDER,
            f"  ✅ Arquivos criados    : {stats.get('created',  0):>6}",
            f"  🗑  Arquivos removidos  : {stats.get('deleted',  0):>6}",
            f"  ✏  Arquivos modificados: {stats.get('modified', 0):>6}",
            f"  🔄 Arquivos renomeados : {stats.get('renamed',  0):>6}",
            "  " + "─" * 34,
            f"  📊 TOTAL DE EVENTOS    : {stats.get('total', 0):>6}",
            _DIVIDER,
        ]

        by_ext: dict = stats.get("by_extension", {})
        if by_ext:
            lines.append("  POR EXTENSÃO")
            lines.append(_DIVIDER)

            # Ordena por total decrescente
            sorted_exts = sorted(
                by_ext.items(),
                key=lambda kv: sum(kv[1].values()),
                reverse=True,
            )
            for ext, ev in sorted_exts[:30]:  # Limita a 30 extensões
                total_ext = sum(ev.values())
                parts = []
                for k, label in [
                    ("created", "cri"),
                    ("deleted", "rem"),
                    ("modified", "mod"),
                    ("renamed", "ren"),
                ]:
                    if ev.get(k, 0):
                        parts.append(f"{label}:{ev[k]}")
                detail = "  ".join(parts)
                lines.append(
                    f"  {ext:<16} {total_ext:>5}  ({detail})"
                )
            lines.append(_DIVIDER)

        lines.append("  Gerado por FolderMonitor")
        lines.append(_DIVIDER)
        lines.append("")

        return "\n".join(lines)

    # Salvamento
    def save_report(
        self,
        stats: dict,
        folder: str,
        session_start: datetime,
        session_end: datetime | None = None,
    ) -> Path | None:
        """
        Salva o relatório em disco.
        Retorna o caminho do arquivo criado, ou None em caso de erro.
        """
        try:
            now      = session_end or datetime.now()
            filename = f"relatorio_{now.strftime('%Y%m%d_%H%M%S')}.txt"
            dest     = self.config.reports_dir / filename

            text = self.build_report_text(stats, folder, session_start, now)
            dest.write_text(text, encoding="utf-8")

            logger.info(f"Relatório salvo em: {dest}")
            return dest
        except Exception as e:
            logger.error(f"Erro ao salvar relatório: {e}")
            return None

    def open_report_folder(self) -> None:
        """Abre a pasta de relatórios no Explorer."""
        try:
            os.startfile(str(self.config.reports_dir))
        except Exception as e:
            logger.warning(f"Não foi possível abrir pasta de relatórios: {e}")

    # Histórico de sessões
    def save_session(
        self,
        stats: dict,
        folder: str,
        session_start: datetime,
        session_end: datetime | None = None,
    ) -> None:
        """Persiste um resumo da sessão no arquivo de histórico."""
        try:
            now      = session_end or datetime.now()
            duration = (now - session_start).total_seconds()

            entry = {
                "date":     now.strftime("%d/%m/%Y %H:%M:%S"),
                "folder":   folder,
                "duration": int(duration),
                "created":  stats.get("created",  0),
                "deleted":  stats.get("deleted",  0),
                "modified": stats.get("modified", 0),
                "renamed":  stats.get("renamed",  0),
                "total":    stats.get("total",    0),
            }

            sessions = self._load_sessions()
            sessions.insert(0, entry)  # Mais recente primeiro

            max_s = self.config.get("max_history_sessions", 100)
            sessions = sessions[:max_s]

            path = self.config.sessions_file
            tmp  = path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(sessions, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.replace(path)
            logger.debug("Histórico de sessões atualizado.")
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")

    def _load_sessions(self) -> list[dict]:
        path = self.config.sessions_file
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def get_session_history(self) -> list[dict]:
        """Retorna lista de sessões salvas (mais recente primeiro)."""
        return self._load_sessions()

    def get_lifetime_stats(self) -> dict:
        """Soma acumulada de todas as sessões salvas."""
        sessions = self._load_sessions()
        totals = {"created": 0, "deleted": 0, "modified": 0,
                  "renamed": 0, "total": 0, "sessions": len(sessions)}
        for s in sessions:
            for k in ("created", "deleted", "modified", "renamed", "total"):
                totals[k] += s.get(k, 0)
        return totals