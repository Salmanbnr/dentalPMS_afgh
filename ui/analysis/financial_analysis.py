# ui/analysis/financial_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QComboBox, QLabel
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from model.analysis_model import get_revenue_analysis, get_price_deviation_analysis
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

class FinancialAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(ANALYSIS_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("Financial Analytics")
        main_layout.addWidget(title)

        # Revenue Analysis
        revenue_widget = QWidget()
        revenue_layout = QHBoxLayout()
        revenue_widget.setLayout(revenue_layout)
        
        period_combo = QComboBox()
        period_combo.addItems(['Day', 'Week', 'Month'])
        revenue_layout.addWidget(period_combo)
        
        revenue_plot = pg.PlotWidget()
        revenue_plot.setTitle("Revenue Trends", color=COLOR_TEXT_LIGHT, size="12pt")
        revenue_plot.setBackground(COLOR_SECONDARY)
        revenue_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        revenue_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        revenue_plot.setStyleSheet(f"border: 1px solid {COLOR_BORDER}; border-radius: 4px;")
        revenue_layout.addWidget(revenue_plot)
        
        scroll_revenue = QScrollArea()
        scroll_revenue.setWidget(revenue_widget)
        scroll_revenue.setWidgetResizable(True)
        scroll_revenue.setFixedHeight(300)
        
        main_layout.addWidget(scroll_revenue)
        
        # Price Deviation Table
        deviation_table = QTableWidget()
        deviation_table.setMinimumHeight(250)
        
        scroll_deviation = QScrollArea()
        scroll_deviation.setWidget(deviation_table)
        scroll_deviation.setWidgetResizable(True)
        scroll_deviation.setFixedHeight(300)
        
        main_layout.addWidget(scroll_deviation)
        
        self.setLayout(main_layout)
        
        # Load Data
        self.load_revenue_analysis(revenue_plot, 'month')
        self.load_price_deviation(deviation_table)
        period_combo.currentTextChanged.connect(lambda text: self.load_revenue_analysis(revenue_plot, text.lower()))

    def load_revenue_analysis(self, plot, period):
        plot.clear()
        data = get_revenue_analysis(period)
        if not data:
            return
            
        df = pd.DataFrame(data)
        if df.empty:
            return
            
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)
        
        x = df['x_index'].values
        plot.plot(x, df['billed_amount'], pen=pg.mkPen(color=COLOR_ACCENT, width=2), name='Billed')
        plot.plot(x, df['collected_amount'], pen=pg.mkPen(color='#27ae60', width=2), name='Collected')
        
        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setLabel('Time Period')
        plot.addLegend()
        
    def load_price_deviation(self, table):
        data = get_price_deviation_analysis()
        services = data['services']
        meds = data['medications']
        
        table.setRowCount(len(services) + len(meds))
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Name', 'Default Price', 'Avg Charged', 'Avg Deviation', 'Count'])
        
        for row, entry in enumerate(services):
            table.setItem(row, 0, QTableWidgetItem(entry['name']))
            table.setItem(row, 1, QTableWidgetItem(str(entry['default_price'])))
            table.setItem(row, 2, QTableWidgetItem(str(round(entry['avg_charged'], 2))))
            table.setItem(row, 3, QTableWidgetItem(str(round(entry['avg_deviation'], 2))))
            table.setItem(row, 4, QTableWidgetItem(str(entry['count'])))
        
        for row, entry in enumerate(meds, len(services)):
            table.setItem(row, 0, QTableWidgetItem(entry['name']))
            table.setItem(row, 1, QTableWidgetItem(str(entry['default_price'])))
            table.setItem(row, 2, QTableWidgetItem(str(round(entry['avg_charged'], 2))))
            table.setItem(row, 3, QTableWidgetItem(str(round(entry['avg_deviation'], 2))))
            table.setItem(row, 4, QTableWidgetItem(str(entry['count'])))
        
        table.resizeColumnsToContents()

    def wheelEvent(self, event):
        event.ignore()