# build/pyinstaller.spec

from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_all, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

# --- Robust path detection regardless of where pyinstaller is invoked ---
try:
    SPEC_DIR = Path(__file__).resolve().parent
except NameError:
    SPEC_DIR = Path.cwd() / "build" if (Path.cwd() / "build" / "pyinstaller.spec").exists() else Path.cwd()

REPO_ROOT = SPEC_DIR if SPEC_DIR.name.lower() != "build" else SPEC_DIR.parent
if not (REPO_ROOT / "src").exists():
    inner = REPO_ROOT / REPO_ROOT.name
    if (inner / "src").exists():
        REPO_ROOT = inner

SRC_DIR = REPO_ROOT / "src"
CONFIG_FILE = REPO_ROOT / "config" / "config_default.json"
HOOKS_DIR = REPO_ROOT / "hooks"   # optional; only used if exists

# Ensure src/ is importable at spec-parse time
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# === DEBUG INFO ===
print(">> REPO_ROOT:", REPO_ROOT)
print(">> SRC_DIR:", SRC_DIR)
_collected_email_sorter = collect_submodules("email_sorter")
print(">> Collected submodules (email_sorter):")
for _m in sorted(_collected_email_sorter):
    print("   -", _m)
# === END DEBUG INFO ===

# ---- Data files bundled next to the exe (inside dist/EmailSorter/) ----
datas = []
if CONFIG_FILE.exists():
    datas.append((str(CONFIG_FILE), "config"))

binaries = []
hiddenimports = set()

# 1) External package submodules
hiddenimports.update(collect_submodules("extract_msg"))
hiddenimports.update(["olefile", "chardet"])

# >>> ADD: RTF tokenizer used by extract_msg
try:
    hiddenimports.update(collect_submodules("rtf_tokenizer"))
except Exception:
    # ok if not installed yet; ensure it's in requirements.txt
    pass

# 2) Collect code+data from our package
email_data, email_bins, email_hidden = collect_all("email_sorter")
datas += email_data
binaries += email_bins
hiddenimports.update(email_hidden)

# 3) Our package as discovered earlier
hiddenimports.update(_collected_email_sorter)

# 4) Belt-and-suspenders explicit names
hiddenimports.update({
    "email_sorter",
    "email_sorter.app",
    "email_sorter.gui",
    "email_sorter.config_loader",
    "email_sorter.utils",
    "email_sorter.summary",
    "email_sorter.text_clean",
    "email_sorter.clustering",
    "email_sorter.dedup",
    "email_sorter.mail_parser",
    "email_sorter.excel_writer",
    "email_sorter.issue_milestone",
    "email_sorter.keys",
    "email_sorter.topic_map",
})

# 5) Include data files for extract_msg (defensive)
datas += collect_data_files("extract_msg")

# >>> ADD: Make sure PySide6 plugins/resources are collected (GUI reliability)
try:
    pyside_data, pyside_bins, pyside_hidden = collect_all("PySide6")
    datas += pyside_data
    binaries += pyside_bins
    hiddenimports.update(pyside_hidden)
except Exception:
    print(">> Warning: PySide6 not found at spec parse time; skipping collect_all(PySide6)")

hiddenimports = list(hiddenimports)

a = Analysis(
    [str(SRC_DIR / "run_email_sorter.py")],    # entry launcher (your file)
    pathex=[str(SRC_DIR)],                     # ONLY src
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(HOOKS_DIR)] if HOOKS_DIR.exists() else [],
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
    console=True,     # keep True for first test; set False after verifying
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="EmailSorter"
)
