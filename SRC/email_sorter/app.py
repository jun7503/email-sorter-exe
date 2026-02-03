from PySide6.QtWidgets import QApplication
from .gui import EmailSorterWindow
from .config_loader import load_config

def main():
    cfg = load_config()
    app = QApplication([])
    window = EmailSorterWindow(cfg)
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
