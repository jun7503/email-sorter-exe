# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


def load_config() -> dict:
    """
    Load config/config_default.json.

    Works both when running from source (python src/run_email_sorter.py)
    and when running as a PyInstaller-frozen executable.
    """
    # Base directory: EXE dir when frozen; repo root when running from source.
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
    else:
        # this file lives at src/email_sorter/config_loader.py
        # repo root = src/.. (parent of src)
        base_dir = Path(__file__).resolve().parent.parent

    cfg_path = base_dir / "config" / "config_default.json"

    if not cfg_path.exists():
        # Provide a clear error with the path we attempted
        raise FileNotFoundError(
            f"Config file not found: {cfg_path}\n"
            f"Current base_dir: {base_dir}\n"
            f"Frozen: {getattr(sys, 'frozen', False)}"
        )

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    return cfg
