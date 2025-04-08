# ui/analysis/operational_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QComboBox, QLabel
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from model.analysis_model import get_clinic_load_analysis, get_visit_trends
import pandas as pd
import numpy as np

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
    QComboBox {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        padding: 8px;
        border-radius: 4px;
    }}
    QComboBox:hover {{
        background-color: {COLOR_HOVER};
    }}
    QLabel {{
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
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("Operational Analytics")
        main_layout.addWidget(title)

        # Clinic Load
        load_widget = QWidget()
        load_layout = QHBoxLayout()
        load_widget.setLayout(load_layout)
        
        day_plot = pg.PlotWidget()
        day_plot.setTitle("Visits by Day of Week", color=COLOR_TEXT_LIGHT, size="12pt")
        day_plot.setBackground(COLOR_SECONDARY)
        day_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        day_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        day_plot.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")
        
        month_plot = pg.PlotWidget()
        month_plot.setTitle("Visits by Month", color=COLOR_TEXT_LIGHT, size="12pt")
        month_plot.setBackground(COLOR_SECONDARY)
        month_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        month_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        month_plot.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")
        
        load_layout.addWidget(day_plot)
        load_layout.addWidget(month_plot)
        
        scroll_load = QScrollArea()
        scroll_load.setWidget(load_widget)
        scroll_load.setWidgetResizable(True)
        scroll_load.setFixedHeight(300)
        
        main_layout.addWidget(scroll_load)
        
        # Visit Trends
        trends_widget = QWidget()
        trends_layout = QHBoxLayout()
        trends_widget.setLayout(trends_layout)
        
        period_combo = QComboBox()
        period_combo.addItems(['Day', 'Week', 'Month'])
        trends_layout.addWidget(period_combo)
        
        trends_plot = pg.PlotWidget()
        trends_plot.setTitle("Visit Trends", color=COLOR_TEXT_LIGHT, size="12pt")
        trends_plot.setBackground(COLOR_SECONDARY)
        trends_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        trends_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        trends_plot.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")
        trends_layout.addWidget(trends_plot)
        
        scroll_trends = QScrollArea()
        scroll_trends.setWidget(trends_widget)
        scroll_trends.setWidgetResizable(True)
        scroll_trends.setFixedHeight(300)
        
        main_layout.addWidget(scroll_trends)
        
        self.setLayout(main_layout)
        
        # Load Data
        self.load_clinic_load(day_plot, month_plot)
        self.load_visit_trends(trends_plot, 'month')
        period_combo.currentTextChanged.connect(lambda text: self.load_visit_trends(trends_plot, text.lower()))

    def load_clinic_load(self, day_plot, month_plot):
        data = get_clinic_load_analysis()
        
        day_df = pd.DataFrame(data['day_of_week'])
        month_df = pd.DataFrame(data['month'])
        
        day_bar = pg.BarGraphItem(x=range(len(day_df)), height=day_df['visit_count'], width=0.6, brush=COLOR_ACCENT)
        day_plot.addItem(day_bar)
        day_plot.getAxis('bottom').setTicks([[(i, d) for i, d in enumerate(day_df['day_name'])]])
        
        month_bar = pg.BarGraphItem(x=range(len(month_df)), height=month_df['visit_count'], width=0.6, brush=COLOR_ACCENT)
        month_plot.addItem(month_bar)
        month_plot.getAxis('bottom').setTicks([[(i, m) for i, m in enumerate(month_df['month_name'])]])
        
    def load_visit_trends(self, plot, period):
        plot.clear()
        data = get_visit_trends(period)
        if not data:
            return
            
        df = pd.DataFrame(data)
        if df.empty:
            return
            
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)
        
        x = df['x_index'].values
        plot.plot(x, df['visit_count'], pen=pg.mkPen(color=COLOR_ACCENT, width=2), name='Visits')
        
        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setLabel('Time Period')
        plot.addLegend()

    def wheelEvent(self, event):
        event.ignore()