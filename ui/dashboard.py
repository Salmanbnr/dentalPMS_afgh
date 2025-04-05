import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
import qtawesome as qta
from pathlib import Path

# --- Determine Project Root (assuming dashboard_window.py is in dental_clinic/ui/dashboard/) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# --- Adjust import paths relative to PROJECT_ROOT ---
sys.path.insert(0, str(PROJECT_ROOT))
try:
    from ui.main_window import PatientListPage
    from database.schema import initialize_database  # For testing block
except ImportError as e:
    print(f"Error importing UI/DB modules in dashboard_window.py: {e}")
    print("Ensure the script is run where PROJECT_ROOT is correctly determined.")
    # Attempt relative import as fallback
    try:
        from main_window import PatientListPage
        from database.schema import initialize_database  # For testing block
    except ImportError:
        print("Failed to import necessary modules using relative paths.")
        sys.exit(1)

# --- Constants ---
CLINIC_NAME = "Salman Dental Clinic"
LOGO_FILENAME = "logo.png"
LOGO_PATH = LOGO_FILENAME

# --- Styling for the Dashboard Frame ---
COLOR_PRIMARY = "#2c3e50"  # Dark Blue/Gray (Sidebar)
COLOR_SECONDARY = "#ecf0f1" # Light Gray (Content Background)
COLOR_ACCENT = "#3498db"    # Bright Blue (Highlights, Buttons)
COLOR_TEXT_LIGHT = "#ffffff" # White (On Dark Background)
COLOR_BORDER = "#bdc3c7"    # Gray (Borders)
COLOR_HOVER = "#4a6fa5"     # Darker blue for hover

DASHBOARD_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_SECONDARY}; /* Overall window background */
    }}
    /* Sidebar Styling */
    #Sidebar {{
        background-color: {COLOR_PRIMARY};
        border-right: 1px solid {COLOR_BORDER};
    }}
    #Sidebar QLabel#ClinicNameLabel {{
        color: {COLOR_TEXT_LIGHT};
        font-size: 16pt;
        font-weight: bold;
        padding: 10px;
    }}
    #Sidebar QLabel#LogoLabel {{
        margin-bottom: 15px;
    }}
    #Sidebar QPushButton {{ /* Sidebar navigation buttons */
        background-color: transparent;
        color: {COLOR_TEXT_LIGHT};
        border: none;
        padding: 12px 15px;
        text-align: left;
        font-size: 11pt;
        border-radius: 4px;
        margin: 5px 10px;
    }}
    #Sidebar QPushButton:hover {{
        background-color: {COLOR_HOVER};
    }}
    #Sidebar QPushButton:checked {{
        background-color: {COLOR_ACCENT};
        font-weight: bold;
    }}

    /* Styling for the container holding the pages (optional) */
    #ContentStackWidget {{
        background-color: {COLOR_SECONDARY};
        /* No padding here; let the individual pages handle their padding */
    }}
"""

class DashboardWindow(QMainWindow):
    """Main application dashboard window with sidebar navigation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{CLINIC_NAME} - Dashboard")
        self.setGeometry(50, 50, 1200, 700)
        self.setStyleSheet(DASHBOARD_STYLESHEET)  # Apply dashboard frame styles

        # --- Main Widget and Layout ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 10)
        sidebar_layout.setSpacing(5)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Logo
        logo_label = QLabel()
        logo_label.setObjectName("LogoLabel")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if LOGO_PATH:
            pixmap = QPixmap(str(LOGO_PATH))
            logo_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("Logo Missing")
            logo_label.setStyleSheet("color: white; font-style: italic;")
            print(f"Warning: Logo file not found at {LOGO_PATH}")
        sidebar_layout.addWidget(logo_label)

        # Clinic Name
        clinic_name_label = QLabel(CLINIC_NAME)
        clinic_name_label.setObjectName("ClinicNameLabel")
        clinic_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clinic_name_label.setWordWrap(True)
        sidebar_layout.addWidget(clinic_name_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #bdc3c7; height: 1px; margin: 10px 5px;")
        sidebar_layout.addWidget(line)

        # Navigation Buttons
        self.nav_buttons = {}
        self.home_button = self.add_nav_button(sidebar_layout, "HOME", 'fa5s.home', 0)
        # Add placeholders for future buttons and connect them
        # self.appointments_button = self.add_nav_button(sidebar_layout, "Appointments", 'fa5s.calendar-alt', 1)
        # self.settings_button = self.add_nav_button(sidebar_layout, "Settings", 'fa5s.cog', 2)

        sidebar_layout.addStretch(1)

        main_layout.addWidget(self.sidebar)

        # --- Content Area ---
        # Use QStackedWidget to hold the different pages
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStackWidget")  # Assign object name for potential styling

        # *** Instantiate PatientListPage from main_window.py ***
        self.home_page = PatientListPage(self)
        self.content_stack.addWidget(self.home_page)  # Add it to the stack (index 0)

        # Add placeholder widgets for other potential pages
        # Make sure the index matches the button index
        # placeholder_appointments = QLabel("Appointments Page Placeholder")
        # placeholder_appointments.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.content_stack.addWidget(placeholder_appointments)  # index 1

        # placeholder_settings = QLabel("Settings Page Placeholder")
        # placeholder_settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.content_stack.addWidget(placeholder_settings)  # index 2

        main_layout.addWidget(self.content_stack)

        # --- Initialize ---
        self.home_button.setChecked(True)  # Start with Home selected
        self.current_button = self.home_button
        self.content_stack.setCurrentIndex(0)  # Ensure Home page is shown first

    def add_nav_button(self, layout, text, icon_name, index):
        button = QPushButton(qta.icon(icon_name, color=COLOR_TEXT_LIGHT), f" {text}")
        button.setCheckable(True)
        button.clicked.connect(lambda checked, idx=index, btn=button: self.switch_tab(checked, idx, btn))
        layout.addWidget(button)
        self.nav_buttons[index] = button
        return button

    def switch_tab(self, checked, index, button):
        if checked:
            if self.current_button and self.current_button != button:
                self.current_button.setChecked(False)

            # Check if the index is valid for the stack
            if index < self.content_stack.count():
                self.content_stack.setCurrentIndex(index)
                self.current_button = button
            else:
                print(f"Error: No content widget found for index {index}")
                # Optional: uncheck the clicked button or show an error
                button.setChecked(False)
                # Ensure the previous button remains checked
                if self.current_button:
                    self.current_button.setChecked(True)

        else:
            # Prevent unchecking the active button by re-clicking it
            if self.current_button == button:
                button.setChecked(True)

    def show_home_page(self):
        """Switch back to the home page (PatientListPage)."""
        self.content_stack.setCurrentIndex(0)
        self.home_button.setChecked(True)
        self.current_button = self.home_button

    def closeEvent(self, event):
        print("Closing Dashboard...")

        # --- Try to close child window from the active page ---
        # Get the current widget from the stack
        current_page = self.content_stack.currentWidget()
        # Check if it has the method we need (duck typing)
        if hasattr(current_page, 'close_active_child_window') and callable(current_page.close_active_child_window):
            print(f"Asking page '{current_page.objectName()}' to close its child window...")
            current_page.close_active_child_window()  # Ask the current page to close its window

        # Confirm exit
        reply = QMessageBox.question(self, 'Confirm Exit',
                                     "Are you sure you want to exit the application?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            print("Exiting application.")
            event.accept()
        else:
            print("Exit cancelled.")
            event.ignore()

# --- Testing Block (Optional, better to use main.py) ---
if __name__ == '__main__':
    print("Attempting to initialize database for Dashboard test...")
    if not initialize_database():
        print("Database initialization failed. Dashboard test may not function correctly.")
    else:
        print("Database initialized/verified successfully.")

    app = QApplication(sys.argv)
    # app.setStyle("Fusion")

    mainWin = DashboardWindow()
    mainWin.show()
    sys.exit(app.exec())
