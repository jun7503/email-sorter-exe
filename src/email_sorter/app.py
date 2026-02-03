from PySide6.QtWidgets import QApplication
from email_sorter.gui import EmailSorterWindow
from email_sorter.config_loader import load_config

def main():
    cfg = load_config()
    app = QApplication([])
    window = EmailSorterWindow(cfg)
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
