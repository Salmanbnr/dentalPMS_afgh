from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QTableWidget, QTableWidgetItem, QScrollArea, QLabel,
                            QPushButton, QFrame, QComboBox, QSizePolicy, QHeaderView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
import pyqtgraph as pg
import pandas as pd
import numpy as np
import qtawesome as qta

from model.analysis_model import get_service_trends, get_service_utilization, get_tooth_number_analysis

# Modern color palette - matching the patient dashboard
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_SUCCESS = "#27ae60"
COLOR_WARNING = "#f39c12"
COLOR_DANGER = "#e74c3c"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_CHART_BG = "#ffffff"
COLOR_HOVER = "#4a6fa5"

# Adjusted colors for better visibility
PIE_COLORS = ['#4f81bd', '#c0504d', '#9bbb59', '#f79646', '#8064a2']

ANALYSIS_STYLESHEET = f"""
    QWidget {{
        background-color: {COLOR_SECONDARY};
        color: {COLOR_TEXT_DARK};
        font-family: 'Segoe UI', 'Arial', sans-serif;
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
    QComboBox {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border-radius: 4px;
        padding: 8px;
        font-size: 10pt;
    }}
    QComboBox:hover {{
        background-color: {COLOR_HOVER};
    }}
"""

class ServiceAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(ANALYSIS_STYLESHEET)
        self.setWindowTitle("Service Analysis")
        self.setMinimumSize(1200, 800)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)

        refresh_btn = QPushButton(qta.icon('fa5s.sync', color=COLOR_TEXT_LIGHT), " Refresh Data", objectName="refreshBtn")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setIconSize(QSize(14, 14))

        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        main_layout.addLayout(header_layout)

        # Main content area wrapped in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_content = QWidget()
        content_layout = QHBoxLayout(scroll_content)
        content_layout.setSpacing(15)

        # Left column - Service Utilization and Tooth Analysis
        left_column = QVBoxLayout()

        # Service Utilization Chart
        utilization_frame = QFrame(objectName="chartFrame")
        utilization_layout = QVBoxLayout(utilization_frame)
        self.utilization_plot = pg.PlotWidget()
        self.utilization_plot.setBackground(COLOR_CHART_BG)
        self.utilization_plot.showGrid(x=True, y=True, alpha=0.3)
        self.utilization_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.utilization_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.utilization_plot.setLabel('left', 'Usage Count')
        self.utilization_plot.setLabel('bottom', 'Service')
        self.utilization_plot.setMaximumHeight(300)
        self.utilization_plot.setMouseEnabled(x=False, y=False)
        utilization_layout.addWidget(self.utilization_plot)
        left_column.addWidget(utilization_frame)

        # Tooth Number Analysis Table
        tooth_frame = QFrame(objectName="chartFrame")
        tooth_layout = QVBoxLayout(tooth_frame)
        self.tooth_table = QTableWidget()
        self.tooth_table.setColumnCount(3)
        self.tooth_table.setHorizontalHeaderLabels(['Tooth Number', 'Treatment Count', 'Common Treatments'])
        self.tooth_table.verticalHeader().setVisible(False)
        self.tooth_table.setAlternatingRowColors(True)
        self.tooth_table.horizontalHeader().setStretchLastSection(True)
        self.tooth_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tooth_table.setMinimumHeight(240)
        tooth_layout.addWidget(self.tooth_table)
        left_column.addWidget(tooth_frame)

        # Right column - Service Trends
        right_column = QVBoxLayout()
        trends_frame = QFrame(objectName="chartFrame")
        trends_layout = QVBoxLayout(trends_frame)

        period_combo = QComboBox(objectName="periodCombo")
        period_combo.addItems(['Day', 'Week', 'Month'])
        period_combo.currentTextChanged.connect(lambda text: self.load_service_trends(self.trends_plot, text.lower()))
        trends_layout.addWidget(period_combo)

        self.trends_plot = pg.PlotWidget()
        self.trends_plot.setBackground(COLOR_CHART_BG)
        self.trends_plot.showGrid(x=True, y=True, alpha=0.3)
        self.trends_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.trends_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.trends_plot.setLabel('left', 'Usage Count')
        self.trends_plot.setLabel('bottom', 'Time Period')
        self.trends_plot.setMaximumHeight(300)
        self.trends_plot.setMouseEnabled(x=False, y=False)
        trends_layout.addWidget(self.trends_plot)

        trends_frame.setLayout(trends_layout)
        right_column.addWidget(trends_frame)

        # Add columns to content layout
        content_layout.addLayout(left_column, 1)
        content_layout.addLayout(right_column, 1)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.refresh_data()

    def refresh_data(self):
        self.load_service_utilization(self.utilization_plot)
        self.load_tooth_number(self.tooth_table)
        self.load_service_trends(self.trends_plot, 'month')

    def load_service_utilization(self, plot):
        data = get_service_utilization()
        df = pd.DataFrame(data)
        bar = pg.BarGraphItem(x=range(len(df)), height=df['usage_count'], width=0.6, brush=COLOR_ACCENT)
        plot.clear()
        plot.addItem(bar)
        plot.getAxis('bottom').setTicks([[(i, str(s)) for i, s in enumerate(df['name'])]])
        plot.getAxis('bottom').setStyle(tickTextOffset=10)
        plot.setTitle("Service Utilization", color=COLOR_TEXT_DARK, size="12pt")

    def load_tooth_number(self, table):
        data = get_tooth_number_analysis()
        table.setRowCount(len(data))
        for row, entry in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(str(entry['tooth_number'])))
            table.setItem(row, 1, QTableWidgetItem(str(entry['treatment_count'])))
            table.setItem(row, 2, QTableWidgetItem(entry['common_treatments']))
        table.resizeColumnsToContents()

    def load_service_trends(self, plot, period):
        plot.clear()
        data = get_service_trends(period)
        if not data or pd.DataFrame(data).empty:
            return

        df = pd.DataFrame(data)
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)

        for i, service in enumerate(df['service_name'].unique()):
            service_data = df[df['service_name'] == service]
            x = service_data['x_index'].values
            y = service_data['usage_count'].values
            plot.plot(x, y, pen=pg.mkPen(color=PIE_COLORS[i % len(PIE_COLORS)], width=2), name=service)

        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.setTitle(f"Service Trends ({period.capitalize()})", color=COLOR_TEXT_DARK, size="12pt")
        plot.addLegend()
