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

# --- Collect hidden imports ---
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = set()

# 외부 패키지 서브모듈 수집 (기존 유지)
hiddenimports.update(collect_submodules("extract_msg"))

# 우리 패키지 전체(자동 수집)
hiddenimports.update(collect_submodules("email_sorter"))

# 안전을 위해 '정확한 이름'도 직접 명시 (반드시 포함되게)
hiddenimports.update({
    "email_sorter",
    "email_sorter.gui",
    "email_sorter.config_loader",
    "email_sorter.utils",
    "email_sorter.summary",
    "email_sorter.text_clean",
    "email_sorter.clustering",
    "email_sorter.dedup",
    "email_sorter.email_parser",
    "email_sorter.excel_writer",
    "email_sorter.issue_milestone",
    "email_sorter.keys",
    "email_sorter.topic_map",
})

hiddenimports = list(hiddenimports)

a = Analysis(
    [str(SRC_DIR / "run_email_sorter.py")],   # ← use the launcher
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
