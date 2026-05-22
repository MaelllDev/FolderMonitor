import tkinter as tk
from datetime import datetime
from typing import TYPE_CHECKING, Optional

try:
    import customtkinter as ctk
    CTK = True
except ImportError:
    import tkinter.ttk as ttk
    CTK = False

if TYPE_CHECKING:
    from app import FolderMonitorApp

# Paleta de cores
COLORS = {
    "bg":       "#0f172a",
    "card":     "#1e293b",
    "border":   "#334155",
    "text":     "#f1f5f9",
    "muted":    "#94a3b8",
    "created":  "#22c55e",
    "deleted":  "#ef4444",
    "modified": "#3b82f6",
    "renamed":  "#f59e0b",
    "total":    "#a78bfa",
    "header":   "#0ea5e9",
}

REFRESH_MS = 1000  # Atualiza a cada 1 segundo


class StatsWindow:
    """
    Janela de estatísticas — singleton por sessão do app.
    Fecha e recria a cada chamada se já existia.
    """

    def __init__(self, app: "FolderMonitorApp") -> None:
        self.app = app
        self._win: Optional[tk.Toplevel] = None
        self._after_id: Optional[str]  = None
        self._labels: dict[str, tk.StringVar] = {}
        self._ext_frame = None
        self._session_start: Optional[datetime] = None

    def open(self) -> None:
        if self._win and tk.Toplevel.winfo_exists(self._win):
            self._win.lift()
            self._win.focus_force()
            return

        self._session_start = self.app.session_start

        if CTK:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self._win = ctk.CTkToplevel(self.app.root)
        else:
            self._win = tk.Toplevel(self.app.root)

        self._win.title("📊 Estatísticas — FolderMonitor")
        self._win.resizable(False, False)
        self._win.configure(bg=COLORS["bg"])
        self._win.protocol("WM_DELETE_WINDOW", self._on_close)

        # Centraliza na tela
        w, h = 480, 620
        sw   = self._win.winfo_screenwidth()
        sh   = self._win.winfo_screenheight()
        x    = (sw - w) // 2
        y    = (sh - h) // 2
        self._win.geometry(f"{w}x{h}+{x}+{y}")

        self._build_ui()
        self._update()
        self._win.lift()

    def _build_ui(self) -> None:
        win = self._win
        bg  = COLORS["bg"]
        card = COLORS["card"]

        # Cabeçalho
        header = tk.Frame(win, bg=COLORS["header"], pady=14)
        header.pack(fill="x")

        tk.Label(
            header,
            text="📊  Estatísticas em Tempo Real",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=COLORS["header"],
        ).pack()

        # Informações da sessão
        info_frame = tk.Frame(win, bg=card, padx=16, pady=10)
        info_frame.pack(fill="x", padx=12, pady=(10, 0))

        folder = self.app.config.monitored_folder or "(não definida)"
        if len(folder) > 50:
            folder = "…" + folder[-47:]

        tk.Label(
            info_frame,
            text=f"📁  {folder}",
            font=("Segoe UI", 9),
            fg=COLORS["muted"],
            bg=card,
            anchor="w",
        ).pack(fill="x")

        self._labels["session"] = tk.StringVar(value="⏱  Calculando...")
        tk.Label(
            info_frame,
            textvariable=self._labels["session"],
            font=("Segoe UI", 9),
            fg=COLORS["muted"],
            bg=card,
            anchor="w",
        ).pack(fill="x")

        self._labels["status"] = tk.StringVar(value="● Ativo")
        tk.Label(
            info_frame,
            textvariable=self._labels["status"],
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["created"],
            bg=card,
            anchor="w",
        ).pack(fill="x")

        # Contadores principais
        counts_outer = tk.Frame(win, bg=bg, padx=12, pady=8)
        counts_outer.pack(fill="x")

        tk.Label(
            counts_outer,
            text="EVENTOS DA SESSÃO",
            font=("Segoe UI", 8, "bold"),
            fg=COLORS["muted"],
            bg=bg,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        counters_frame = tk.Frame(counts_outer, bg=bg)
        counters_frame.pack(fill="x")

        event_defs = [
            ("created",  "✅  Criados",      COLORS["created"]),
            ("deleted",  "🗑   Removidos",    COLORS["deleted"]),
            ("modified", "✏   Modificados",  COLORS["modified"]),
            ("renamed",  "🔄  Renomeados",    COLORS["renamed"]),
        ]

        for i, (key, label, color) in enumerate(event_defs):
            row = tk.Frame(counters_frame, bg=card, pady=8, padx=12)
            row.grid(row=i // 2, column=i % 2, padx=4, pady=3, sticky="nsew")
            counters_frame.columnconfigure(i % 2, weight=1)

            tk.Label(row, text=label, font=("Segoe UI", 9),
                     fg=COLORS["muted"], bg=card, anchor="w").pack(anchor="w")

            var = tk.StringVar(value="0")
            self._labels[key] = var
            tk.Label(row, textvariable=var, font=("Segoe UI", 22, "bold"),
                     fg=color, bg=card, anchor="w").pack(anchor="w")

        # Total
        total_frame = tk.Frame(win, bg=card, padx=16, pady=10)
        total_frame.pack(fill="x", padx=12, pady=(4, 0))

        tk.Label(
            total_frame,
            text="TOTAL DE EVENTOS",
            font=("Segoe UI", 8, "bold"),
            fg=COLORS["muted"],
            bg=card,
        ).pack(side="left")

        var = tk.StringVar(value="0")
        self._labels["total"] = var
        tk.Label(
            total_frame,
            textvariable=var,
            font=("Segoe UI", 22, "bold"),
            fg=COLORS["total"],
            bg=card,
        ).pack(side="right")

        # Por extensão
        ext_outer = tk.Frame(win, bg=bg, padx=12, pady=8)
        ext_outer.pack(fill="both", expand=True)

        tk.Label(
            ext_outer,
            text="POR EXTENSÃO",
            font=("Segoe UI", 8, "bold"),
            fg=COLORS["muted"],
            bg=bg,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        canvas   = tk.Canvas(ext_outer, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(ext_outer, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._ext_canvas   = canvas
        self._ext_inner    = tk.Frame(canvas, bg=bg)
        self._ext_canvas_id = canvas.create_window(
            (0, 0), window=self._ext_inner, anchor="nw"
        )
        self._ext_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(
                self._ext_canvas_id, width=e.width
            )
        )

        # Botões inferiores
        btn_frame = tk.Frame(win, bg=bg, pady=10)
        btn_frame.pack(fill="x", padx=12)

        btn_cfg = [
            ("💾  Salvar Relatório",  self._save,  COLORS["modified"]),
            ("🔄  Resetar",           self._reset, COLORS["renamed"]),
        ]
        for text, cmd, color in btn_cfg:
            btn = tk.Button(
                btn_frame,
                text=text,
                command=cmd,
                bg=color,
                fg="white",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                cursor="hand2",
                pady=6,
                padx=10,
            )
            btn.pack(side="left", padx=(0, 8))

    def _update_ext_list(self, by_ext: dict) -> None:
        """Reconstrói a lista de extensões."""
        for widget in self._ext_inner.winfo_children():
            widget.destroy()

        if not by_ext:
            tk.Label(
                self._ext_inner,
                text="Nenhuma extensão rastreada ainda.",
                font=("Segoe UI", 9),
                fg=COLORS["muted"],
                bg=COLORS["bg"],
            ).pack(anchor="w")
            return

        sorted_exts = sorted(
            by_ext.items(),
            key=lambda kv: sum(kv[1].values()),
            reverse=True,
        )[:25]

        max_total = sum(sum(v.values()) for _, v in sorted_exts) or 1

        for ext, ev in sorted_exts:
            total_ext = sum(ev.values())
            row = tk.Frame(self._ext_inner, bg=COLORS["card"], pady=4, padx=10)
            row.pack(fill="x", pady=2)

            tk.Label(
                row,
                text=ext,
                font=("Consolas", 9, "bold"),
                fg=COLORS["text"],
                bg=COLORS["card"],
                width=14,
                anchor="w",
            ).pack(side="left")

            # Mini barra de progresso
            bar_w = 120
            bar_h = 8
            fill_w = max(4, int(bar_w * total_ext / max_total))
            c = tk.Canvas(row, width=bar_w, height=bar_h,
                          bg=COLORS["border"], highlightthickness=0,
                          relief="flat")
            c.pack(side="left", padx=6)
            c.create_rectangle(0, 0, fill_w, bar_h,
                                fill=COLORS["modified"], width=0)

            tk.Label(
                row,
                text=str(total_ext),
                font=("Segoe UI", 9, "bold"),
                fg=COLORS["modified"],
                bg=COLORS["card"],
                width=5,
            ).pack(side="left")

    def _update(self) -> None:
        if not (self._win and tk.Toplevel.winfo_exists(self._win)):
            return

        stats = self.app.get_stats()

        # Contadores
        for key in ("created", "deleted", "modified", "renamed", "total"):
            if key in self._labels:
                self._labels[key].set(str(stats.get(key, 0)))

        # Duração da sessão
        if self.app.session_start:
            from datetime import datetime
            elapsed = (datetime.now() - self.app.session_start).total_seconds()
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            s = int(elapsed % 60)
            dur_str = f"{h:02d}:{m:02d}:{s:02d}"
            self._labels["session"].set(f"⏱  Duração: {dur_str}")

        # Status
        if self.app.monitor and self.app.monitor.is_paused:
            self._labels["status"].set("⏸  Pausado")
        elif self.app.monitor and self.app.monitor.is_running:
            self._labels["status"].set("● Monitorando")
        else:
            self._labels["status"].set("◼  Inativo")

        # Extensões
        self._update_ext_list(stats.get("by_extension", {}))

        self._after_id = self._win.after(REFRESH_MS, self._update)

    def _save(self) -> None:
        self.app.request("save_report")

    def _reset(self) -> None:
        self.app.request("reset")

    def _on_close(self) -> None:
        if self._after_id and self._win:
            try:
                self._win.after_cancel(self._after_id)
            except Exception:
                pass
        if self._win:
            self._win.destroy()
        self._win = None