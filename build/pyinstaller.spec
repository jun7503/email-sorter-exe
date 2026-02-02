# PyInstaller spec for EmailSorter (windowed, onefile)

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# --- Paths (robust to CWD) ---
REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # '..' from build/
SRC_DIR = os.path.join(REPO_ROOT, 'src')
CONFIG_SRC = os.path.join(REPO_ROOT, 'config', 'config_default.json')

# --- Data files ---
# Copy config/config_default.json into the bundled app under "config/"
datas = [
    (CONFIG_SRC, 'config'),
]

# --- Hidden imports (packages that do dynamic imports) ---
hiddenimports = collect_submodules('extract_msg')

# --- Analysis ---
a = Analysis(
    ['src/app.py'],              # Path is relative to repo root at build time
    pathex=[SRC_DIR],            # Help resolver find your source package
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# --- Python bytecode archive ---
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- One-file, windowed EXE (no console) ---
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EmailSorter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                  # set True if you want UPX compression and it’s available
    upx_exclude=[],
    runtime_tmpdir=None,        # None => use default temp dir for onefile extraction
    console=False,              # windowed app (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,       # only relevant on macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None                   # set to e.g. os.path.join(REPO_ROOT, 'build', 'email_sorter.ico')
)
``
