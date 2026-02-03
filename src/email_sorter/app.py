# src/email_sorter/app.py

import logging
import os
import tempfile
import time

from PySide6.QtWidgets import QApplication
from .gui import EmailSorterWindow
from .config_loader import load_config


def init_logger():
    r"""
    Initialize runtime logging.
    Creates a log file in the user's temp folder:
        C:\Users\<User>\AppData\Local\Temp\EmailSorterLogs\
    """
    log_dir = os.path.join(tempfile.gettempdir(), "EmailSorterLogs")
    os.makedirs(log_dir, exist_ok=True)

    ts = time.strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(log_dir, f"EmailSorter_{ts}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
    )

    logging.getLogger().info("=== EmailSorter started ===")
    logging.getLogger().info("Log file: %s", log_path)

    return log_path


def main():
    log_path = init_logger()
    logging.getLogger().info("main() started")

    try:
        cfg = load_config()
        logging.getLogger().info("Configuration loaded successfully")

        app = QApplication([])
        window = EmailSorterWindow(cfg)
        window.show()

        logging.getLogger().info("GUI created successfully")

        app.exec()

    except Exception as e:
        logging.getLogger().exception("Unhandled error in main()")
        raise


if __name__ == "__main__":
    main()
