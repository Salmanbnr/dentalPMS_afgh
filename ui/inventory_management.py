import sys
import os
from pathlib import Path

# Add project root to path to enable imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QStatusBar, QLabel
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
    QMainWindow, QWidget {{
        background-color: {COLOR_SECONDARY};
    }}
    QTabWidget {{
        border: none;
        background-color: {COLOR_SECONDARY};
        padding: 5px;
    }}
    QTabBar::tab {{
        background-color: {COLOR_SECONDARY};
        border: 2px solid {COLOR_BORDER};
        border-bottom: none;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 15px 30px;
        color: {COLOR_TEXT_DARK};
        margin-right: 4px;
        min-width: 150px;
        font-size: 12pt;
        font-weight: 600;
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease; /* Smooth transition for hover and selection */
    }}
    QTabBar::tab:selected {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border-bottom: 3px solid {COLOR_PRIMARY};
        font-weight: bold;
        box-shadow: 0 5px 10px rgba(0, 0, 0, 0.3);
        border: 2px solid {COLOR_PRIMARY};
    }}
    QTabBar::tab:hover {{
        background-color: {COLOR_HOVER};
        color: {COLOR_TEXT_LIGHT};
        border: 2px solid {COLOR_ACCENT};
        box-shadow: 0 5px 10px rgba(0, 0, 0, 0.3);
    }}
    QTabWidget::pane {{
        border: 2px solid {COLOR_BORDER};
        border-radius: 6px;
        background-color: {COLOR_SECONDARY};
        padding: 15px;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    QStatusBar {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        border-top: 2px solid {COLOR_BORDER};
        padding: 8px;
        font-size: 10pt;
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

        # Services tab with icon
        self.services_widget = ServicesManagementWidget()
        self.tab_widget.addTab(self.services_widget, qta.icon('fa5s.cogs', color=COLOR_TEXT_DARK), "Services")

        # Medications tab with icon
        self.medications_widget = MedicationsManagementWidget()
        self.tab_widget.addTab(self.medications_widget, qta.icon('fa5s.pills', color=COLOR_TEXT_DARK), "Medications")

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

    def get_central_widget(self):
        """Return the central widget for embedding in another window, with its stylesheet."""
        widget = self.centralWidget()
        widget.setStyleSheet(INVENTORY_STYLESHEET)  # Ensure the widget retains its stylesheet
        return widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryManagementWindow()
    window.show()
    sys.exit(app.exec())