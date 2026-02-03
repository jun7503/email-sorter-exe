import os
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QFileDialog,
    QHBoxLayout, QTextEdit
)
from PySide6.QtCore import Qt

from email_parser import parse_email_file
from text_clean import clean_body_for_semantics, canonical_subject, sender_domain
from keys import message_key, thread_key, update_group_key, content_hash
from dedup import SimilarityDecider
from excel_writer import ExcelStore
from summary import rebuild_summary
from topic_map import TopicMap
from clustering import DomainClusterer
from issue_milestone import extract_issue_milestone
from version import __version__

class EmailSorterWindow(QWidget):
    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle(f\"📬 EmailSorter v{__version__}")
        self.setMinimumSize(720, 520)
        self.setAcceptDrops(True)

        self.sim = SimilarityDecider(cfg)
        self.clusterer = DomainClusterer(cfg)
        self.excel = None
        self.index_keys = set()
        self.topic_map = TopicMap()

        self._build_ui()
        self._choose_excel_path()

    def _build_ui(self):
        v = QVBoxLayout(self)

        title = QLabel(\"Drag & drop .eml / .msg files here\")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(\"font-size:18px; font-weight:bold;\")
        v.addWidget(title)

        self.path_label = QLabel(\"Excel: (not chosen)\")
        v.addWidget(self.path_label)

        row = QHBoxLayout()
        choose_btn = QPushButton(\"Choose Excel Save Location…\")
        choose_btn.clicked.connect(self._choose_excel_path)
        open_btn = QPushButton(\"Open Excel\")
        open_btn.clicked.connect(self._open_excel)
        row.addWidget(choose_btn)
        row.addWidget(open_btn)
        v.addLayout(row)

        self.pb = QProgressBar()
        v.addWidget(self.pb)

        rebuild_btn = QPushButton(\"Rebuild Index & Summary\")
        rebuild_btn.clicked.connect(self._rebuild_index_summary)
        v.addWidget(rebuild_btn)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        v.addWidget(self.log)

        hint = QLabel(\"Tip: Append-only; your manual edits stay safe.\")
        hint.setStyleSheet(\"color:gray;\")
        v.addWidget(hint)

    def _choose_excel_path(self):
        default_dir = str(Path.home())
        path, _ = QFileDialog.getSaveFileName(self, \"Choose Excel output\", default_dir, \"Excel (*.xlsx)\")
        if not path:
            path = str(Path.home() / \"Email_Sorter.xlsx\")
        if not path.lower().endswith(\".xlsx\"):
            path += \".xlsx\"

        self.excel = ExcelStore(path)
        self.path_label.setText(f\"Excel: {path}\")
        self.index_keys = self.excel.load_index_keys()
        self._log(f\"Excel ready: {path}\")

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        self._process_files(files)

    def _open_excel(self):
        if self.excel and Path(self.excel.xlsx_path).exists():
            os.startfile(self.excel.xlsx_path)
        else:
            self._log(\"Excel file not found yet.\")

    def _rebuild_index_summary(self):
        self.excel.rebuild_index_from_topics()
        rebuild_summary(self.excel.wb)
        self._log(\"✔ Index & Summary rebuilt.\")

    def _process_files(self, files: List[str]):
        if not self.excel:
            self._log(\"Choose Excel location first.\")
            return

        total = len(files)
        done = skipped = appended = 0

        for i, f in enumerate(files, start=1):
            try:
                res = self._handle_one(f)
                if res == \"skipped\": skipped += 1
                if res == \"appended\": appended += 1
            except Exception as e:
                self._log(f\"Error: {e}\")

            done += 1
            self.pb.setValue(int(done / max(total, 1) * 100))

        rebuild_summary(self.excel.wb)
        self._log(f\"✔ Done. Processed {done}. Skipped {skipped}. Appended {appended}.\")
        self._log(\"✔ Summary rebuilt.\")

    def _handle_one(self, path: str):
        meta = parse_email_file(path)

        mkey = message_key(meta)
        if mkey in self.index_keys:
            return \"skipped\"

        tkey = thread_key(meta)
        clean_body = clean_body_for_semantics(meta.get(\"Body\", \"\"))
        up_key = update_group_key(meta, clean_body[:400])

        prev = self.excel.latest_body_for_update_group(up_key)
        is_version = self.sim.is_version(clean_body, prev)

        dom = sender_domain(meta.get(\"From\", \"\"))
        sub_idx = self.clusterer.assign(dom, canonical_subject(meta.get(\"Subject\", \"\")), clean_body)
        topic_info = self.topic_map.ensure_domain_topic(self.excel.wb, dom, sub_idx)

        issue, milestone = extract_issue_milestone(meta.get(\"Subject\", \"\"), clean_body)

        row = {
            \"Received\": meta.get(\"Received\"),
            \"From\": meta.get(\"From\"), \"To\": meta.get(\"To\"), \"Cc\": meta.get(\"Cc\"),
            \"Subject\": meta.get(\"Subject\"),
            \"SuperTopicID\": topic_info[\"SuperTopicID\"],
            \"SuperTopicName\": topic_info[\"SuperTopicName\"],
            \"TopicID\": topic_info[\"TopicID\"],
            \"SubTopicName\": topic_info[\"SubTopicName\"],
            \"Issue\": issue, \"Milestone\": milestone,
            \"Sender\": meta.get(\"Sender\"),
            \"Body\": clean_body[: int(self.cfg.get(\"max_body_chars\", 4000))],
            \"MessageID\": meta.get(\"MessageID\"),
            \"Hash\": content_hash(meta),
            \"FilePath\": path,
            \"ThreadKey\": tkey,
            \"UpdateGroupKey\": up_key,
            \"Status\": \"\"
        }

        sheet = self.excel.topic_sheet(dom)
        self.excel.append_topic_row(dom, row)

        last_row = self.excel.last_row_index(dom)
        self.excel.append_index(mkey, tkey, up_key, sheet, last_row)
        self.index_keys.add(mkey)

        return \"appended\"

    def _log(self, msg: str):
        self.log.append(msg)
