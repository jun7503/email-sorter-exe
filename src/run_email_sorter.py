# src/run_email_sorter.py
from email_sorter.app import main
import os, logging

if __name__ == "__main__":
    main()
    print("\nDEBUG: Program finished.")
    input("Press Enter to exit...")

def init_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename=os.path.join("logs", "app.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
