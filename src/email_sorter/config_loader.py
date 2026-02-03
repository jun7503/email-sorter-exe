# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


def _project_root_from_this_file() -> Path:
    """
    This file lives at: <repo>/src/email_sorter/config_loader.py
    parents[0] -> email_sorter
    parents[1] -> src
    parents[2] -> <repo root>   <-- we want this in dev
    """
    return Path(__file__).resolve().parents[2]


def _bundle_base_dir() -> Path:
    """
    Return the base directory for bundled resources when running as a frozen app.
    - In PyInstaller onefile, data is unpacked under sys._MEIPASS.
    - In PyInstaller onedir, data is next to the EXE (sys.executable.parent).
    """
    if hasattr(sys, "_MEIPASS"):
        # onefile
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # onedir fallback (and some other frozen modes)
    return Path(sys.executable).parent


def resource_path(relative_path: str) -> Path:
    """
    Resolve a resource path that works both in dev and frozen builds.
    """
    if getattr(sys, "frozen", False):
        base_dir = _bundle_base_dir()
    else:
        base_dir = _project_root_from_this_file()
    return base_dir / relative_path


def load_config() -> dict:
    """
    Load config/config_default.json, working in both dev and PyInstaller builds.
    """
    cfg_path = resource_path("config/config_default.json")

    if not cfg_path.exists():
        raise FileNotFoundError(
            "Config file not found: "
            f"{cfg_path}\n"
            f"Base dir used: {cfg_path.parent.parent}\n"
            f"Frozen: {getattr(sys, 'frozen', False)} "
            f"(MEIPASS: {getattr(sys, '_MEIPASS', None)})"
        )

    with cfg_path.open("r", encoding="utf-8") as f:
        return json.load(f)
