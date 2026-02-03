# build/pyinstaller.spec

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# --- Robust path detection regardless of where pyinstaller is invoked ---
try:
    # Works when __file__ is defined (most local runs, many CI contexts)
    SPEC_DIR = Path(__file__).resolve().parent
except NameError:
    # Fallback: derive from current working directory if __file__ is not set
    SPEC_DIR = Path.cwd() / "build" if (Path.cwd() / "build" / "pyinstaller.spec").exists() else Path.cwd()

# In your repo the spec lives at <repo_root>/build/pyinstaller.spec
# If SPEC_DIR points to .../build, parent is the repo root.
REPO_ROOT = SPEC_DIR if SPEC_DIR.name.lower() != "build" else SPEC_DIR.parent
if not (REPO_ROOT / "src").exists():
    # Last-ditch fallback for the Actions double-folder checkout pattern
    # If we accidentally ended up at D:\a\repo instead of D:\a\repo\repo
    # and the inner folder exists, use it.
    inner = REPO_ROOT / REPO_ROOT.name
    if (inner / "src").exists():
        REPO_ROOT = inner

SRC_DIR = REPO_ROOT / "src"
CONFIG_FILE = REPO_ROOT / "config" / "config_default.json"

datas = [
    (str(CONFIG_FILE), "config"),
]

# Keep hidden imports from extract_msg, and also include all local .py modules in src
hiddenimports = set(collect_submodules("extract_msg"))

# Add every .py file (except app.py) in src as hidden imports (e.g., gui, utils, etc.)
for p in SRC_DIR.glob("*.py"):
    name = p.stem
    if name != "app":
        hiddenimports.add(name)

hiddenimports = list(hiddenimports)

a = Analysis(
    [str(SRC_DIR / "email_sorter" / "app.py")],  # ← MUST be the package path now
    pathex=[str(SRC_DIR), str(REPO_ROOT)],  # include both src and repo root
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="EmailSorter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,    # show a console window (useful for debugging)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
