import sys
import os
from pathlib import Path

# Add project root to path to enable imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QColor, QFont
import qtawesome as qta

# Use absolute/relative imports for the model
try:
    from model import due_model
except ImportError:
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(project_root))
    from model import due_model

# Premium Color Palette (aligned with PatientAnalysis)
COLOR_PRIMARY = "#1a2b4a"      # Deep Navy Blue (Headers, Titles)
COLOR_SECONDARY = "#f5f7fa"    # Soft Off-White (Background)
COLOR_SUCCESS = "#27ae60"      # Green (Success, Positive Metrics)
COLOR_WARNING = "#e67e22"      # Orange (Warnings, Medium Risk)
COLOR_DANGER = "#e74c3c"       # Red (Danger, Critical Conditions)
COLOR_ACCENT = "#00aaff"         # Purple (Optional Category)
COLOR_TEXT_LIGHT = "#ffffff"   # Pure White (Light Text)
COLOR_TEXT_DARK = "#1f2a44"     # Dark Slate (Body Text)
COLOR_TEXT_MUTED = "#7f8c8d"   # Muted Gray (Subtext)
COLOR_BORDER = "#d0d7de"       # Light Gray Border (UI Elements)
COLOR_CHART_BG = "#ffffff"     # White (Chart/Table Background)
COLOR_TABLE_ALT_ROW = "#f8f9f9" # Very Light Gray (Alternating Rows)
COLOR_HOVER = "#007acc"        # Darker Blue (Hover State)

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
        padding: 8px 12px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        font-size: 11pt;
        background-color: {COLOR_CHART_BG};
        font-family: 'Roboto', sans-serif;
    }}
    #DuePatientsWidget QLineEdit:focus {{
        border: 2px solid {COLOR_ACCENT};
    }}
    #DuePatientsWidget QPushButton#SearchBtn, #DuePatientsWidget QPushButton#RefreshBtn {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border: none;
        padding: 8px 15px;
        border-radius: 8px;
        font-size: 11pt;
        font-family: 'Roboto', sans-serif;
        min-width: 120px;

    }}
    #DuePatientsWidget QPushButton#SearchBtn:hover, #DuePatientsWidget QPushButton#RefreshBtn:hover {{
        background-color: {COLOR_HOVER};
    }}
    #DuePatientsWidget QPushButton:disabled {{
        background-color: #95a5a6;
        color: #ecf0f1;
    }}

    /* Card Styling (for overview cards) */
    #DuePatientsWidget QFrame#CardFrame {{
        background-color: {COLOR_CHART_BG};
        border-radius: 10px;
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
    designed to be used in a dashboard with modern overview cards.
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
                font-size: 26pt;
                font-weight: bold;
                color: {COLOR_PRIMARY};
                margin-bottom: 15px;
                font-family: 'Roboto', sans-serif;
            }}
        """)
        main_layout.addWidget(heading_label)

        # Header Frame
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # Search Section
        search_icon = qta.icon('fa5s.search', color=COLOR_TEXT_DARK)
        search_label = QLabel()
        search_label.setPixmap(search_icon.pixmap(QSize(18, 18)))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Patient ID, Name, or Phone...")
        self.search_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_input.setMinimumWidth(300)

        self.search_button = QPushButton(qta.icon('fa5s.search', color=COLOR_TEXT_LIGHT), " Search", objectName="SearchBtn")
        self.refresh_button = QPushButton(qta.icon('fa5s.sync', color=COLOR_TEXT_LIGHT), " Refresh", objectName="RefreshBtn")

        # Overview Cards (Inspired by PatientAnalysis)
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(10)
        self.cards = {}
        metrics = [
            ("Total Due Patients", "fa5s.users", COLOR_ACCENT, lambda: self.due_patients_count),
            ("Total Due Amount", "fa5s.money-bill", COLOR_ACCENT, lambda: f"{self.total_due_amount:,.2f}"),
        ]
        for text, icon, color, func in metrics:
            card = QFrame(objectName="CardFrame")
            card.setMinimumHeight(80)
            card.setMaximumWidth(200)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(15, 10, 15, 10)
            row = QHBoxLayout()
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon(icon, color=color).pixmap(24, 24))
            row.addWidget(icon_lbl)
            lbl = QLabel(text)
            lbl.setFont(QFont('Roboto', 10, QFont.Weight.Medium))
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
            row.addWidget(lbl)
            row.addStretch()
            layout.addLayout(row)
            val = QLabel("--")
            val.setFont(QFont('Roboto', 16, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {color};")
            layout.addWidget(val)
            self.cards[text] = (val, func)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 20))
            shadow.setOffset(0, 3)
            card.setGraphicsEffect(shadow)
            self.cards_layout.addWidget(card)
        self.cards_layout.addStretch()

        # Assemble header layout
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 1)
        header_layout.addWidget(self.search_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addLayout(self.cards_layout)
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

        # Initialize data variables
        self.due_patients_count = 0
        self.total_due_amount = 0.0

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
        patients_data = due_model.get_due_patients_details(search_term)

        self.due_table.setSortingEnabled(False)
        self.due_table.setRowCount(0)

        if patients_data is None:
            QMessageBox.critical(self, "Database Error", "Could not retrieve patient debt information. Please check logs.")
            self.update_cards_with_error()
            return
        else:
            self.due_table.setRowCount(len(patients_data))
            self.due_patients_count = len(patients_data)
            self.total_due_amount = 0.0
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
                self.total_due_amount += total_due
                due_item = QTableWidgetItem(f"PKR {total_due:,.2f}")
                due_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                self.due_table.setItem(row, 0, id_item)
                self.due_table.setItem(row, 1, name)
                self.due_table.setItem(row, 2, father_name)
                self.due_table.setItem(row, 3, phone)
                self.due_table.setItem(row, 4, address)
                self.due_table.setItem(row, 5, due_visits_item)
                self.due_table.setItem(row, 6, due_item)

            self.update_cards()

        self.due_table.setSortingEnabled(True)
        self.data_loaded.emit()

    def update_cards(self):
        """Update the overview cards with current data."""
        for text, (lbl, func) in self.cards.items():
            try:
                lbl.setText(str(func()))
            except:
                lbl.setText("N/A")

    def update_cards_with_error(self):
        """Set cards to error state if data loading fails."""
        for text, (lbl, _) in self.cards.items():
            lbl.setText("N/A")

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = DuePatientsWidget()
    window.setWindowTitle("Patients with Due Amounts")
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())
