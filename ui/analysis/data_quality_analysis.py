# ui/analysis/data_quality_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QLabel
from PyQt6.QtCore import Qt
from model.analysis_model import get_data_quality_issues

COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

ANALYSIS_STYLESHEET = f"""
    QWidget {{
        background-color: {COLOR_SECONDARY};
        padding: 15px;
    }}
    QTableWidget {{
        border: 1px solid {COLOR_BORDER};
        gridline-color: {COLOR_BORDER};
        font-size: 10pt;
        background-color: white;
    }}
    QTableWidget::item {{
        padding: 5px;
        color: {COLOR_TEXT_DARK};
    }}
    QTableWidget::item:selected {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
    }}
    QHeaderView::section {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        padding: 6px;
        border: none;
        font-weight: bold;
    }}
    QScrollArea {{
        border: none;
        background-color: {COLOR_SECONDARY};
    }}
    QScrollBar:vertical {{
        border: none;
        background: {COLOR_SECONDARY};
        width: 10px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar:horizontal {{
        border: none;
        background: {COLOR_SECONDARY};
        height: 10px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER};
        min-width: 20px;
        border-radius: 5px;
    }}
    QLabel {{
        font-size: 18pt;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        margin-bottom: 10px;
    }}
"""

class DataQualityAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(ANALYSIS_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("Data Quality Analytics")
        main_layout.addWidget(title)

        # Duplicate Patients Table
        duplicate_table = QTableWidget()
        duplicate_table.setMinimumHeight(250)
        
        scroll_duplicate = QScrollArea()
        scroll_duplicate.setWidget(duplicate_table)
        scroll_duplicate.setWidgetResizable(True)
        scroll_duplicate.setFixedHeight(300)
        
        main_layout.addWidget(scroll_duplicate)
        
        # Visits Without Items Table
        visits_table = QTableWidget()
        visits_table.setMinimumHeight(250)
        
        scroll_visits = QScrollArea()
        scroll_visits.setWidget(visits_table)
        scroll_visits.setWidgetResizable(True)
        scroll_visits.setFixedHeight(300)
        
        main_layout.addWidget(scroll_visits)
        
        self.setLayout(main_layout)
        
        # Load Data
        self.load_data_quality(duplicate_table, visits_table)

    def load_data_quality(self, duplicate_table, visits_table):
        data = get_data_quality_issues()
        
        # Duplicate Patients
        duplicates = data['duplicate_patients']
        duplicate_table.setRowCount(len(duplicates))
        duplicate_table.setColumnCount(4)
        duplicate_table.setHorizontalHeaderLabels(['Patient ID', 'Name', 'Phone', 'Gender'])
        
        for row, entry in enumerate(duplicates):
            duplicate_table.setItem(row, 0, QTableWidgetItem(str(entry['patient_id'])))
            duplicate_table.setItem(row, 1, QTableWidgetItem(entry['name']))
            duplicate_table.setItem(row, 2, QTableWidgetItem(entry['phone_number'] or 'N/A'))
            duplicate_table.setItem(row, 3, QTableWidgetItem(entry['gender'] or 'N/A'))
        
        duplicate_table.resizeColumnsToContents()
        
        # Visits Without Items
        visits = data['visits_without_items']
        visits_table.setRowCount(len(visits))
        visits_table.setColumnCount(5)
        visits_table.setHorizontalHeaderLabels(['Visit ID', 'Patient Name', 'Visit Date', 'Total Amount', 'Paid Amount'])
        
        for row, entry in enumerate(visits):
            visits_table.setItem(row, 0, QTableWidgetItem(str(entry['visit_id'])))
            visits_table.setItem(row, 1, QTableWidgetItem(entry['patient_name']))
            visits_table.setItem(row, 2, QTableWidgetItem(entry['visit_date']))
            visits_table.setItem(row, 3, QTableWidgetItem(str(entry['total_amount'])))
            visits_table.setItem(row, 4, QTableWidgetItem(str(entry['paid_amount'])))
        
        visits_table.resizeColumnsToContents()

    def wheelEvent(self, event):
        event.ignore()