# src/email_sorter/app.py
from PySide6.QtWidgets import QApplication
from .gui import EmailSorterWindow        # ← relative import
from .config_loader import load_config    # ← relative import

def main():
    cfg = load_config()
    app = QApplication([])
    window = EmailSorterWindow(cfg)
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
