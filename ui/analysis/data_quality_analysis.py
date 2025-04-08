# ui/analysis/data_quality_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt6.QtCore import Qt
from model.analysis_model import get_data_quality_issues

class DataQualityAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Duplicate Patients Table
        duplicate_table = QTableWidget()
        duplicate_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d44;
                color: #ffffff;
                border: 1px solid #3e3e5f;
                border-radius: 5px;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #3e3e5f;
                padding: 8px;
                border: none;
                color: #ffffff;
            }
        """)
        duplicate_table.setMinimumHeight(250)
        
        scroll_duplicate = QScrollArea()
        scroll_duplicate.setWidget(duplicate_table)
        scroll_duplicate.setWidgetResizable(True)
        scroll_duplicate.setFixedHeight(300)
        
        main_layout.addWidget(scroll_duplicate)
        
        # Visits Without Items Table
        visits_table = QTableWidget()
        visits_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d44;
                color: #ffffff;
                border: 1px solid #3e3e5f;
                border-radius: 5px;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #3e3e5f;
                padding: 8px;
                border: none;
                color: #ffffff;
            }
        """)
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