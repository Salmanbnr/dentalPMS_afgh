import sys
import os
from pathlib import Path

# Add project root to path to enable imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QStatusBar,QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import qtawesome as qta

# Import our modules
from ui.services.services_ui import ServicesManagementWidget
from ui.medication.medication_ui import MedicationsManagementWidget

# Color constants (reused from previous UIs)
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

INVENTORY_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_SECONDARY};
    }}
    QTabWidget {{
        border: none;
        background-color: {COLOR_SECONDARY};
    }}
    QTabBar::tab {{
        background-color: {COLOR_SECONDARY};
        border: 1px solid {COLOR_BORDER};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 10px 20px;
        color: {COLOR_TEXT_DARK};
        margin-right: 2px;
    }}
    QTabBar::tab:selected, QTabBar::tab:hover {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
    }}
    QStatusBar {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        border-top: 1px solid {COLOR_BORDER};
    }}
"""

class InventoryManagementWindow(QMainWindow):
    """Main window for managing services and medications"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dental Clinic - Inventory Management")
        self.resize(1000, 700)

        # Set window icon
        self.setWindowIcon(qta.icon('fa5s.tooth'))

        self.setup_ui()
        self.setup_status_bar()

    def setup_ui(self):
        # Apply stylesheet
        self.setStyleSheet(INVENTORY_STYLESHEET)

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        
        

        # Tab widget for switching between services and medications
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget { border: none; }")

        # Services tab
        self.services_widget = ServicesManagementWidget()
        self.tab_widget.addTab(self.services_widget, "Services")

        # Medications tab
        self.medications_widget = MedicationsManagementWidget()
        self.tab_widget.addTab(self.medications_widget, "Medications")

        main_layout.addWidget(self.tab_widget)

        self.setCentralWidget(main_widget)

    def setup_status_bar(self):
        # Create a status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLOR_PRIMARY};
                color: {COLOR_TEXT_LIGHT};
                border-top: 1px solid {COLOR_BORDER};
                padding: 5px;
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryManagementWindow()
    window.show()
    sys.exit(app.exec())