# -*- coding: utf-8 -*-
import json
from pathlib import Path
import sys

def load_config() -> dict:
    """
    Loads config/config_default.json.
    Supports both script mode and PyInstaller EXE mode.
    """
    # When running as a frozen EXE
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).resolve().parent.parent

    cfg_path = base_dir / "config" / "config_default.json"

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    return cfg
