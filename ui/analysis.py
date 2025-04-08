# ui/analysis/operational_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QComboBox
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from model.analysis_model import get_clinic_load_analysis, get_visit_trends
import pandas as pd
import numpy as np

class OperationalAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Clinic Load
        load_widget = QWidget()
        load_layout = QHBoxLayout()
        load_widget.setLayout(load_layout)
        
        day_plot = pg.PlotWidget()
        day_plot.setTitle("Visits by Day of Week", color="#ffffff", size="12pt")
        day_plot.setBackground("#1e1e2f")
        day_plot.getAxis('bottom').setPen(pg.mkPen("#ffffff"))
        day_plot.getAxis('left').setPen(pg.mkPen("#ffffff"))
        
        month_plot = pg.PlotWidget()
        month_plot.setTitle("Visits by Month", color="#ffffff", size="12pt")
        month_plot.setBackground("#1e1e2f")
        month_plot.getAxis('bottom').setPen(pg.mkPen("#ffffff"))
        month_plot.getAxis('left').setPen(pg.mkPen("#ffffff"))
        
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
        period_combo.setStyleSheet("background-color: #3e3e5f; color: #ffffff; padding: 5px;")
        trends_layout.addWidget(period_combo)
        
        trends_plot = pg.PlotWidget()
        trends_plot.setTitle("Visit Trends", color="#ffffff", size="12pt")
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
        self.load_clinic_load(day_plot, month_plot)
        self.load_visit_trends(trends_plot, 'month')
        period_combo.currentTextChanged.connect(lambda text: self.load_visit_trends(trends_plot, text.lower()))

    def load_clinic_load(self, day_plot, month_plot):
        data = get_clinic_load_analysis()
        
        day_df = pd.DataFrame(data['day_of_week'])
        month_df = pd.DataFrame(data['month'])
        
        day_bar = pg.BarGraphItem(x=range(len(day_df)), height=day_df['visit_count'], width=0.6, brush='#ab47bc')
        day_plot.addItem(day_bar)
        day_plot.getAxis('bottom').setTicks([[(i, d) for i, d in enumerate(day_df['day_name'])]])
        
        month_bar = pg.BarGraphItem(x=range(len(month_df)), height=month_df['visit_count'], width=0.6, brush='#ff7043')
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
            
        # Convert time periods to numerical indices
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)
        
        x = df['x_index'].values
        plot.plot(x, df['visit_count'], pen=pg.mkPen(color='#42a5f5', width=2), name='Visits')
        
        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setLabel('Time Period')
        plot.addLegend()

    def wheelEvent(self, event):
        event.ignore()