# ui/analysis/patient_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, QScrollArea, QLabel, QPushButton, QTabWidget, QFrame, QSplitter
from PyQt6.QtCore import Qt, QSize
import pyqtgraph as pg
import qtawesome as qta
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from model.analysis_model import get_patient_demographics, get_patient_visit_frequency, get_inactive_patients, get_single_visit_patients
import pandas as pd

# Color constants
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_SUCCESS = "#27ae60"
COLOR_WARNING = "#f1c40f"
COLOR_DANGER = "#e74c3c"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

# Stylesheet
ANALYSIS_STYLESHEET = f"""
    QWidget {{
        background-color: {COLOR_SECONDARY};
        color: {COLOR_TEXT_DARK};
        font-family: 'Segoe UI', sans-serif;
    }}
    QLabel#title {{
        font-size: 18pt;
        font-weight: bold;
        color: {COLOR_PRIMARY};
    }}
    QPushButton#refreshBtn {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border-radius: 5px;
        padding: 5px 10px;
    }}
    QPushButton#refreshBtn:hover {{
        background-color: {COLOR_HOVER};
    }}
    QFrame#card {{
        background-color: {COLOR_PRIMARY};
        border-radius: 10px;
        padding: 15px;
    }}
    QLabel#cardTitle {{
        color: {COLOR_TEXT_LIGHT};
        font-size: 12pt;
        background: transparent;
    }}
    QLabel#cardValue {{
        color: {COLOR_TEXT_LIGHT};
        font-size: 24pt;
        font-weight: bold;
        background-color: {COLOR_ACCENT};
        padding: 5px;
        border-radius: 4px;
    }}
    QTabWidget::pane {{
        border: none;
    }}
    QTabBar::tab {{
        background: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        padding: 10px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }}
    QTabBar::tab:selected {{
        background: {COLOR_ACCENT};
    }}
    QTableWidget {{
        border: 1px solid {COLOR_BORDER};
        gridline-color: {COLOR_BORDER};
        font-size: 10pt;
        background-color: white;
    }}
    QTableWidget::item {{
        padding: 5px;
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
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        border: none;
        background: {COLOR_SECONDARY};
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar:horizontal {{
        border: none;
        background: {COLOR_SECONDARY};
        height: 8px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER};
        min-width: 20px;
        border-radius: 4px;
    }}
"""

class PatientAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(ANALYSIS_STYLESHEET)
        self.setWindowTitle("Patient Analytics Dashboard")
        self.setMinimumSize(1200, 800)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Patient Analytics Dashboard", objectName="title")
        refresh_btn = QPushButton(qta.icon('fa5s.sync', color=COLOR_TEXT_LIGHT), " Refresh", objectName="refreshBtn")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setIconSize(QSize(16, 16))
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        main_layout.addLayout(header_layout)

        # Summary Cards
        card_layout = QGridLayout()
        card_layout.setSpacing(10)
        self.cards = {}
        metrics = [
            ("Total Patients", "fa5s.users", COLOR_ACCENT, self.get_total_patients),
            ("Active Patients", "fa5s.user-check", COLOR_SUCCESS, self.get_active_patients),
            ("Inactive Patients", "fa5s.user-times", COLOR_DANGER, self.get_inactive_count),
            ("Single-Visit Patients", "fa5s.user-clock", COLOR_WARNING, self.get_single_visit_count),
        ]
        for i, (label, icon, color, func) in enumerate(metrics):
            frame = QFrame(objectName="card")
            frame_layout = QHBoxLayout(frame)
            icon_lbl = QLabel()
            icon_lbl.setStyleSheet("background: transparent;")
            icon_lbl.setPixmap(qta.icon(icon, color=COLOR_TEXT_LIGHT).pixmap(80, 80))
            text_layout = QVBoxLayout()
            title_lbl = QLabel(label, objectName="cardTitle")
            value_lbl = QLabel("0", objectName="cardValue")
            text_layout.addWidget(title_lbl)
            text_layout.addWidget(value_lbl)
            frame_layout.addWidget(icon_lbl)
            frame_layout.addLayout(text_layout)
            card_layout.addWidget(frame, 0, i)
            self.cards[label] = (value_lbl, func)
        main_layout.addLayout(card_layout)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_demographics_tab(), "Demographics")
        self.tabs.addTab(self.create_visit_tab(), "Visit Frequency")
        self.tabs.addTab(self.create_inactive_tab(), "Inactive Patients")
        main_layout.addWidget(self.tabs)

        # Load data
        self.refresh_data()

    def refresh_data(self):
        for label, (value_lbl, func) in self.cards.items():
            value_lbl.setText(str(func()))
        self.load_demographics()
        self.load_visit_frequency()
        self.load_inactive_data()

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

    # Demographics Tab
    def create_demographics_tab(self):
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        # Pie Chart for Gender
        self.gender_canvas = FigureCanvas(plt.Figure(figsize=(4,4)))
        self.gender_canvas.setMinimumWidth(400)
        self.gender_ax = self.gender_canvas.figure.add_subplot(111)

        # Bar Chart for Age
        self.age_plot = pg.PlotWidget()
        self.age_plot.setMinimumWidth(400)
        self.age_plot.setBackground(COLOR_SECONDARY)
        self.age_plot.showGrid(x=True, y=True, alpha=0.3)
        self.age_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.age_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.age_plot.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")

        splitter.addWidget(self.gender_canvas)
        splitter.addWidget(self.age_plot)
        splitter.setSizes([500,500])

        scroll = QScrollArea()
        scroll.setWidget(splitter)
        scroll.setWidgetResizable(False)
        scroll.setFixedHeight(450)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout = QVBoxLayout(tab)
        layout.addWidget(scroll)
        return tab

    def load_demographics(self):
        data = get_patient_demographics()
        # Gender Pie
        gender_df = pd.DataFrame(data['gender'], columns=['gender','count'])
        self.gender_ax.clear()
        colors = [COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER]
        self.gender_ax.pie(gender_df['count'], labels=gender_df['gender'], autopct='%1.1f%%', colors=colors[:len(gender_df)])
        self.gender_ax.set_title('Gender Distribution')
        self.gender_canvas.draw()

        # Age Bar
        age_df = pd.DataFrame(data['age'], columns=['age_group','count'])
        brushes = [pg.mkBrush(COLOR_ACCENT), pg.mkBrush(COLOR_SUCCESS), pg.mkBrush(COLOR_WARNING), pg.mkBrush(COLOR_DANGER), pg.mkBrush('#9b59b6')]
        x = list(range(len(age_df)))
        self.age_plot.clear()
        self.age_plot.addItem(pg.BarGraphItem(x=x, height=age_df['count'], width=0.6, brushes=brushes[:len(age_df)]))
        self.age_plot.getAxis('bottom').setTicks([[(i, a) for i,a in enumerate(age_df['age_group'])]])

    # Visit Frequency Tab
    def create_visit_tab(self):
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        # Chart
        self.visit_chart = pg.PlotWidget(title="Top 10 Frequent Visitors")
        self.visit_chart.setBackground(COLOR_SECONDARY)
        self.visit_chart.showGrid(x=True, y=True, alpha=0.3)
        self.visit_chart.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.visit_chart.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.visit_chart.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")

        # Table
        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(7)
        self.visit_table.setHorizontalHeaderLabels(['Patient ID','Name','Visit Count','First Visit','Last Visit','Avg Days','Days Since'])
        self.visit_table.verticalHeader().setVisible(False)
        self.visit_table.setAlternatingRowColors(True)
        scroll = QScrollArea()
        scroll.setWidget(self.visit_table)
        scroll.setWidgetResizable(True)

        splitter.addWidget(self.visit_chart)
        splitter.addWidget(scroll)
        splitter.setSizes([500,500])

        layout = QVBoxLayout(tab)
        layout.addWidget(splitter)
        return tab

    def load_visit_frequency(self):
        data = get_patient_visit_frequency()
        top10 = sorted(data, key=lambda x: x['visit_count'], reverse=True)[:10]
        df = pd.DataFrame(top10)
        colors = [COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, '#9b59b6']
        brushes = [pg.mkBrush(colors[i % len(colors)]) for i in range(len(df))]
        x = list(range(len(df)))
        self.visit_chart.clear()
        self.visit_chart.addItem(pg.BarGraphItem(x=x, height=df['visit_count'], width=0.6, brushes=brushes))
        self.visit_chart.getAxis('bottom').setTicks([[(i, df.iloc[i]['name']) for i in x]])

        self.visit_table.setRowCount(len(data))
        for r, e in enumerate(data):
            self.visit_table.setItem(r,0,QTableWidgetItem(str(e['patient_id'])))
            self.visit_table.setItem(r,1,QTableWidgetItem(e['name']))
            self.visit_table.setItem(r,2,QTableWidgetItem(str(e['visit_count'])))
            self.visit_table.setItem(r,3,QTableWidgetItem(e['first_visit'] or 'N/A'))
            self.visit_table.setItem(r,4,QTableWidgetItem(e['last_visit'] or 'N/A'))
            self.visit_table.setItem(r,5,QTableWidgetItem(str(e['avg_days_between_visits']) if e['avg_days_between_visits'] else 'N/A'))
            self.visit_table.setItem(r,6,QTableWidgetItem(str(e['days_since_last_visit']) if e['days_since_last_visit'] else 'N/A'))
        self.visit_table.resizeColumnsToContents()

    # Inactive Patients Tab
    def create_inactive_tab(self):
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        # Chart
        self.inactive_chart = pg.PlotWidget(title="Inactive by Duration")
        self.inactive_chart.setBackground(COLOR_SECONDARY)
        self.inactive_chart.showGrid(x=True, y=True, alpha=0.3)
        self.inactive_chart.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.inactive_chart.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.inactive_chart.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")

        # Table
        self.inactive_table = QTableWidget()
        self.inactive_table.setColumnCount(5)
        self.inactive_table.setHorizontalHeaderLabels(['ID','Name','Phone','Last Visit','Days Inactive'])
        self.inactive_table.verticalHeader().setVisible(False)
        self.inactive_table.setAlternatingRowColors(True)
        scroll2 = QScrollArea()
        scroll2.setWidget(self.inactive_table)
        scroll2.setWidgetResizable(True)

        splitter.addWidget(self.inactive_chart)
        splitter.addWidget(scroll2)
        splitter.setSizes([500,500])

        layout = QVBoxLayout(tab)
        layout.addWidget(splitter)
        return tab

    def load_inactive_data(self):
        data = get_inactive_patients()
        df = pd.DataFrame(data)
        if not df.empty and 'days_inactive' in df.columns:
            bins = [0,30,60,90,df['days_inactive'].max()+1]
            labels = ['0-30','31-60','61-90','90+']
            df['bucket'] = pd.cut(df['days_inactive'], bins=bins, labels=labels, right=False)
            counts = df['bucket'].value_counts().reindex(labels).fillna(0)
            colors = [COLOR_DANGER, COLOR_WARNING, COLOR_ACCENT, COLOR_SUCCESS]
            brushes = [pg.mkBrush(colors[i]) for i in range(len(labels))]
            x = list(range(len(labels)))
            self.inactive_chart.clear()
            self.inactive_chart.addItem(pg.BarGraphItem(x=x, height=counts.values.tolist(), width=0.6, brushes=brushes))
            self.inactive_chart.getAxis('bottom').setTicks([[(i, labels[i]) for i in x]])
        else:
            self.inactive_chart.clear()

        self.inactive_table.setRowCount(len(data))
        for r,e in enumerate(data):
            self.inactive_table.setItem(r,0,QTableWidgetItem(str(e['patient_id'])))
            self.inactive_table.setItem(r,1,QTableWidgetItem(e['name']))
            self.inactive_table.setItem(r,2,QTableWidgetItem(e.get('phone_number','N/A')))
            self.inactive_table.setItem(r,3,QTableWidgetItem(e.get('last_visit','')))
            self.inactive_table.setItem(r,4,QTableWidgetItem(str(round(e.get('days_inactive',0)))))
        self.inactive_table.resizeColumnsToContents()