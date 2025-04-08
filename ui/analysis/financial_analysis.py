# ui/analysis/financial_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QComboBox
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from model.analysis_model import get_revenue_analysis, get_price_deviation_analysis
import pandas as pd
import numpy as np

class FinancialAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Revenue Analysis
        revenue_widget = QWidget()
        revenue_layout = QHBoxLayout()
        revenue_widget.setLayout(revenue_layout)
        
        period_combo = QComboBox()
        period_combo.addItems(['Day', 'Week', 'Month'])
        period_combo.setStyleSheet("background-color: #3e3e5f; color: #ffffff; padding: 5px;")
        revenue_layout.addWidget(period_combo)
        
        revenue_plot = pg.PlotWidget()
        revenue_plot.setTitle("Revenue Trends", color="#ffffff", size="12pt")
        revenue_plot.setBackground("#1e1e2f")
        revenue_plot.getAxis('bottom').setPen(pg.mkPen("#ffffff"))
        revenue_plot.getAxis('left').setPen(pg.mkPen("#ffffff"))
        revenue_layout.addWidget(revenue_plot)
        
        scroll_revenue = QScrollArea()
        scroll_revenue.setWidget(revenue_widget)
        scroll_revenue.setWidgetResizable(True)
        scroll_revenue.setFixedHeight(300)
        
        main_layout.addWidget(scroll_revenue)
        
        # Price Deviation Table
        deviation_table = QTableWidget()
        deviation_table.setStyleSheet("""
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
            
        # Convert time periods to numerical indices
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)
        
        x = df['x_index'].values
        plot.plot(x, df['billed_amount'], pen=pg.mkPen(color='#42a5f5', width=2), name='Billed')
        plot.plot(x, df['collected_amount'], pen=pg.mkPen(color='#66bb6a', width=2), name='Collected')
        
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