# PyInstaller spec for EmailSorter (windowed, onefile)

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# --- Paths robust to CWD ---
# This spec lives in: <repo_root>/build/pyinstaller.spec
REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
CONFIG_FILE = os.path.join(REPO_ROOT, "config", "config_default.json")

# --- Data files to bundle ---
# Copy config/config_default.json into the bundle under a "config" directory
datas = [
    (CONFIG_FILE, "config"),
]

# --- Hidden imports (for modules that import dynamically) ---
hiddenimports = collect_submodules("extract_msg")

# --- Analysis ---
a = Analysis(
    ["src/app.py"],            # relative to repo root when pyinstaller runs
    pathex=[SRC_DIR],          # help resolver find your modules in src/
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},            # PyInstaller 6+ accepts hooksconfig
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# --- Python bytecode archive ---
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- One-file, windowed EXE ---
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],                        # exclude list for PKG (usually empty)
    name="EmailSorter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # set True if UPX is available and desired
    upx_exclude=[],
    runtime_tmpdir=None,       # default temp extraction dir for onefile
    console=False,             # windowed (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,      # macOS only
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None                  # e.g., os.path.join(REPO_ROOT, "build", "email_sorter.ico")
)
