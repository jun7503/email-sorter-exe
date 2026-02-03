# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QFileDialog,
    QHBoxLayout, QTextEdit
)
from PySide6.QtCore import Qt

# 🔁 Use relative imports inside the package
from .mail_parser import parse_email_file  # ← change to .email_parser if your file is email_parser.py
from .text_clean import clean_body_for_semantics, canonical_subject, sender_domain
from .keys import message_key, thread_key, update_group_key, content_hash
from .dedup import SimilarityDecider
from .excel_writer import ExcelStore
from .summary import rebuild_summary
from .topic_map import TopicMap
from .clustering import DomainClusterer
from .issue_milestone import extract_issue_milestone
from .version import __version__


class EmailSorterWindow(QWidget):
    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle(f"📬 EmailSorter v{__version__}")
        self.setMinimumSize(720, 520)
        self.setAcceptDrops(True)

        self.sim = SimilarityDecider(cfg)
        self.clusterer = DomainClusterer(cfg)
        self.excel = None
        self.index_keys: set[str] = set()
        self.topic_map = TopicMap()

        self._build_ui()
        self._choose_excel_path()   # ← NOW VALID – method exists

    # ------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------
    def _build_ui(self):
        v = QVBoxLayout(self)

        title = QLabel("Drag & drop .eml / .msg files here")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        v.addWidget(title)

        self.path_label = QLabel("Excel: (not chosen)")
        v.addWidget(self.path_label)

        row = QHBoxLayout()
        # Add more UI elements here (buttons, progress bar…)
        # Example:
        # self.btn_run = QPushButton("Run")
        # row.addWidget(self.btn_run)
        v.addLayout(row)

    # ------------------------------------------------------------
    # Excel output path selection
    # ------------------------------------------------------------
    def _choose_excel_path(self):
        """
        Ask the user where to save the Excel output file.
        Works in both config modes.
        """

        mode = (self.cfg.get("excel_path_mode") or "").lower()

        # Ask user every time
        if mode == "ask_each_time":
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Choose Excel Output File",
                "EmailSorter_Output.xlsx",
                "Excel Files (*.xlsx)",
            )

            if not path:
                self.excel_path = None
                self.path_label.setText("Excel: (not chosen)")
                return

            self.excel_path = path
            self.path_label.setText(f"Excel: {path}")
            return

        # Fixed output path mode
        if mode == "fixed_path":
            fixed = self.cfg.get("excel_output_path")

            if fixed:
                self.excel_path = fixed
                self.path_label.setText(f"Excel: {fixed}")
                return

            self.excel_path = None
            self.path_label.setText("Excel: (fixed path missing)")
            return

        # Default fallback
        self.excel_path = None
        self.path_label.setText("Excel: (not chosen)")
