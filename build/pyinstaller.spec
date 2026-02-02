# PyInstaller spec for EmailSorter (windowed, onefile)

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# --- Paths robust to PyInstaller's execution model ---
# PyInstaller runs with CWD = directory containing this spec file.
SPEC_DIR = Path.cwd()                 # .../<repo_root>/build
REPO_ROOT = SPEC_DIR.parent           # .../<repo_root>
SRC_DIR = REPO_ROOT / "src"
CONFIG_FILE = REPO_ROOT / "config" / "config_default.json"

# --- Data files to bundle ---
# Copy config/config_default.json into the bundle under a "config" directory
datas = [
    (str(CONFIG_FILE), "config"),
]

# --- Hidden imports (for modules that import dynamically) ---
hiddenimports = collect_submodules("extract_msg")

# --- Analysis ---
a = Analysis(
    # Always pass absolute or spec-relative paths as strings
    [str(SRC_DIR / "app.py")],        # entry point
    pathex=[str(SRC_DIR)],            # help resolver find your modules in src/
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},                   # PyInstaller 6+ supports hooksconfig
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
    [],                                # exclude list for PKG (usually empty)
    name="EmailSorter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                         # set True if UPX is available and desired
    upx_exclude=[],
    runtime_tmpdir=None,               # default temp extraction dir for onefile
    console=False,                     # windowed (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,              # macOS only
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None                          # e.g., str(REPO_ROOT / "build" / "email_sorter.ico")
)
