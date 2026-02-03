# build/pyinstaller.spec

from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_all

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
    inner = REPO_ROOT / REPO_ROOT.name
    if (inner / "src").exists():
        REPO_ROOT = inner

SRC_DIR = REPO_ROOT / "src"
CONFIG_FILE = REPO_ROOT / "config" / "config_default.json"
HOOKS_DIR = REPO_ROOT / "hooks"   # <— NEW: where hook-email_sorter.py lives

# ✅ Add src/ to sys.path so collect_submodules("email_sorter") works at spec-parse time
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# === DEBUG INFO (keep for now; appears in Actions logs) ===
print(">> REPO_ROOT:", REPO_ROOT)
print(">> SRC_DIR:", SRC_DIR)
_collected_email_sorter = collect_submodules("email_sorter")
print(">> Collected submodules (email_sorter):")
for _m in sorted(_collected_email_sorter):
    print("   -", _m)
# === END DEBUG INFO ===

# ---- Data files bundled next to the exe (inside dist/EmailSorter/) ----
datas = [(str(CONFIG_FILE), "config")]
binaries = []
hiddenimports = set()

# 1) External package submodules (keep)
hiddenimports.update(collect_submodules("extract_msg"))

# 2) Collect *everything* from our package (code + data) — very robust
email_data, email_bins, email_hidden = collect_all("email_sorter")
datas += email_data
binaries += email_bins
hiddenimports.update(email_hidden)

# 3) Our package as discovered earlier
hiddenimports.update(_collected_email_sorter)

# 4) Optional: explicit names (belt-and-suspenders)
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

hiddenimports = list(hiddenimports)

# ⚠️ IMPORTANT: resolve imports ONLY from src/ to avoid path shadowing
a = Analysis(
    [str(SRC_DIR / "run_email_sorter.py")],   # entry launcher
    pathex=[str(SRC_DIR)],                    # ← ONLY src (remove repo root)
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(HOOKS_DIR)] if HOOKS_DIR.exists() else [],  # <— NEW
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
    console=False,    # <— Turn ON for one run to see logs; set False later
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
