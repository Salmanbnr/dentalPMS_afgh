import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
import qtawesome as qta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.main_window import PatientListPage
from database.schema import initialize_database
from ui.inventory_management import InventoryManagementWindow
from ui.due import DuePatientsWidget  # Import the DuePatientsWidget

CLINIC_NAME = "Salman Dental Clinic"
LOGO_FILENAME = "logo.png"
LOGO_PATH = LOGO_FILENAME

COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

DASHBOARD_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_SECONDARY};
    }}
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
    #Sidebar QPushButton {{
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
    #ContentStackWidget {{
        background-color: transparent; /* Allow child widgets to handle their own background */
    }}
    QTabWidget, QTabBar::tab {{
        background-color: transparent; /* Ensure no interference with inventory tabs */
        border: none;
    }}
"""

class DashboardWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{CLINIC_NAME} - Dashboard")
        self.setGeometry(50, 50, 1200, 700)
        self.setStyleSheet(DASHBOARD_STYLESHEET)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 10)
        sidebar_layout.setSpacing(5)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        logo_label = QLabel()
        logo_label.setObjectName("LogoLabel")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            pixmap = QPixmap(str(LOGO_PATH))
            logo_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except:
            logo_label.setText("Logo Missing")
            logo_label.setStyleSheet("color: white; font-style: italic;")
        sidebar_layout.addWidget(logo_label)

        clinic_name_label = QLabel(CLINIC_NAME)
        clinic_name_label.setObjectName("ClinicNameLabel")
        clinic_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clinic_name_label.setWordWrap(True)
        sidebar_layout.addWidget(clinic_name_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #bdc3c7; height: 1px; margin: 10px 5px;")
        sidebar_layout.addWidget(line)

        self.nav_buttons = {}
        # Connect directly to refresh functions instead of switch_tab
        self.home_button = self.add_nav_button(sidebar_layout, "HOME", 'fa5s.home', self.refresh_home_page)
        self.due_patients_button = self.add_nav_button(sidebar_layout, "DUE PATIENTS", 'fa5s.money-bill-alt', self.refresh_due_patients)
        self.inventory_button = self.add_nav_button(sidebar_layout, "INVENTORY", 'fa5s.box', self.refresh_inventory)
        self.settings_button = self.add_nav_button(sidebar_layout, "SETTINGS", 'fa5s.cog', self.refresh_settings)

        sidebar_layout.addStretch(1)
        main_layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStackWidget")

        self.home_page = None
        self.init_home_page()

        # Add Due Patients widget
        self.due_patients_page = None
        self.init_due_patients_page()

        # Create and add Inventory management UI
        self.inventory_page = None
        self.init_inventory_page()

        # Create settings page
        self.settings_page = None
        self.init_settings_page()

        main_layout.addWidget(self.content_stack)

        self.home_button.setChecked(True)
        self.current_button = self.home_button
        self.content_stack.setCurrentIndex(0)

    def init_home_page(self):
        try:
            if self.home_page is not None:
                self.content_stack.removeWidget(self.home_page)
                self.home_page.deleteLater()

            self.home_page = PatientListPage(self)
            self.content_stack.insertWidget(0, self.home_page)
        except Exception as e:
            error_widget = QLabel(f"Error loading PatientListPage: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.home_page = error_widget
            self.content_stack.insertWidget(0, error_widget)

    def init_due_patients_page(self):
        try:
            if self.due_patients_page is not None:
                self.content_stack.removeWidget(self.due_patients_page)
                self.due_patients_page.deleteLater()
                
            self.due_patients_page = DuePatientsWidget(self)
            self.content_stack.insertWidget(1, self.due_patients_page)
        except Exception as e:
            error_widget = QLabel(f"Error loading DuePatientsWidget: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.due_patients_page = error_widget
            self.content_stack.insertWidget(1, error_widget)

    def init_inventory_page(self):
        try:
            if self.inventory_page is not None:
                self.content_stack.removeWidget(self.inventory_page)
                self.inventory_page.deleteLater()
                
            self.inventory_page = InventoryManagementWindow()
            self.inventory_widget = self.inventory_page.get_central_widget()
            self.content_stack.insertWidget(2, self.inventory_widget)
            self.inventory_page = self.inventory_widget  # Store reference for deletion later
        except Exception as e:
            error_widget = QLabel(f"Error loading InventoryManagementWindow: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.inventory_page = error_widget
            self.content_stack.insertWidget(2, error_widget)

    def init_settings_page(self):
        try:
            if self.settings_page is not None:
                self.content_stack.removeWidget(self.settings_page)
                self.settings_page.deleteLater()
                
            self.settings_page = QLabel("Settings Page")
            self.settings_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.settings_page.setStyleSheet("font-size: 24px;")
            self.content_stack.insertWidget(3, self.settings_page)
        except Exception as e:
            error_widget = QLabel(f"Error loading Settings: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.settings_page = error_widget
            self.content_stack.insertWidget(3, error_widget)

    def add_nav_button(self, layout, text, icon_name, callback_function):
        button = QPushButton(qta.icon(icon_name, color=COLOR_TEXT_LIGHT), f" {text}")
        button.setCheckable(True)
        button.clicked.connect(callback_function)
        layout.addWidget(button)
        return button

    def update_button_states(self, active_button):
        # Update button states
        for btn in [self.home_button, self.due_patients_button, self.inventory_button, self.settings_button]:
            if btn != active_button:
                btn.setChecked(False)
        active_button.setChecked(True)
        self.current_button = active_button

    def refresh_home_page(self):
        self.init_home_page()  # Recreate the page
        self.content_stack.setCurrentIndex(0)
        self.update_button_states(self.home_button)

    def refresh_due_patients(self):
        self.init_due_patients_page()  # Recreate the page
        self.content_stack.setCurrentIndex(1)
        self.update_button_states(self.due_patients_button)

    def refresh_inventory(self):
        self.init_inventory_page()  # Recreate the page
        self.content_stack.setCurrentIndex(2)
        self.update_button_states(self.inventory_button)

    def refresh_settings(self):
        self.init_settings_page()  # Recreate the page
        self.content_stack.setCurrentIndex(3)
        self.update_button_states(self.settings_button)

    def show_home_page(self):
        self.refresh_home_page()

    def closeEvent(self, event):
        current_page = self.content_stack.currentWidget()
        if hasattr(current_page, 'close_active_child_window') and callable(current_page.close_active_child_window):
            current_page.close_active_child_window()

        reply = QMessageBox.question(self, 'Confirm Exit',
                                     "Are you sure you want to exit the application?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    initialize_database()
    app = QApplication(sys.argv)
    mainWin = DashboardWindow()
    mainWin.show()
    sys.exit(app.exec())