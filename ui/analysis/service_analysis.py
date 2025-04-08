# ui/analysis/service_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QComboBox
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from model.analysis_model import get_service_utilization, get_tooth_number_analysis, get_service_trends
import pandas as pd
import numpy as np

class ServiceAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Service Utilization
        utilization_widget = QWidget()
        utilization_layout = QHBoxLayout()
        utilization_widget.setLayout(utilization_layout)
        
        utilization_plot = pg.PlotWidget()
        utilization_plot.setTitle("Service Utilization", color="#ffffff", size="12pt")
        utilization_plot.setBackground("#1e1e2f")
        utilization_plot.getAxis('bottom').setPen(pg.mkPen("#ffffff"))
        utilization_plot.getAxis('left').setPen(pg.mkPen("#ffffff"))
        
        utilization_layout.addWidget(utilization_plot)
        
        scroll_utilization = QScrollArea()
        scroll_utilization.setWidget(utilization_widget)
        scroll_utilization.setWidgetResizable(True)
        scroll_utilization.setFixedHeight(300)
        
        main_layout.addWidget(scroll_utilization)
        
        # Tooth Number Analysis Table
        tooth_table = QTableWidget()
        tooth_table.setStyleSheet("""
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
        period_combo.setStyleSheet("background-color: #3e3e5f; color: #ffffff; padding: 5px;")
        trends_layout.addWidget(period_combo)
        
        trends_plot = pg.PlotWidget()
        trends_plot.setTitle("Service Trends", color="#ffffff", size="12pt")
        trends_plot.setBackground("#1e1e2f")
        trends_plot.getAxis('bottom').setPen(pg.mkPen("#ffffff"))
        trends_plot.getAxis('left').setPen(pg.mkPen("#ffffff"))
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
        
        bar = pg.BarGraphItem(x=range(len(df)), height=df['usage_count'], width=0.6, brush='#ab47bc')
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
            
        # Convert time periods to numerical indices
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)
        
        for service in df['service_name'].unique():
            service_data = df[df['service_name'] == service]
            x = service_data['x_index'].values
            y = service_data['usage_count'].values
            plot.plot(x, y, pen=pg.mkPen(color='#ab47bc', width=2), name=service)
        
        # Set custom ticks for x-axis
        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setLabel('Time Period')
        plot.addLegend()

    def wheelEvent(self, event):
        event.ignore()