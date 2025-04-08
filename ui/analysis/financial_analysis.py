# ui/analysis/financial_analysis.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QTableWidget, QTableWidgetItem, QScrollArea, QLabel,
                            QPushButton, QFrame, QComboBox, QSizePolicy, QHeaderView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
import pyqtgraph as pg
import pandas as pd
import numpy as np
import qtawesome as qta

from model.analysis_model import get_revenue_analysis, get_price_deviation_analysis

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

class FinancialAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(ANALYSIS_STYLESHEET)
        self.setWindowTitle("Financial Analysis")
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
        title = QLabel("Financial Analytics", objectName="titleLabel")
        main_layout.addWidget(title)

        # Main content area wrapped in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_content = QWidget()
        content_layout = QHBoxLayout(scroll_content)
        content_layout.setSpacing(15)

        # Left column - Revenue Analysis
        left_column = QVBoxLayout()

        revenue_frame = QFrame(objectName="chartFrame")
        revenue_layout = QVBoxLayout(revenue_frame)

        period_combo = QComboBox(objectName="periodCombo")
        period_combo.addItems(['Day', 'Week', 'Month'])
        period_combo.currentTextChanged.connect(lambda text: self.load_revenue_analysis(self.revenue_plot, text.lower()))
        revenue_layout.addWidget(period_combo)

        self.revenue_plot = pg.PlotWidget()
        self.revenue_plot.setBackground(COLOR_CHART_BG)
        self.revenue_plot.showGrid(x=True, y=True, alpha=0.3)
        self.revenue_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.revenue_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.revenue_plot.setLabel('left', 'Amount')
        self.revenue_plot.setLabel('bottom', 'Time Period')
        self.revenue_plot.setMaximumHeight(300)
        self.revenue_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        revenue_layout.addWidget(self.revenue_plot)

        revenue_frame.setLayout(revenue_layout)
        left_column.addWidget(revenue_frame)

        # Right column - Price Deviation Table
        right_column = QVBoxLayout()

        deviation_frame = QFrame(objectName="chartFrame")
        deviation_layout = QVBoxLayout(deviation_frame)

        self.deviation_table = QTableWidget()
        self.deviation_table.setColumnCount(5)
        self.deviation_table.setHorizontalHeaderLabels(['Name', 'Default Price', 'Avg Charged', 'Avg Deviation', 'Count'])
        self.deviation_table.verticalHeader().setVisible(False)
        self.deviation_table.setAlternatingRowColors(True)
        self.deviation_table.horizontalHeader().setStretchLastSection(True)
        self.deviation_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.deviation_table.setMinimumHeight(300)
        deviation_layout.addWidget(self.deviation_table)

        deviation_frame.setLayout(deviation_layout)
        right_column.addWidget(deviation_frame)

        # Add columns to content layout
        content_layout.addLayout(left_column, 1)
        content_layout.addLayout(right_column, 1)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.refresh_data()

    def refresh_data(self):
        self.load_revenue_analysis(self.revenue_plot, 'month')
        self.load_price_deviation(self.deviation_table)

    def load_revenue_analysis(self, plot, period):
        plot.clear()
        data = get_revenue_analysis(period)
        if not data or pd.DataFrame(data).empty:
            return

        df = pd.DataFrame(data)
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)

        x = df['x_index'].values
        plot.plot(x, df['billed_amount'], pen=pg.mkPen(color=COLOR_ACCENT, width=2), name='Billed')
        plot.plot(x, df['collected_amount'], pen=pg.mkPen(color=COLOR_SUCCESS, width=2), name='Collected')

        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setStyle(tickTextOffset=10)
        plot.setTitle(f"Revenue Trends ({period.capitalize()})", color=COLOR_TEXT_DARK, size="12pt")
        plot.addLegend()

    def load_price_deviation(self, table):
        data = get_price_deviation_analysis()
        services = data['services']
        meds = data['medications']

        table.setRowCount(len(services) + len(meds))
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
        event.ignore()  # Disable wheel scroll for the entire widget