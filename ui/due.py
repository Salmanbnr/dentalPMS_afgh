import sys
import os
from pathlib import Path

# Add project root to path to enable imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QColor
import qtawesome as qta

# Use absolute/relative imports for the model
try:
    from model import due_model
except ImportError:
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(project_root))
    from model import due_model

# Color constants (matching the provided style)
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

DUE_PAGE_STYLESHEET = f"""
    /* Style the DuePatientsWidget itself */
    #DuePatientsWidget {{
        background-color: {COLOR_SECONDARY};
        padding: 15px;
    }}

    /* Header frame styling */
    #DuePatientsWidget #HeaderFrame {{
        border-bottom: 1px solid {COLOR_BORDER};
        padding-bottom: 10px;
    }}

    /* Input fields and buttons */
    #DuePatientsWidget QLineEdit {{
        padding: 8px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        font-size: 10pt;
        background-color: white;
    }}
    #DuePatientsWidget QPushButton {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border: none;
        padding: 8px 15px;
        border-radius: 4px;
        font-size: 10pt;
        min-width: 120px;
    }}
    #DuePatientsWidget QPushButton:hover {{
        background-color: {COLOR_HOVER};
    }}
    #DuePatientsWidget QPushButton:disabled {{
        background-color: #95a5a6;
        color: #ecf0f1;
    }}

    /* Table Styling */
    #DuePatientsWidget QTableWidget {{
        border: 1px solid {COLOR_BORDER};
        gridline-color: {COLOR_BORDER};
        font-size: 10pt;
        background-color: white;
    }}
    #DuePatientsWidget QHeaderView::section {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        padding: 6px;
        border: none;
        border-right: 1px solid {COLOR_BORDER};
        font-weight: bold;
    }}
    #DuePatientsWidget QHeaderView::section:last {{
        border-right: none;
    }}
    #DuePatientsWidget QTableWidget::item {{
        padding: 5px;
        color: {COLOR_TEXT_DARK};
    }}
    #DuePatientsWidget QTableWidget::item:selected {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
    }}
    #DuePatientsWidget QTableWidget::item:focus {{
        outline: none;
    }}

    /* Scroll Bars */
    #DuePatientsWidget QScrollBar:vertical {{
        border: none;
        background: {COLOR_SECONDARY};
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    #DuePatientsWidget QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}
    #DuePatientsWidget QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        background: none;
    }}
    #DuePatientsWidget QScrollBar:horizontal {{
        border: none;
        background: {COLOR_SECONDARY};
        height: 10px;
        margin: 0px 0px 0px 0px;
    }}
    #DuePatientsWidget QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER};
        min-width: 20px;
        border-radius: 5px;
    }}
    #DuePatientsWidget QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: none;
    }}
"""

class DuePatientsWidget(QWidget):
    """
    A widget to display patients with outstanding due amounts,
    designed to be used in a dashboard.
    """
    data_loaded = pyqtSignal()

    SEARCH_DEBOUNCE_MS = 350

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DuePatientsWidget")
        self.setStyleSheet(DUE_PAGE_STYLESHEET)

        # Timer for live search debouncing
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(self.SEARCH_DEBOUNCE_MS)

        self._setup_ui()
        self._connect_signals()
        self.load_due_patients()  # Load data initially

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Heading "Patients with Due Amounts"
        heading_label = QLabel("Patients with Due Amounts")
        heading_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24pt;
                font-weight: bold;
                color: {COLOR_PRIMARY};
                margin-bottom: 15px;
            }}
        """)
        main_layout.addWidget(heading_label)

        # Header
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        search_icon = qta.icon('fa5s.search', color=COLOR_TEXT_DARK)
        search_label = QLabel()
        search_label.setPixmap(search_icon.pixmap(QSize(16, 16)))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Live search by Patient ID, Name, or Phone...")
        self.search_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_input.setMinimumWidth(300)

        self.search_button = QPushButton(qta.icon('fa5s.search', color=COLOR_TEXT_LIGHT), " Search")
        self.refresh_button = QPushButton(qta.icon('fa5s.sync', color=COLOR_TEXT_LIGHT), " Refresh")

        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 1)
        header_layout.addWidget(self.search_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addStretch(1)

        main_layout.addWidget(header_frame)

        # Scroll Area for Due Table
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Due Table
        self.due_table = QTableWidget()
        self.due_table.setColumnCount(7)
        self.due_table.setHorizontalHeaderLabels([
            "Patient ID", "Name", "Father's Name", "Phone Number", "Address", "Due Visits", "Total Due (PKR)"
        ])
        self.due_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.due_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.due_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.due_table.verticalHeader().setVisible(False)
        self.due_table.horizontalHeader().setStretchLastSection(True)
        self.due_table.setShowGrid(True)

        # Adjust column widths
        self.due_table.setColumnWidth(0, 80)  # Patient ID
        self.due_table.setColumnWidth(1, 150)  # Name
        self.due_table.setColumnWidth(2, 150)  # Father's Name
        self.due_table.setColumnWidth(3, 120)  # Phone Number
        self.due_table.setColumnWidth(4, 200)  # Address
        self.due_table.setColumnWidth(5, 80)   # Due Visits
        self.due_table.setColumnWidth(6, 120)  # Total Due (PKR)

        scroll_area.setWidget(self.due_table)
        main_layout.addWidget(scroll_area)

        # Status Label
        self.status_label = QLabel("Loading data...")
        self.status_label.setStyleSheet(f"font-style: italic; color: {COLOR_TEXT_DARK};")
        main_layout.addWidget(self.status_label)

    def _connect_signals(self):
        self.search_input.textChanged.connect(self.search_timer.start)
        self.search_timer.timeout.connect(self._perform_search)
        self.search_button.clicked.connect(self._perform_search)
        self.refresh_button.clicked.connect(self.refresh_list)

    def _perform_search(self):
        search_term = self.search_input.text().strip()
        self.load_due_patients(search_term)

    def refresh_list(self):
        self.search_input.clear()
        self._perform_search()

    def load_due_patients(self, search_term=""):
        self.status_label.setText("Searching..." if search_term else "Loading data...")
        
        patients_data = due_model.get_due_patients_details(search_term)

        self.due_table.setSortingEnabled(False)
        self.due_table.setRowCount(0)

        if patients_data is None:
            QMessageBox.critical(self, "Database Error", "Could not retrieve patient debt information. Please check logs.")
            self.status_label.setText("Error loading data.")
            return
        elif not patients_data:
            search_message_part = f' matching "{search_term}"' if search_term else ""
            self.status_label.setText(f"No patients found with due amounts{search_message_part}.")
        else:
            self.due_table.setRowCount(len(patients_data))
            total_overall_due = 0.0
            for row, patient in enumerate(patients_data):
                patient_id_num = patient.get('patient_id')
                id_item = QTableWidgetItem(str(patient_id_num) if patient_id_num is not None else "N/A")
                name = QTableWidgetItem(str(patient.get('name', 'N/A')))
                father_name = QTableWidgetItem(str(patient.get('father_name', '')))
                phone = QTableWidgetItem(str(patient.get('phone_number', 'N/A')))
                address = QTableWidgetItem(str(patient.get('address', '')))
                due_visits_count_val = patient.get('due_visits_count', 0)
                due_visits_item = QTableWidgetItem(str(due_visits_count_val))
                due_visits_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                total_due = patient.get('total_due', 0.0)
                total_overall_due += total_due
                due_item = QTableWidgetItem(f"PKR {total_due:,.2f}")
                due_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                self.due_table.setItem(row, 0, id_item)
                self.due_table.setItem(row, 1, name)
                self.due_table.setItem(row, 2, father_name)
                self.due_table.setItem(row, 3, phone)
                self.due_table.setItem(row, 4, address)
                self.due_table.setItem(row, 5, due_visits_item)
                self.due_table.setItem(row, 6, due_item)

            self.status_label.setText(f"Found {len(patients_data)} patient(s) with a total due amount of PKR {total_overall_due:,.2f}.")

        self.due_table.setSortingEnabled(True)
        self.data_loaded.emit()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DuePatientsWidget()
    window.setWindowTitle("Patients with Due Amounts")
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())