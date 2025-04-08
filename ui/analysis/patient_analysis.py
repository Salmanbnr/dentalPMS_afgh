# ui/analysis/patient_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QLabel
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import qtawesome as qta
from model.analysis_model import get_patient_demographics, get_patient_visit_frequency, get_inactive_patients, get_single_visit_patients
import pandas as pd

# Color constants
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

class PatientAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(ANALYSIS_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("Patient Analytics")
        main_layout.addWidget(title)

        # Demographics Section
        demographics_widget = QWidget()
        demographics_layout = QHBoxLayout()
        demographics_widget.setLayout(demographics_layout)
        
        gender_plot = pg.PlotWidget()
        gender_plot.setTitle("Gender Distribution", color=COLOR_TEXT_LIGHT, size="12pt")
        gender_plot.setBackground(COLOR_SECONDARY)
        gender_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        gender_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        gender_plot.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")
        
        age_plot = pg.PlotWidget()
        age_plot.setTitle("Age Distribution", color=COLOR_TEXT_LIGHT, size="12pt")
        age_plot.setBackground(COLOR_SECONDARY)
        age_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        age_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        age_plot.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")
        
        demographics_layout.addWidget(gender_plot)
        demographics_layout.addWidget(age_plot)
        
        scroll_demographics = QScrollArea()
        scroll_demographics.setWidget(demographics_widget)
        scroll_demographics.setWidgetResizable(True)
        scroll_demographics.setFixedHeight(300)
        
        main_layout.addWidget(scroll_demographics)
        
        # Visit Frequency Table
        visit_table = QTableWidget()
        visit_table.setMinimumHeight(250)
        
        scroll_visits = QScrollArea()
        scroll_visits.setWidget(visit_table)
        scroll_visits.setWidgetResizable(True)
        scroll_visits.setFixedHeight(300)
        
        main_layout.addWidget(scroll_visits)
        
        # Inactive Patients Table
        inactive_table = QTableWidget()
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
        
        gender_bar = pg.BarGraphItem(x=range(len(gender_df)), height=gender_df['count'], width=0.6, brush=COLOR_ACCENT)
        gender_plot.addItem(gender_bar)
        gender_plot.getAxis('bottom').setTicks([[(i, g) for i, g in enumerate(gender_df['gender'])]])
        
        age_bar = pg.BarGraphItem(x=range(len(age_df)), height=age_df['count'], width=0.6, brush=COLOR_ACCENT)
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

    # def wheelEvent(self, event):
    #     event.ignore()