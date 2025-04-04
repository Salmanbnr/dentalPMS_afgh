# ui/inventory_management.py
import sys
import os
from pathlib import Path

# Add project root to path to enable imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QStyle, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
import qtawesome as qta

# Import our modules
from ui.services.services_ui import ServicesManagementWidget
from ui.medication.medication_ui import MedicationsManagementWidget

class InventoryManagementWindow(QMainWindow):
    """Main window for managing services and medications"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dental Clinic - Inventory Management")
        self.resize(900, 700)

        # Set window icon
        self.setWindowIcon(qta.icon('fa5s.tooth'))

        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()

    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Tab widget for switching between services and medications
        self.tab_widget = QTabWidget()

        # Services tab
        self.services_widget = ServicesManagementWidget()
        self.tab_widget.addTab(self.services_widget, "Services")

        # Medications tab
        self.medications_widget = MedicationsManagementWidget()
        self.tab_widget.addTab(self.medications_widget, "Medications")

        main_layout.addWidget(self.tab_widget)

        self.setCentralWidget(main_widget)

    def setup_menu(self):
        # Create a menu bar
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setIcon(qta.icon('fa5s.sign-out-alt'))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def setup_status_bar(self):
        # Create a status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryManagementWindow()
    window.show()
    sys.exit(app.exec())
