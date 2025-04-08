from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QTableWidget, QTableWidgetItem, QScrollArea, QLabel, 
                            QPushButton, QFrame, QSplitter, QSizePolicy, QHeaderView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPalette, QFont
import pyqtgraph as pg
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from model.analysis_model import get_patient_demographics, get_patient_visit_frequency, get_inactive_patients, get_single_visit_patients
import pandas as pd
import qtawesome as qta

# Modern color palette - professional and calm
COLOR_PRIMARY = "#1e3d59"       # Dark blue
COLOR_SECONDARY = "#f5f5f5"     # Light gray
COLOR_ACCENT = "#3498db"        # Blue
COLOR_SUCCESS = "#27ae60"       # Green
COLOR_WARNING = "#f39c12"       # Amber
COLOR_DANGER = "#e74c3c"        # Red
COLOR_TEXT_LIGHT = "#ffffff"    # White
COLOR_TEXT_DARK = "#2c3e50"     # Dark slate
COLOR_BORDER = "#e0e0e0"        # Light border
COLOR_CHART_BG = "#ffffff"      # White background for charts
COLOR_HOVER = "#4a6fa5"         # Hover state

# Professional dashboard stylesheet
DASHBOARD_STYLESHEET = f"""
    QWidget {{
        background-color: {COLOR_SECONDARY};
        color: {COLOR_TEXT_DARK};
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    QLabel#header {{
        font-size: 24pt;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        padding: 5px;
    }}
    QLabel#subtitle {{
        font-size: 12pt;
        color: {COLOR_TEXT_DARK};
        padding-bottom: 10px;
    }}
    QPushButton#refreshBtn {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 10pt;
    }}
    QPushButton#refreshBtn:hover {{
        background-color: {COLOR_HOVER};
    }}
    QFrame#metricCard {{
        background-color: {COLOR_CHART_BG};
        border-radius: 6px;
        border: 1px solid {COLOR_BORDER};
    }}
    QLabel#cardTitle {{
        color: {COLOR_TEXT_DARK};
        font-size: 10pt;
        background: transparent;
        padding-top: 8px;
    }}
    QLabel#cardValue {{
        color: {COLOR_PRIMARY};
        font-size: 22pt;
        font-weight: bold;
        background: transparent;
    }}
    QLabel#cardIcon {{
        background: transparent;
    }}
    QLabel#sectionTitle {{
        font-size: 14pt;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        padding: 10px 0;
    }}
    QTableWidget {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        gridline-color: {COLOR_BORDER};
        font-size: 10pt;
        background-color: white;
        selection-background-color: {COLOR_ACCENT}40;
        selection-color: {COLOR_TEXT_DARK};
    }}
    QTableWidget::item {{
        padding: 5px;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    QHeaderView::section {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        padding: 8px;
        border: none;
        font-weight: bold;
    }}
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QFrame#chartFrame {{
        background-color: {COLOR_CHART_BG};
        border-radius: 6px;
        border: 1px solid {COLOR_BORDER};
        padding: 10px;
    }}
    QFrame#visitorsFrame {{
        background-color: {COLOR_CHART_BG};
        border-radius: 6px;
        border: 1px solid {COLOR_BORDER};
    }}
"""

class PatientAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Patient Analytics Dashboard")
        self.setMinimumSize(1200, 800)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header with welcome message
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        title_layout = QVBoxLayout()
        header = QLabel("Patient Analytics Dashboard", objectName="header")
        subtitle = QLabel("Monitor patient statistics and trends", objectName="subtitle")
        title_layout.addWidget(header)
        title_layout.addWidget(subtitle)
        
        refresh_btn = QPushButton(qta.icon('fa5s.sync', color=COLOR_TEXT_LIGHT), " Refresh Data", objectName="refreshBtn")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setIconSize(QSize(14, 14))
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        main_layout.addLayout(header_layout)

        # Overview Cards
        overview_label = QLabel("Overview", objectName="sectionTitle")
        main_layout.addWidget(overview_label)
        
        card_layout = QGridLayout()
        card_layout.setSpacing(15)
        self.cards = {}
        metrics = [
            ("Total Patients", "fa5s.users", COLOR_ACCENT, self.get_total_patients),
            ("Active Patients", "fa5s.user-check", COLOR_SUCCESS, self.get_active_patients),
            ("Single-Visit Patients", "fa5s.user-clock", COLOR_WARNING, self.get_single_visit_count),
            ("Inactive Patients", "fa5s.user-times", COLOR_DANGER, self.get_inactive_count),
        ]
        
        for i, (label, icon, color, func) in enumerate(metrics):
            frame = QFrame(objectName="metricCard")
            frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            frame.setFixedHeight(110)
            
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(15, 10, 15, 10)
            
            title_lbl = QLabel(label, objectName="cardTitle")
            value_lbl = QLabel("0", objectName="cardValue")
            
            icon_lbl = QLabel(objectName="cardIcon")
            icon_lbl.setPixmap(qta.icon(icon, color=color).pixmap(32, 32))
            
            title_row = QHBoxLayout()
            title_row.addWidget(icon_lbl)
            title_row.addWidget(title_lbl)
            title_row.addStretch()
            
            frame_layout.addLayout(title_row)
            frame_layout.addWidget(value_lbl)
            frame_layout.addStretch()
            
            card_layout.addWidget(frame, 0, i)
            self.cards[label] = (value_lbl, func)
        
        main_layout.addLayout(card_layout)

        # Main content area wrapped in scroll area for page scrolling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_content = QWidget()
        content_layout = QHBoxLayout(scroll_content)
        content_layout.setSpacing(15)

        # Left column - Demographics
        left_column = QVBoxLayout()
        demographics_label = QLabel("Patient Demographics", objectName="sectionTitle")
        left_column.addWidget(demographics_label)
        
        # Demographics charts
        demographics_frame = QFrame(objectName="chartFrame")
        demographics_layout = QHBoxLayout(demographics_frame)
        
        # Gender pie chart
        self.gender_canvas = FigureCanvas(plt.Figure(figsize=(5, 5)))
        self.gender_ax = self.gender_canvas.figure.add_subplot(111)
        self.gender_canvas.figure.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        # Disable wheel events on Matplotlib canvas
        self.gender_canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.gender_canvas.wheelEvent = lambda event: None  # Ignore wheel events

        # Age distribution chart
        self.age_plot = pg.PlotWidget()
        self.age_plot.setBackground(COLOR_CHART_BG)
        self.age_plot.showGrid(x=True, y=True, alpha=0.3)
        self.age_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.age_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.age_plot.setLabel('left', 'Patient Count')
        self.age_plot.setLabel('bottom', 'Age Group')
        # Disable wheel events on PyQtGraph plot
        self.age_plot.wheelEvent = lambda event: None  # Ignore wheel events

        demographics_layout.addWidget(self.gender_canvas)
        demographics_layout.addWidget(self.age_plot)
        left_column.addWidget(demographics_frame)
        
        # Right column - Visit Frequency with Chart and Table
        right_column = QVBoxLayout()
        visit_frequency_label = QLabel("Visit Frequency", objectName="sectionTitle")
        right_column.addWidget(visit_frequency_label)
        
        # Visit frequency frame containing both chart and table
        visit_frame = QFrame(objectName="visitorsFrame")
        visit_layout = QVBoxLayout(visit_frame)
        
        # Chart title
        chart_title = QLabel("Top 10 Most Frequent Visitors", objectName="cardTitle")
        visit_layout.addWidget(chart_title)
        
        # Chart
        self.visit_chart = pg.PlotWidget()
        self.visit_chart.setBackground(COLOR_CHART_BG)
        self.visit_chart.showGrid(x=True, y=True, alpha=0.3)
        self.visit_chart.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.visit_chart.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.visit_chart.setLabel('left', 'Visit Count')
        self.visit_chart.setLabel('bottom', 'Patient')
        self.visit_chart.setMaximumHeight(250)
        # Disable wheel events on PyQtGraph plot
        self.visit_chart.wheelEvent = lambda event: None  # Ignore wheel events

        visit_layout.addWidget(self.visit_chart)
        
        # Table title
        table_title = QLabel("Frequent Visitors Details", objectName="cardTitle")
        visit_layout.addWidget(table_title)
        
        # Visit frequency table
        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(7)
        self.visit_table.setHorizontalHeaderLabels([
            'Patient ID', 'Name', 'Visit Count', 'First Visit', 
            'Last Visit', 'Avg Days Between', 'Days Since Last'
        ])
        self.visit_table.verticalHeader().setVisible(False)
        self.visit_table.setAlternatingRowColors(True)
        self.visit_table.horizontalHeader().setStretchLastSection(True)
        self.visit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        visit_layout.addWidget(self.visit_table)
        
        right_column.addWidget(visit_frame)
                
        # Add columns to content layout
        content_layout.addLayout(left_column, 1)  # 50% width
        content_layout.addLayout(right_column, 1)  # 50% width
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Load data
        self.refresh_data()

    def refresh_data(self):
        for label, (value_lbl, func) in self.cards.items():
            value_lbl.setText(str(func()))
        self.load_demographics()
        self.load_visit_frequency()

    # Metrics
    def get_total_patients(self):
        data = get_patient_demographics()
        return sum(item['count'] for item in data['gender'])

    def get_active_patients(self):
        return self.get_total_patients() - self.get_inactive_count()

    def get_inactive_count(self):
        return len(get_inactive_patients())

    def get_single_visit_count(self):
        return len(get_single_visit_patients())

    def load_demographics(self):
        data = get_patient_demographics()
        
        # Gender Pie Chart
        gender_df = pd.DataFrame(data['gender'], columns=['gender', 'count'])
        self.gender_ax.clear()
        colors = [COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER]
        wedges, texts, autotexts = self.gender_ax.pie(
            gender_df['count'], 
            labels=gender_df['gender'], 
            autopct='%1.1f%%', 
            colors=colors[:len(gender_df)],
            startangle=90,
            wedgeprops={'width': 0.5, 'edgecolor': 'w', 'linewidth': 1}
        )
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_color('white')
        self.gender_ax.set_title('Gender Distribution', fontsize=12, pad=10)
        self.gender_canvas.draw()

        # Age Bar Chart
        age_df = pd.DataFrame(data['age'], columns=['age_group', 'count'])
        x = list(range(len(age_df)))
        brushes = [pg.mkBrush(COLOR_ACCENT) for _ in range(len(age_df))]
        self.age_plot.clear()
        self.age_plot.addItem(pg.BarGraphItem(x=x, height=age_df['count'], width=0.6, brushes=brushes))
        self.age_plot.getAxis('bottom').setTicks([[(i, a) for i, a in enumerate(age_df['age_group'])]])
        self.age_plot.setTitle('Age Distribution', color=COLOR_TEXT_DARK, size='12pt')

    def load_visit_frequency(self):
        data = get_patient_visit_frequency()
        top10 = sorted(data, key=lambda x: x['visit_count'], reverse=True)[:10]
        df = pd.DataFrame(top10)
        
        # Bar chart for top 10
        x = range(len(df))
        self.visit_chart.clear()
        self.visit_chart.addItem(pg.BarGraphItem(
            x=x, 
            height=df['visit_count'], 
            width=0.7, 
            brush=COLOR_ACCENT
        ))
        self.visit_chart.getAxis('bottom').setTicks([[(i, df.iloc[i]['name']) for i in x]])
        
        # Table for top frequent visitors
        self.visit_table.setRowCount(len(top10))
        for r, patient in enumerate(top10):
            self.visit_table.setItem(r, 0, QTableWidgetItem(str(patient['patient_id'])))
            
            # Make patient name bold
            name_item = QTableWidgetItem(patient['name'])
            name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.visit_table.setItem(r, 1, name_item)
            
            # Color code visit count based on frequency
            visit_count = patient['visit_count']
            visit_item = QTableWidgetItem(str(visit_count))
            if visit_count > 10:
                visit_item.setForeground(QColor(COLOR_SUCCESS))
                visit_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif visit_count > 5:
                visit_item.setForeground(QColor(COLOR_ACCENT))
            self.visit_table.setItem(r, 2, visit_item)
            
            # First and last visit dates
            self.visit_table.setItem(r, 3, QTableWidgetItem(patient.get('first_visit', 'N/A')))
            self.visit_table.setItem(r, 4, QTableWidgetItem(patient.get('last_visit', 'N/A')))
            
            # Average days between visits and days since last visit
            avg_days = patient.get('avg_days_between_visits')
            if avg_days is not None:
                self.visit_table.setItem(r, 5, QTableWidgetItem(f"{avg_days:.1f}"))
            else:
                self.visit_table.setItem(r, 5, QTableWidgetItem('N/A'))
                
            days_since = patient.get('days_since_last_visit')
            days_item = QTableWidgetItem(str(days_since) if days_since is not None else 'N/A')
            
            # Color code days since last visit
            if days_since is not None:
                if days_since > 90:
                    days_item.setForeground(QColor(COLOR_DANGER))
                elif days_since > 60:
                    days_item.setForeground(QColor(COLOR_WARNING))
                elif days_since < 30:
                    days_item.setForeground(QColor(COLOR_SUCCESS))
            
            self.visit_table.setItem(r, 6, days_item)
            
        self.visit_table.resizeColumnsToContents()