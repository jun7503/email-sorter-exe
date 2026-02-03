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

# 🔁 Relative imports inside the package
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
        self.processed_items = []    # collected parsed emails
        self.excel_path: str | None = None

        # Build UI
        self._build_ui()

        # Select Excel output location
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

        # Excel path display
        self.path_label = QLabel("Excel: (not chosen)")
        v.addWidget(self.path_label)

        row = QHBoxLayout()

        # Change output path
        self.btn_change_path = QPushButton("Change Excel Path")
        self.btn_change_path.clicked.connect(self._choose_excel_path)
        row.addWidget(self.btn_change_path)

        # Save Excel
        self.btn_save_excel = QPushButton("Save Excel")
        self.btn_save_excel.clicked.connect(self._on_save_excel_clicked)
        row.addWidget(self.btn_save_excel)

        v.addLayout(row)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        v.addWidget(self.progress)

    # ------------------------------------------------------------
    # Drag & drop events (fully fixed)
    # ------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        from PySide6.QtCore import QUrl
        import logging

        urls = event.mimeData().urls()
        if not urls:
            logging.error("DropEvent: No URLs found.")
            return

        filepaths = []

        # Convert QUrl to local file paths
        for url in urls:
            local_path = url.toLocalFile()
            if local_path:
                filepaths.append(local_path)
                logging.info(f"DropEvent: Received file = {local_path}")

        if not filepaths:
            QMessageBox.warning(self, "No files", "No valid files dropped.")
            return

        # Process each file
        for path in filepaths:
            ext = os.path.splitext(path)[1].lower()

            if ext not in (".eml", ".msg"):
                logging.warning(f"Skipped non-email file: {path}")
                continue

            try:
                rec = parse_email_file(path)
                logging.info(
                    f"Parsed successfully: subject={rec.get('Subject')}"
                )
                self.processed_items.append(rec)

            except Exception as e:
                logging.exception(f"Failed parsing file: {path}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Cannot parse:\n{path}\n\n{str(e)}"
                )

        QMessageBox.information(
            self,
            "Done",
            f"Processed {len(filepaths)} email(s)."
        )

    # ------------------------------------------------------------
    # Excel output path selection
    # ------------------------------------------------------------
    def _choose_excel_path(self):
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

        # Default
        self.excel_path = None
        self.path_label.setText("Excel: (not chosen)")

    # ------------------------------------------------------------
    # Save Excel Handler
    # ------------------------------------------------------------
    def _on_save_excel_clicked(self):
        try:
            mode = (self.cfg.get("excel_path_mode") or "").lower()

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

            if not self.excel_path:
                self._choose_excel_path()
                if not self.excel_path:
                    return

            p = Path(self.excel_path)
            p.parent.mkdir(parents=True, exist_ok=True)

            # Show progress
            self.progress.setVisible(True)
            self.btn_save_excel.setEnabled(False)

            self._save_excel_to(self.excel_path)

            self.path_label.setText(f"Excel: {self.excel_path}")
            QMessageBox.information(
                self,
                "Success",
                f"Excel saved successfully:\n{self.excel_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

        finally:
               self.progress.setVisible(False)
            self.btn_save_excel.setEnabled(True)

    # ------------------------------------------------------------
    # Excel Writing Logic
    # ------------------------------------------------------------
    def _save_excel_to(self, path: str | os.PathLike):
        rows = self.processed_items

        store = ExcelStore(path)
        try:
            if hasattr(store, "write_rows"):
                store.write_rows("Emails", rows)

            if hasattr(store, "save"):
                store.save()

        finally:
            if hasattr(store, "close"):
                store.close()
