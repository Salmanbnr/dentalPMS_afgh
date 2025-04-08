# ui/analysis/patient_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import qtawesome as qta
from model.analysis_model import get_patient_demographics, get_patient_visit_frequency, get_inactive_patients, get_single_visit_patients
import pandas as pd

class PatientAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Demographics Section
        demographics_widget = QWidget()
        demographics_layout = QHBoxLayout()
        demographics_widget.setLayout(demographics_layout)
        
        gender_plot = pg.PlotWidget()
        gender_plot.setTitle("Gender Distribution", color="#ffffff", size="12pt")
        gender_plot.setBackground("#1e1e2f")
        gender_plot.getAxis('bottom').setPen(pg.mkPen("#ffffff"))
        gender_plot.getAxis('left').setPen(pg.mkPen("#ffffff"))
        
        age_plot = pg.PlotWidget()
        age_plot.setTitle("Age Distribution", color="#ffffff", size="12pt")
        age_plot.setBackground("#1e1e2f")
        age_plot.getAxis('bottom').setPen(pg.mkPen("#ffffff"))
        age_plot.getAxis('left').setPen(pg.mkPen("#ffffff"))
        
        demographics_layout.addWidget(gender_plot)
        demographics_layout.addWidget(age_plot)
        
        scroll_demographics = QScrollArea()
        scroll_demographics.setWidget(demographics_widget)
        scroll_demographics.setWidgetResizable(True)
        scroll_demographics.setFixedHeight(300)
        
        main_layout.addWidget(scroll_demographics)
        
        # Visit Frequency Table
        visit_table = QTableWidget()
        visit_table.setStyleSheet("""
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
        visit_table.setMinimumHeight(250)
        
        scroll_visits = QScrollArea()
        scroll_visits.setWidget(visit_table)
        scroll_visits.setWidgetResizable(True)
        scroll_visits.setFixedHeight(300)
        
        main_layout.addWidget(scroll_visits)
        
        # Inactive Patients Table
        inactive_table = QTableWidget()
        inactive_table.setStyleSheet("""
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
        inactive_table.setMinimumHeight(250)
        
        scroll_inactive = QScrollArea()
        scroll_inactive.setWidget(inactive_table)
        scroll_inactive.setWidgetResizable(True)
        scroll_inactive.setFixedHeight(300)
        
        main_layout.addWidget(scroll_inactive)
        
        self.setLayout(main_layout)
        
        # Load Data
        self.load_demographics(gender_plot, age_plot)
        self.load_visit_frequency(visit_table)
        self.load_inactive_patients(inactive_table)

    def load_demographics(self, gender_plot, age_plot):
        data = get_patient_demographics()
        
        gender_df = pd.DataFrame(data['gender'], columns=['gender', 'count'])
        age_df = pd.DataFrame(data['age'], columns=['age_group', 'count'])
        
        gender_bar = pg.BarGraphItem(x=range(len(gender_df)), height=gender_df['count'], width=0.6, brush='#42a5f5')
        gender_plot.addItem(gender_bar)
        gender_plot.getAxis('bottom').setTicks([[(i, g) for i, g in enumerate(gender_df['gender'])]])
        
        age_bar = pg.BarGraphItem(x=range(len(age_df)), height=age_df['count'], width=0.6, brush='#66bb6a')
        age_plot.addItem(age_bar)
        age_plot.getAxis('bottom').setTicks([[(i, a) for i, a in enumerate(age_df['age_group'])]])
        
    def load_visit_frequency(self, table):
        data = get_patient_visit_frequency()
        table.setRowCount(len(data))
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(['Patient ID', 'Name', 'Visit Count', 'First Visit', 'Last Visit', 'Avg Days Between', 'Days Since Last'])
        
        for row, entry in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(str(entry['patient_id'])))
            table.setItem(row, 1, QTableWidgetItem(entry['name']))
            table.setItem(row, 2, QTableWidgetItem(str(entry['visit_count'])))
            table.setItem(row, 3, QTableWidgetItem(entry['first_visit'] or 'N/A'))
            table.setItem(row, 4, QTableWidgetItem(entry['last_visit'] or 'N/A'))
            table.setItem(row, 5, QTableWidgetItem(str(entry['avg_days_between_visits']) if entry['avg_days_between_visits'] else 'N/A'))
            table.setItem(row, 6, QTableWidgetItem(str(entry['days_since_last_visit']) if entry['days_since_last_visit'] else 'N/A'))
        
        table.resizeColumnsToContents()
        
    def load_inactive_patients(self, table):
        data = get_inactive_patients()
        table.setRowCount(len(data))
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Patient ID', 'Name', 'Phone', 'Last Visit', 'Days Inactive'])
        
        for row, entry in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(str(entry['patient_id'])))
            table.setItem(row, 1, QTableWidgetItem(entry['name']))
            table.setItem(row, 2, QTableWidgetItem(entry['phone_number'] or 'N/A'))
            table.setItem(row, 3, QTableWidgetItem(entry['last_visit']))
            table.setItem(row, 4, QTableWidgetItem(str(round(entry['days_inactive']))))
        
        table.resizeColumnsToContents()

    def wheelEvent(self, event):
        event.ignore()