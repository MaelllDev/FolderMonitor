import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app import FolderMonitorApp

COLORS = {
    "bg":     "#0f172a",
    "card":   "#1e293b",
    "border": "#334155",
    "text":   "#f1f5f9",
    "muted":  "#94a3b8",
    "accent": "#0ea5e9",
    "danger": "#ef4444",
    "success":"#22c55e",
}


class SettingsWindow:
    """
    Janela de configurações — singleton por sessão.
    """

    def __init__(self, app: "FolderMonitorApp") -> None:
        self.app = app
        self._win: Optional[tk.Toplevel] = None
        self._vars: dict[str, tk.Variable] = {}

    def open(self) -> None:
        if self._win and tk.Toplevel.winfo_exists(self._win):
            self._win.lift()
            self._win.focus_force()
            return

        self._win = tk.Toplevel(self.app.root)
        self._win.title("⚙  Configurações — FolderMonitor")
        self._win.resizable(False, False)
        self._win.configure(bg=COLORS["bg"])
        self._win.protocol("WM_DELETE_WINDOW", self._on_cancel)

        w, h = 520, 560
        sw   = self._win.winfo_screenwidth()
        sh   = self._win.winfo_screenheight()
        self._win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._build_ui()
        self._load_current()
        self._win.lift()

    def _build_ui(self) -> None:
        win  = self._win
        bg   = COLORS["bg"]
        card = COLORS["card"]

        # Cabeçalho
        header = tk.Frame(win, bg=COLORS["accent"], pady=12)
        header.pack(fill="x")
        tk.Label(
            header,
            text="⚙   Configurações",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=COLORS["accent"],
        ).pack()

        # Notebook / Seções
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TNotebook",
            background=bg,
            borderwidth=0,
        )
        style.configure(
            "Dark.TNotebook.Tab",
            background=COLORS["card"],
            foreground=COLORS["muted"],
            padding=[12, 6],
            font=("Segoe UI", 9),
        )
        style.map(
            "Dark.TNotebook.Tab",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", "white")],
        )

        nb = ttk.Notebook(win, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True, padx=12, pady=10)

        # Tab: Monitoramento
        tab_mon = tk.Frame(nb, bg=bg)
        nb.add(tab_mon, text="  📁 Monitoramento  ")
        self._build_monitoring_tab(tab_mon)

        # Tab: Comportamento
        tab_beh = tk.Frame(nb, bg=bg)
        nb.add(tab_beh, text="  🔧 Comportamento  ")
        self._build_behavior_tab(tab_beh)

        # Tab: Filtros
        tab_flt = tk.Frame(nb, bg=bg)
        nb.add(tab_flt, text="  🚫 Filtros  ")
        self._build_filters_tab(tab_flt)

        # Botões
        btn_frame = tk.Frame(win, bg=bg, pady=12)
        btn_frame.pack(fill="x", padx=16)

        tk.Button(
            btn_frame,
            text="✕  Cancelar",
            command=self._on_cancel,
            bg=COLORS["border"],
            fg=COLORS["text"],
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=14, pady=7,
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            btn_frame,
            text="✔  Salvar",
            command=self._on_save,
            bg=COLORS["success"],
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=14, pady=7,
        ).pack(side="right")

    # Tab: Monitoramento
    def _build_monitoring_tab(self, parent: tk.Frame) -> None:
        bg   = COLORS["bg"]
        card = COLORS["card"]

        def section(text: str) -> tk.Frame:
            lbl = tk.Label(parent, text=text,
                           font=("Segoe UI", 8, "bold"),
                           fg=COLORS["muted"], bg=bg)
            lbl.pack(fill="x", padx=14, pady=(12, 2))
            f = tk.Frame(parent, bg=card, padx=12, pady=10)
            f.pack(fill="x", padx=12)
            return f

        # Pasta monitorada
        frm = section("PASTA MONITORADA")

        self._vars["folder"] = tk.StringVar()
        folder_row = tk.Frame(frm, bg=card)
        folder_row.pack(fill="x")

        entry = tk.Entry(
            folder_row,
            textvariable=self._vars["folder"],
            font=("Segoe UI", 9),
            bg=COLORS["border"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            bd=4,
        )
        entry.pack(side="left", fill="x", expand=True)

        tk.Button(
            folder_row,
            text="  📂  ",
            command=self._browse_folder,
            bg=COLORS["accent"],
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2",
        ).pack(side="left", padx=(6, 0))

        # Botão abrir pasta
        tk.Button(
            frm,
            text="↗  Abrir no Explorer",
            command=self._open_folder_in_explorer,
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            pady=2,
        ).pack(anchor="w", pady=(6, 0))

        # Opções de rastreamento
        frm2 = section("OPÇÕES")

        self._vars["track_extensions"] = tk.BooleanVar()
        self._check(frm2, "track_extensions",
                    "🔎  Rastrear eventos por extensão (.py, .json, ...)")

        self._vars["auto_start_monitoring"] = tk.BooleanVar()
        self._check(frm2, "auto_start_monitoring",
                    "▶  Iniciar monitoramento ao abrir o programa")

    # Tab: Comportamento
    def _build_behavior_tab(self, parent: tk.Frame) -> None:
        bg   = COLORS["bg"]
        card = COLORS["card"]

        def section(text: str) -> tk.Frame:
            tk.Label(parent, text=text, font=("Segoe UI", 8, "bold"),
                     fg=COLORS["muted"], bg=bg).pack(
                         fill="x", padx=14, pady=(12, 2))
            f = tk.Frame(parent, bg=card, padx=12, pady=10)
            f.pack(fill="x", padx=12)
            return f

        frm1 = section("SISTEMA")

        self._vars["start_with_windows"] = tk.BooleanVar()
        self._check(frm1, "start_with_windows",
                    "🚀  Iniciar automaticamente com o Windows")

        frm2 = section("RELATÓRIOS")

        self._vars["save_report_on_exit"] = tk.BooleanVar()
        self._check(frm2, "save_report_on_exit",
                    "💾  Salvar relatório ao fechar o programa")

        tk.Button(
            frm2,
            text="📂  Abrir pasta de relatórios",
            command=lambda: self.app.report_manager.open_report_folder(),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
        ).pack(anchor="w", pady=(6, 0))

        frm3 = section("NOTIFICAÇÕES")

        self._vars["notifications_enabled"] = tk.BooleanVar()
        self._check(frm3, "notifications_enabled",
                    "🔔  Notificações do Windows (iniciar/parar/relatório)")

        # Histórico
        frm4 = section("HISTÓRICO")
        tk.Label(
            frm4,
            text="Máximo de sessões no histórico:",
            font=("Segoe UI", 9),
            fg=COLORS["text"],
            bg=COLORS["card"],
        ).pack(anchor="w")

        self._vars["max_history_sessions"] = tk.IntVar(value=100)
        spin = tk.Spinbox(
            frm4,
            from_=10, to=1000, increment=10,
            textvariable=self._vars["max_history_sessions"],
            width=6,
            font=("Segoe UI", 9),
            bg=COLORS["border"],
            fg=COLORS["text"],
            relief="flat",
            bd=4,
        )
        spin.pack(anchor="w", pady=(4, 0))

    # Tab: Filtros
    def _build_filters_tab(self, parent: tk.Frame) -> None:
        bg   = COLORS["bg"]
        card = COLORS["card"]

        tk.Label(
            parent,
            text="PADRÕES IGNORADOS",
            font=("Segoe UI", 8, "bold"),
            fg=COLORS["muted"],
            bg=bg,
        ).pack(fill="x", padx=14, pady=(12, 2))

        frm = tk.Frame(parent, bg=card, padx=12, pady=10)
        frm.pack(fill="both", expand=True, padx=12)

        tk.Label(
            frm,
            text=(
                "Arquivos ou pastas que contiverem estes termos serão ignorados.\n"
                "Separe por vírgula ou nova linha."
            ),
            font=("Segoe UI", 8),
            fg=COLORS["muted"],
            bg=card,
            justify="left",
            wraplength=420,
        ).pack(anchor="w", pady=(0, 8))

        self._ignore_text = tk.Text(
            frm,
            height=8,
            font=("Consolas", 9),
            bg=COLORS["border"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            bd=6,
            wrap="word",
        )
        self._ignore_text.pack(fill="both", expand=True)

        # Presets rápidos
        tk.Label(
            frm,
            text="Presets rápidos:",
            font=("Segoe UI", 8),
            fg=COLORS["muted"],
            bg=card,
        ).pack(anchor="w", pady=(8, 2))

        presets_frame = tk.Frame(frm, bg=card)
        presets_frame.pack(anchor="w")

        presets = [
            ("Git",         ".git\n"),
            ("Python",      "__pycache__\n.pyc\n"),
            ("Node.js",     "node_modules\n"),
            ("Temporários", ".tmp\n~$\n.bak\n"),
        ]
        for label, text in presets:
            tk.Button(
                presets_frame,
                text=label,
                command=lambda t=text: self._add_preset(t),
                bg=COLORS["border"],
                fg=COLORS["text"],
                font=("Segoe UI", 8),
                relief="flat",
                cursor="hand2",
                padx=6, pady=3,
            ).pack(side="left", padx=(0, 4))

    def _add_preset(self, text: str) -> None:
        current = self._ignore_text.get("1.0", "end-1c").strip()
        if current and not current.endswith("\n"):
            current += "\n"
        self._ignore_text.delete("1.0", "end")
        self._ignore_text.insert("1.0", current + text)

    # Helpers
    def _check(self, parent: tk.Frame, var_name: str, label: str) -> None:
        """Cria um checkbox estilizado."""
        var = self._vars[var_name]
        cb = tk.Checkbutton(
            parent,
            text=label,
            variable=var,
            font=("Segoe UI", 9),
            fg=COLORS["text"],
            bg=COLORS["card"],
            selectcolor=COLORS["bg"],
            activeforeground=COLORS["text"],
            activebackground=COLORS["card"],
            cursor="hand2",
            anchor="w",
        )
        cb.pack(fill="x", pady=2)

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory(
            title="Selecionar pasta para monitorar",
            initialdir=self._vars["folder"].get() or None,
            mustexist=True,
        )
        if path:
            self._vars["folder"].set(path)

    def _open_folder_in_explorer(self) -> None:
        folder = self._vars["folder"].get()
        if folder and Path(folder).exists():
            import os
            os.startfile(folder)

    # Carga e salvamento
    def _load_current(self) -> None:
        cfg = self.app.config

        str_vars = {
            "folder": cfg.monitored_folder or "",
        }
        for k, v in str_vars.items():
            if k in self._vars:
                self._vars[k].set(v)

        bool_vars = {
            "track_extensions":      cfg.track_by_extension,
            "auto_start_monitoring": bool(cfg.get("auto_start_monitoring", True)),
            "start_with_windows":    cfg.is_startup_registered(),
            "save_report_on_exit":   cfg.save_report_on_exit,
            "notifications_enabled": cfg.notifications_enabled,
        }
        for k, v in bool_vars.items():
            if k in self._vars:
                self._vars[k].set(v)

        self._vars["max_history_sessions"].set(
            cfg.get("max_history_sessions", 100)
        )

        # Padrões ignorados
        patterns = cfg.ignore_patterns
        self._ignore_text.delete("1.0", "end")
        self._ignore_text.insert("1.0", "\n".join(patterns))

    def _on_save(self) -> None:
        folder = self._vars["folder"].get().strip()
        if folder and not Path(folder).is_dir():
            messagebox.showerror(
                "Pasta inválida",
                f"A pasta selecionada não existe:\n{folder}",
                parent=self._win,
            )
            return

        # Padrões ignorados
        raw     = self._ignore_text.get("1.0", "end-1c")
        patterns = [
            p.strip()
            for p in raw.replace(",", "\n").split("\n")
            if p.strip()
        ]

        new_cfg = {
            "monitored_folder":        folder,
            "track_by_extension":      self._vars["track_extensions"].get(),
            "auto_start_monitoring":   self._vars["auto_start_monitoring"].get(),
            "save_report_on_exit":     self._vars["save_report_on_exit"].get(),
            "notifications_enabled":   self._vars["notifications_enabled"].get(),
            "ignore_patterns":         patterns,
            "max_history_sessions":    self._vars["max_history_sessions"].get(),
        }

        # Autostart Windows
        if self._vars["start_with_windows"].get():
            self.app.config.set_startup_with_windows(True)
        else:
            self.app.config.set_startup_with_windows(False)

        self.app.request("apply_settings", **new_cfg)
        self._on_close()

    def _on_cancel(self) -> None:
        self._on_close()

    def _on_close(self) -> None:
        if self._win:
            self._win.destroy()
        self._win = None