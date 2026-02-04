# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QFileDialog,
    QHBoxLayout, QMessageBox
)

# Local modules
from .version import __version__
from .processor import process_paths  # <-- pipeline: parse -> dedup -> cluster -> write

SUPPORTED_EXTS = {".eml", ".msg"}


class EmailSorterWindow(QWidget):
    """
    Main UI window for EmailSorter application.

    NOTE:
      - Drag files from *File Explorer* (not directly from Outlook).
      - The pipeline writes/updates the Excel workbook on each run.
    """

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg or {}
        self.setWindowTitle(f"📬 EmailSorter v{__version__}")
        self.setMinimumSize(720, 520)
        self.setAcceptDrops(True)

        # State
        self.excel_path: str | None = None

        # UI
        self._build_ui()
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
        self.path_label.setWordWrap(True)
        v.addWidget(self.path_label)

        row = QHBoxLayout()

        # Change output path
        self.btn_change_path = QPushButton("Change Excel Path")
        self.btn_change_path.clicked.connect(self._choose_excel_path)
        row.addWidget(self.btn_change_path)

        # Save Excel (confirmation only; pipeline already saves on write)
        self.btn_save_excel = QPushButton("Save Excel")
        self.btn_save_excel.clicked.connect(self._on_save_excel_clicked)
        row.addWidget(self.btn_save_excel)

        v.addLayout(row)

        # Optional file picker (so you don't have to drag)
        self.btn_add_files = QPushButton("Add files…")
        self.btn_add_files.clicked.connect(self._pick_files)
        v.addWidget(self.btn_add_files)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        v.addWidget(self.progress)

    # ------------------------------------------------------------
    # Drag & drop events (drag from File Explorer)
    # ------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls: List[QUrl] = event.mimeData().urls()
        if not urls:
            QMessageBox.information(self, "Info", "No items dropped.")
            return

        filepaths: List[str] = []
        for u in urls:
            if u.isLocalFile():
                p = u.toLocalFile()
                if os.path.isfile(p) and os.path.splitext(p)[1].lower() in SUPPORTED_EXTS:
                    filepaths.append(p)

        if not filepaths:
            QMessageBox.information(self, "Info", "No supported files (.eml/.msg) found in drop.")
            return

        self._process_files(filepaths)

    # ------------------------------------------------------------
    # File picker
    # ------------------------------------------------------------
    def _pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select .eml/.msg files",
            "",
            "Email files (*.eml *.msg);;All files (*.*)"
        )
        if files:
            self._process_files(files)

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
            self._set_excel_path(path)
            return

        # Fixed path mode
        if mode == "fixed_path":
            fixed = (self.cfg.get("excel_output_path") or "").strip()
            if fixed:
                self._set_excel_path(fixed)
                return
            self.excel_path = None
            self.path_label.setText("Excel: (fixed path missing)")
            return

        # Default (manual selection on first use)
        self.excel_path = None
        self.path_label.setText("Excel: (not chosen)")

    def _ensure_excel_path(self) -> bool:
        """Prompt for a path if not yet chosen."""
        if self.excel_path:
            return True
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Choose Excel Output File",
            "EmailSorter_Output.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not path:
            return False
        self._set_excel_path(path)
        return True

    def _set_excel_path(self, path: str):
        p = Path(path)
        if p.suffix.lower() != ".xlsx":
            p = p.with_suffix(".xlsx")
        p.parent.mkdir(parents=True, exist_ok=True)
        self.excel_path = str(p)
        self.path_label.setText(f"Excel: {self.excel_path}")

    # ------------------------------------------------------------
    # Save Excel (confirmation only)
    # ------------------------------------------------------------
    def _on_save_excel_clicked(self):
        if not self._ensure_excel_path():
            return
        QMessageBox.information(self, "Success", f"Excel saved successfully:\n{self.excel_path}")

    # ------------------------------------------------------------
    # Core processing flow
    # ------------------------------------------------------------
    def _process_files(self, paths: List[str]):
        if not self._ensure_excel_path():
            return

        # Show progress & disable actions
        self.progress.setVisible(True)
        self.btn_add_files.setEnabled(False)
        self.btn_change_path.setEnabled(False)
        self.btn_save_excel.setEnabled(False)

        try:
            logging.info("Processing %d files -> %s", len(paths), self.excel_path)
            result = process_paths(paths, self.excel_path)

            # Human-friendly breakdown
            msg = (
                f"Dropped: {result.get('dropped', 0)} file(s)\n"
                f"Parsed OK: {result.get('parsed', 0)}\n"
                f"Empty/unsupported skipped: {result.get('empty', 0)}\n"
                f"Duplicates skipped: {result.get('dedup_skipped', 0)}\n"
                f"Appended to _Data: {result.get('appended', 0)}\n"
                f"Index entries added: {result.get('index_added', 0)}"
            )
            QMessageBox.information(self, "Done", msg)

        except PermissionError:
            QMessageBox.warning(
                self, "File Locked",
                "Excel file appears to be locked by Excel/OneDrive.\n"
                "Please close it and try again."
            )
        except Exception as e:
            logging.exception("Processing failed: %s", e)
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.progress.setVisible(False)
            self.btn_add_files.setEnabled(True)
            self.btn_change_path.setEnabled(True)
            self.btn_save_excel.setEnabled(True)
``
