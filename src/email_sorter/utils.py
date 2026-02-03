# -*- coding: utf-8 -*-
import os
import hashlib
from pathlib import Path

def ensure_dirs(paths):
    """Create directories safely."""
    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

def safe_sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data or b"")
    return h.hexdigest()

def pretty_exc(e: Exception) -> str:
    return f"{type(e).__name__}: {e}"
