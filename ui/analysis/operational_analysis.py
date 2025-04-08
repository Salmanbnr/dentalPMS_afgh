# ui/analysis/operational_analysis.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QTableWidget, QTableWidgetItem, QScrollArea, QLabel,
                            QPushButton, QFrame, QComboBox, QSizePolicy, QHeaderView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
import pyqtgraph as pg
import pandas as pd
import numpy as np
import qtawesome as qta

from model.analysis_model import get_clinic_load_analysis, get_visit_trends

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
    QLabel#titleLabel {{
        font-size: 18pt;
        font-weight: bold;
        color: {COLOR_PRIMARY};
        margin-bottom: 10px;
    }}
"""

class OperationalAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(ANALYSIS_STYLESHEET)
        self.setWindowTitle("Operational Analysis")
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

        # Title
        title = QLabel("Operational Analytics", objectName="titleLabel")
        main_layout.addWidget(title)

        # Main content area wrapped in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_content = QWidget()
        content_layout = QHBoxLayout(scroll_content)
        content_layout.setSpacing(15)

        # Left column - Clinic Load (Visits by Day and Month)
        left_column = QVBoxLayout()

        load_frame = QFrame(objectName="chartFrame")
        load_layout = QHBoxLayout(load_frame)

        self.day_plot = pg.PlotWidget()
        self.day_plot.setBackground(COLOR_CHART_BG)
        self.day_plot.showGrid(x=True, y=True, alpha=0.3)
        self.day_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.day_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.day_plot.setLabel('left', 'Visit Count')
        self.day_plot.setLabel('bottom', 'Day of Week')
        self.day_plot.setMaximumHeight(300)
        self.day_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        load_layout.addWidget(self.day_plot)

        self.month_plot = pg.PlotWidget()
        self.month_plot.setBackground(COLOR_CHART_BG)
        self.month_plot.showGrid(x=True, y=True, alpha=0.3)
        self.month_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.month_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.month_plot.setLabel('left', 'Visit Count')
        self.month_plot.setLabel('bottom', 'Month')
        self.month_plot.setMaximumHeight(300)
        self.month_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        load_layout.addWidget(self.month_plot)

        load_frame.setLayout(load_layout)
        left_column.addWidget(load_frame)

        # Right column - Visit Trends
        right_column = QVBoxLayout()

        trends_frame = QFrame(objectName="chartFrame")
        trends_layout = QVBoxLayout(trends_frame)

        period_combo = QComboBox(objectName="periodCombo")
        period_combo.addItems(['Day', 'Week', 'Month'])
        period_combo.currentTextChanged.connect(lambda text: self.load_visit_trends(self.trends_plot, text.lower()))
        trends_layout.addWidget(period_combo)

        self.trends_plot = pg.PlotWidget()
        self.trends_plot.setBackground(COLOR_CHART_BG)
        self.trends_plot.showGrid(x=True, y=True, alpha=0.3)
        self.trends_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.trends_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.trends_plot.setLabel('left', 'Visit Count')
        self.trends_plot.setLabel('bottom', 'Time Period')
        self.trends_plot.setMaximumHeight(300)
        self.trends_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
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
        self.load_clinic_load(self.day_plot, self.month_plot)
        self.load_visit_trends(self.trends_plot, 'month')

    def load_clinic_load(self, day_plot, month_plot):
        data = get_clinic_load_analysis()
        
        day_df = pd.DataFrame(data['day_of_week'])
        month_df = pd.DataFrame(data['month'])
        
        day_bar = pg.BarGraphItem(x=range(len(day_df)), height=day_df['visit_count'], width=0.6, brush=COLOR_ACCENT)
        day_plot.clear()
        day_plot.addItem(day_bar)
        day_plot.getAxis('bottom').setTicks([[(i, d) for i, d in enumerate(day_df['day_name'])]])
        day_plot.getAxis('bottom').setStyle(tickTextOffset=10)
        day_plot.setTitle("Visits by Day of Week", color=COLOR_TEXT_DARK, size="12pt")

        month_bar = pg.BarGraphItem(x=range(len(month_df)), height=month_df['visit_count'], width=0.6, brush=COLOR_ACCENT)
        month_plot.clear()
        month_plot.addItem(month_bar)
        month_plot.getAxis('bottom').setTicks([[(i, m) for i, m in enumerate(month_df['month_name'])]])
        month_plot.getAxis('bottom').setStyle(tickTextOffset=10)
        month_plot.setTitle("Visits by Month", color=COLOR_TEXT_DARK, size="12pt")

    def load_visit_trends(self, plot, period):
        plot.clear()
        data = get_visit_trends(period)
        if not data or pd.DataFrame(data).empty:
            return

        df = pd.DataFrame(data)
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)

        x = df['x_index'].values
        plot.plot(x, df['visit_count'], pen=pg.mkPen(color=COLOR_ACCENT, width=2), name='Visits')

        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setStyle(tickTextOffset=10)
        plot.setTitle(f"Visit Trends ({period.capitalize()})", color=COLOR_TEXT_DARK, size="12pt")
        plot.addLegend()

    def wheelEvent(self, event):
        event.ignore()  # Disable wheel scroll for the entire widget