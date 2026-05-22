# main.spec — Configuração do PyInstaller para FolderMonitor
# Gera um .exe único, sem console, com ícone personalizado.
#
# Uso:
#   pyinstaller main.spec
#
# O executável estará em: dist\FolderMonitor.exe

import sys
from pathlib import Path

block_cipher = None

# Coleta todos os dados do customtkinter (temas, imagens, etc.)
from PyInstaller.utils.hooks import collect_all, collect_data_files

ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=ctk_binaries,
    datas=[
        # Inclui assets do customtkinter
        *ctk_datas,
    ],
    hiddenimports=[
        "pystray._win32",
        "watchdog.observers.winapi",
        "PIL._imaging",
        "PIL.Image",
        "PIL.ImageDraw",
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        *ctk_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "IPython",
        "jupyter",
        "notebook",
        "test",
        "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="FolderMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,               # Comprime o exe (requer UPX instalado)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # SEM janela de console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico",        # Ícone do .exe (gerado pelo generate_icon.py)
    version_file=None,
    uac_admin=False,
)
