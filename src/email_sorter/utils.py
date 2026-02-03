# -*- coding: utf-8 -*-
import os
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
