# ui/analysis/medication_analysis.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QScrollArea, QComboBox
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from model.analysis_model import get_medication_utilization, get_medication_trends
import pandas as pd
import numpy as np

class MedicationAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Medication Utilization
        utilization_widget = QWidget()
        utilization_layout = QHBoxLayout()
        utilization_widget.setLayout(utilization_layout)
        
        utilization_plot = pg.PlotWidget()
        utilization_plot.setTitle("Medication Utilization", color="#ffffff", size="12pt")
        utilization_plot.setBackground("#1e1e2f")
        utilization_plot.getAxis('bottom').setPen(pg.mkPen("#ffffff"))
        utilization_plot.getAxis('left').setPen(pg.mkPen("#ffffff"))
        
        utilization_layout.addWidget(utilization_plot)
        
        scroll_utilization = QScrollArea()
        scroll_utilization.setWidget(utilization_widget)
        scroll_utilization.setWidgetResizable(True)
        scroll_utilization.setFixedHeight(300)
        
        main_layout.addWidget(scroll_utilization)
        
        # Medication Trends
        trends_widget = QWidget()
        trends_layout = QHBoxLayout()
        trends_widget.setLayout(trends_layout)
        
        period_combo = QComboBox()
        period_combo.addItems(['Day', 'Week', 'Month'])
        period_combo.setStyleSheet("background-color: #3e3e5f; color: #ffffff; padding: 5px;")
        trends_layout.addWidget(period_combo)
        
        trends_plot = pg.PlotWidget()
        trends_plot.setTitle("Medication Trends", color="#ffffff", size="12pt")
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
        self.load_medication_utilization(utilization_plot)
        self.load_medication_trends(trends_plot, 'month')
        period_combo.currentTextChanged.connect(lambda text: self.load_medication_trends(trends_plot, text.lower()))

    def load_medication_utilization(self, plot):
        data = get_medication_utilization()
        df = pd.DataFrame(data)
        
        bar = pg.BarGraphItem(x=range(len(df)), height=df['prescription_count'], width=0.6, brush='#ff7043')
        plot.addItem(bar)
        plot.getAxis('bottom').setTicks([[(i, m) for i, m in enumerate(df['name'])]])
        
    def load_medication_trends(self, plot, period):
        plot.clear()
        data = get_medication_trends(period)
        if not data:
            return
            
        df = pd.DataFrame(data)
        if df.empty:
            return
            
        # Convert time periods to numerical indices
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)
        
        for med in df['medication_name'].unique():
            med_data = df[df['medication_name'] == med]
            x = med_data['x_index'].values
            y = med_data['usage_count'].values
            plot.plot(x, y, pen=pg.mkPen(color='#ff7043', width=2), name=med)
        
        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setLabel('Time Period')
        plot.addLegend()

    def wheelEvent(self, event):
        event.ignore()