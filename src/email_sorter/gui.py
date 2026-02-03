# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QFileDialog,
    QHBoxLayout, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt

# 🔁 Use relative imports inside the package
from .mail_parser import parse_email_file
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
    """
    Main UI window for EmailSorter application.
    """

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle(f"📬 EmailSorter v{__version__}")
        self.setMinimumSize(720, 520)
        self.setAcceptDrops(True)

        # Internal state
        self.sim = SimilarityDecider(cfg)
        self.clusterer = DomainClusterer(cfg)
        self.index_keys: set[str] = set()
        self.topic_map = TopicMap()
        self.processed_items = []    # fill this after processing
        self.excel_path: str | None = None

        # Build UI (buttons, labels)
        self._build_ui()

        # Choose Excel output location at startup (depending on config)
        self._choose_excel_path()

    # ------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------
    def _build_ui(self):
        v = QVBoxLayout(self)

        title = QLabel("Drag & drop .eml / .msg files here")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        v.addWidget(title)

        # Path display
        self.path_label = QLabel("Excel: (not chosen)")
        v.addWidget(self.path_label)

        row = QHBoxLayout()

        # Change Excel Path button
        self.btn_change_path = QPushButton("Change Excel Path")
        self.btn_change_path.clicked.connect(self._choose_excel_path)
        row.addWidget(self.btn_change_path)

        # Save Excel button
        self.btn_save_excel = QPushButton("Save Excel")
        self.btn_save_excel.clicked.connect(self._on_save_excel_clicked)
        row.addWidget(self.btn_save_excel)

        v.addLayout(row)

        # Progress bar (indeterminate mode)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        v.addWidget(self.progress)

    # ------------------------------------------------------------
    # Excel output path selection
    # ------------------------------------------------------------
    def _choose_excel_path(self):
        """
        Ask the user where to save the Excel output file.
        Works in both config modes:
          - ask_each_time
          - fixed_path
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

        # Fixed path mode
        if mode == "fixed_path":
            fixed = (self.cfg.get("excel_output_path") or "").strip()
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

    # ------------------------------------------------------------
    # Save Excel Handler
    # ------------------------------------------------------------
    def _on_save_excel_clicked(self):
        """
        Save the Excel file using ExcelStore.
        If the path is missing and config says ask_each_time,
        prompt the user again.
        """
        try:
            mode = (self.cfg.get("excel_path_mode") or "").lower()

            # Ask user again if needed
            if mode == "ask_each_time":
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Excel As...",
                    self.excel_path or "EmailSorter_Output.xlsx",
                    "Excel Files (*.xlsx)",
                )
                if not path:
                    return
                self.excel_path = path

            # If no path yet → choose one
            if not self.excel_path:
                self._choose_excel_path()
                if not self.excel_path:
                    return

            # Ensure folder exists
            p = Path(self.excel_path)
            p.parent.mkdir(parents=True, exist_ok=True)

            # Show progress
            self.progress.setVisible(True)
            self.btn_save_excel.setEnabled(False)

            # Save the file
            self._save_excel_to(self.excel_path)

            self.path_label.setText(f"Excel: {self.excel_path}")
            QMessageBox.information(
                self, "Success",
                f"Excel saved successfully:\n{self.excel_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

        finally:
            self.progress.setVisible(False)
            self.btn_save_excel.setEnabled(True)

    # ------------------------------------------------------------
    # Core Excel Writing Logic
    # ------------------------------------------------------------
    def _save_excel_to(self, path: str | os.PathLike):
        """
        Actually writes to Excel file using ExcelStore.
        Modify this based on your ExcelStore implementation.
        """

        # Example content — replace with real processed items
        rows = self.processed_items

        # Simple ExcelStore pattern (you can customize this)
        store = ExcelStore(path)
        try:
            # Example: write items
            # Replace with your actual ExcelStore API
            if hasattr(store, "write_rows"):
                store.write_rows("Emails", rows)

            # Add more sheets as needed
            # store.write_summary(...)
            # store.write_topics(...)

            # If your class uses save():
            if hasattr(store, "save"):
                store.save()

        finally:
            if hasattr(store, "close"):
                store.close()
