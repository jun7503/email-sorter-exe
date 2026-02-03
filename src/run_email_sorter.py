import sys
from email_sorter.app import main

if __name__ == "__main__":
    main()

    # Keep window open when running the EXE
    if getattr(sys, 'frozen', False):
        print("\nDEBUG: Finished running EmailSorter.exe")
        input("Press Enter to exit...")
