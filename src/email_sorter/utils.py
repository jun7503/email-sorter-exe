# -*- coding: utf-8 -*-
import os
import sys
import hashlib
from pathlib import Path

def ensure_dirs(paths):
    """Create one or more directories safely (no error if they already exist)."""
    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

def safe_sha256(data: bytes) -> str:
    """Compute a SHA‑256 hash, safely handling None as empty bytes."""
    h = hashlib.sha256()
    h.update(data or b"")
    return h.hexdigest()

def pretty_exc(e: Exception) -> str:
    """Return a concise string representation of an exception."""
    return f"{type(e).__name__}: {e}"

# -----------------------------
# New: resource path utilities
# -----------------------------

def _project_root_from_this_file() -> Path:
    """
    For this file located at: <repo>/src/email_sorter/utils.py
    parents[0] -> email_sorter
    parents[1] -> src
    parents[2] -> <repo root>   <-- we want this
    """
    return Path(__file__).resolve().parents[2]

def resource_path(relative_path: str) -> Path:
    """
    Returns an absolute Path to a bundled/static resource (config, templates, etc.)
    - In PyInstaller onefile/onedir, resolves into the _MEIPASS unpack folder.
    - In development, resolves relative to the repository root.
    """
    if hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = _project_root_from_this_file()
    return base / relative_path

def is_frozen() -> bool:
    """True if running as a PyInstaller-frozen executable."""
    return bool(getattr(sys, "frozen", False))
``
