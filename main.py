import sys
from PyQt6.QtWidgets import QApplication
from pathlib import Path

# Determine project root (assuming main.py is at the root)
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from ui.dashboard import DashboardWindow  # Correct import path
    from database.schema import initialize_database
except ImportError as e:
    print(f"Error importing application components: {e}")
    print("Ensure the project structure is correct and all dependencies are installed.")
    sys.exit(1)

if __name__ == '__main__':
    print("Starting Salman Dental Clinic Application...")

    print("Initializing database...")
    if not initialize_database():
        print("ERROR: Database initialization failed. Application cannot start.")
        sys.exit(1)
    else:
        print("Database ready.")

    app = QApplication(sys.argv)

    print("Creating dashboard...")
    main_window = DashboardWindow()
    main_window.showMaximized()  # Use showMaximized() instead of showFullScreen()
    print("Dashboard displayed. Running application event loop.")

    sys.exit(app.exec())
