# ui/analysis/service_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QComboBox, QLabel
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from model.analysis_model import get_service_utilization, get_tooth_number_analysis, get_service_trends
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

class ServiceAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(ANALYSIS_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("Service Analytics")
        main_layout.addWidget(title)

        # Service Utilization
        utilization_widget = QWidget()
        utilization_layout = QHBoxLayout()
        utilization_widget.setLayout(utilization_layout)
        
        utilization_plot = pg.PlotWidget()
        utilization_plot.setTitle("Service Utilization", color=COLOR_TEXT_LIGHT, size="12pt")
        utilization_plot.setBackground(COLOR_SECONDARY)
        utilization_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        utilization_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        utilization_plot.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")
        
        utilization_layout.addWidget(utilization_plot)
        
        scroll_utilization = QScrollArea()
        scroll_utilization.setWidget(utilization_widget)
        scroll_utilization.setWidgetResizable(True)
        scroll_utilization.setFixedHeight(300)
        
        main_layout.addWidget(scroll_utilization)
        
        # Tooth Number Analysis Table
        tooth_table = QTableWidget()
        tooth_table.setMinimumHeight(250)
        
        scroll_tooth = QScrollArea()
        scroll_tooth.setWidget(tooth_table)
        scroll_tooth.setWidgetResizable(True)
        scroll_tooth.setFixedHeight(300)
        
        main_layout.addWidget(scroll_tooth)
        
        # Service Trends
        trends_widget = QWidget()
        trends_layout = QHBoxLayout()
        trends_widget.setLayout(trends_layout)
        
        period_combo = QComboBox()
        period_combo.addItems(['Day', 'Week', 'Month'])
        trends_layout.addWidget(period_combo)
        
        trends_plot = pg.PlotWidget()
        trends_plot.setTitle("Service Trends", color=COLOR_TEXT_LIGHT, size="12pt")
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
        self.load_service_utilization(utilization_plot)
        self.load_tooth_number(tooth_table)
        self.load_service_trends(trends_plot, 'month')
        period_combo.currentTextChanged.connect(lambda text: self.load_service_trends(trends_plot, text.lower()))

    def load_service_utilization(self, plot):
        data = get_service_utilization()
        df = pd.DataFrame(data)
        
        bar = pg.BarGraphItem(x=range(len(df)), height=df['usage_count'], width=0.6, brush=COLOR_ACCENT)
        plot.addItem(bar)
        plot.getAxis('bottom').setTicks([[(i, s) for i, s in enumerate(df['name'])]])
        
    def load_tooth_number(self, table):
        data = get_tooth_number_analysis()
        table.setRowCount(len(data))
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['Tooth Number', 'Treatment Count', 'Common Treatments'])
        
        for row, entry in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(str(entry['tooth_number'])))
            table.setItem(row, 1, QTableWidgetItem(str(entry['treatment_count'])))
            table.setItem(row, 2, QTableWidgetItem(entry['common_treatments']))
        
        table.resizeColumnsToContents()
        
    def load_service_trends(self, plot, period):
        plot.clear()
        data = get_service_trends(period)
        if not data:
            return
        
        df = pd.DataFrame(data)
        if df.empty:
            return
            
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)
        
        for service in df['service_name'].unique():
            service_data = df[df['service_name'] == service]
            x = service_data['x_index'].values
            y = service_data['usage_count'].values
            plot.plot(x, y, pen=pg.mkPen(color=COLOR_ACCENT, width=2), name=service)
        
        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setLabel('Time Period')
        plot.addLegend()

    def wheelEvent(self, event):
        event.ignore()