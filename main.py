# dental_clinic/main.py
import sys
from PyQt6.QtWidgets import QApplication
from pathlib import Path

# Ensure project root is in sys.path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

try:
    from database.schema import initialize_database
    from ui.main_window import MainWindow
except ImportError as e:
    print(f"Error importing necessary modules in main.py: {e}")
    print("Please ensure the directory structure (database/, ui/) is correct and you are in the 'dental_clinic' directory.")
    input("Press Enter to exit...") # Keep console open to see error
    sys.exit(1)

def main():
    # Initialize Database (create tables if they don't exist)
    print("Initializing Database...")
    if not initialize_database():
        print("FATAL: Database initialization failed. Exiting application.")
        # Optionally show a GUI error message here instead of just printing
        sys.exit(1)
    print("Database initialization complete.")

    # --- Create and Run Application ---
    app = QApplication(sys.argv)

    # Optional: Apply a style
    # app.setStyle("Fusion")

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()