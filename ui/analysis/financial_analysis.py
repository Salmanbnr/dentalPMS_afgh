import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QApplication, QGraphicsDropShadowEffect, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QPalette, QLinearGradient
import pyqtgraph as pg
import pandas as pd
import numpy as np

from model.analysis_model import get_revenue_analysis, get_price_deviation_analysis

# --- Updated Color Palette for Dental Clinic (Professional and Clean) ---
COLOR_PRIMARY = "#2c3e50"  # Dark Blue (Headers, Titles)
COLOR_SECONDARY = "#ecf0f1"  # Light Gray (Background)
COLOR_ACCENT = "#3498db"  # Bright Blue (Buttons, Highlights)
COLOR_SUCCESS = "#27ae60"  # Green (Success, Normal Ranges)
COLOR_WARNING = "#e67e22"  # Orange (Warnings, Medium Risk)
COLOR_DANGER = "#e74c3c"  # Red (Danger, Critical Conditions)
COLOR_INFO = "#8e44ad"  # Purple (Optional Category)
COLOR_TEXT_LIGHT = "#ffffff"  # White (Light Text)
COLOR_TEXT_DARK = "#34495e"  # Dark Gray (Body Text)
COLOR_TEXT_MUTED = "#7f8c8d"  # Muted Gray (Subtext)
COLOR_BORDER = "#bdc3c7"  # Light Gray Border (UI Elements)
COLOR_CHART_BG = "#ffffff"  # White (Chart Background)
COLOR_TABLE_ALT_ROW = "#f8f9f9"  # Very Light Gray (Alternating Rows)
COLOR_HOVER = "#4a6fa5"  # Hover State (Darker Accent Blue)

# New Chart Colors for Dental Clinic (Clean and Professional)
CHART_COLORS_DENTAL = [
    "#1E90FF",  # Dodger Blue (Primary Data Series, Trustworthy)
    "#32CD32",  # Lime Green (Healthy, Positive Outcomes)
    "#FFD700",  # Gold (Highlight, Premium Services)
    "#FF4500",  # Orange Red (Alerts, Urgent Issues)
    "#C0C0C0",  # Silver (Neutral, Background Data)
    "#20B2AA"   # Light Sea Green (Secondary Metrics, Calm)
]

# --- Stylesheet ---
DASHBOARD_STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_TEXT_DARK};
    font-family: 'Roboto', 'Segoe UI', sans-serif;
    font-size: 11pt;
}}
QFrame {{
    border-radius: 12px;
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
}}
QTableWidget {{
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
    gridline-color: {COLOR_BORDER};
    alternate-background-color: {COLOR_TABLE_ALT_ROW};
    border-radius: 8px;
}}
QTableWidget::item:selected {{
    background-color: {COLOR_HOVER};  /* Row selection color */
    color: {COLOR_TEXT_LIGHT};
}}
QHeaderView::section {{
    background-color: {COLOR_PRIMARY};  /* Fixed dark blue header */
    color: {COLOR_TEXT_LIGHT};
    padding: 10px;
    font-weight: 600;
    border-bottom: 1px solid {COLOR_BORDER};
}}
QComboBox {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT_LIGHT};
    border-radius: 8px;
    padding: 8px;
    font-size: 10pt;
}}
QComboBox:hover {{
    background-color: {COLOR_HOVER};
}}
"""

class FinancialAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Financial Analysis Dashboard")
        self.setMinimumSize(800, 900)  # Reduced for side panel compatibility
        self.init_ui()
        self.load_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Main Content (No horizontal scroll, vertical scroll only if needed)
        container = QWidget()
        cont_layout = QHBoxLayout(container)
        cont_layout.setSpacing(15)
        cont_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Revenue Analysis Chart
        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        revenue_frame = QFrame()
        revenue_frame.setMinimumHeight(400)
        revenue_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:12px;")
        revenue_layout = QVBoxLayout(revenue_frame)
        revenue_layout.setContentsMargins(15, 15, 15, 15)

        # Add Period Filter (Day/Week/Month)
        period_combo = QComboBox()
        period_combo.addItems(['Day', 'Week', 'Month'])
        period_combo.currentTextChanged.connect(lambda text: self.load_revenue_analysis(self.revenue_plot, text.lower()))
        revenue_layout.addWidget(period_combo)

        self.revenue_plot = pg.PlotWidget()
        self.revenue_plot.setBackground(COLOR_CHART_BG)
        self.revenue_plot.showGrid(x=True, y=True, alpha=0.3)
        self.revenue_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.revenue_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.revenue_plot.setLabel('left', 'Amount', color=COLOR_TEXT_DARK, size='10pt')
        self.revenue_plot.setLabel('bottom', 'Time Period', color=COLOR_TEXT_DARK, size='10pt')
        self.revenue_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        revenue_layout.addWidget(self.revenue_plot)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        revenue_frame.setGraphicsEffect(shadow)
        left_column.addWidget(revenue_frame)
        left_column.addStretch()

        # Right: Price Deviation Table
        right_column = QVBoxLayout()
        right_column.setSpacing(15)

        deviation_frame = QFrame()
        deviation_frame.setMinimumHeight(400)
        deviation_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:12px;")
        deviation_layout = QVBoxLayout(deviation_frame)
        deviation_layout.setContentsMargins(15, 15, 15, 15)

        self.deviation_table = QTableWidget()
        self.deviation_table.setColumnCount(5)
        self.deviation_table.setHorizontalHeaderLabels(['Name', 'Default Price', 'Avg Charged', 'Avg Deviation', 'Count'])
        self.deviation_table.verticalHeader().setVisible(False)
        self.deviation_table.setAlternatingRowColors(True)
        self.deviation_table.setShowGrid(False)
        self.deviation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        hdr_view = self.deviation_table.horizontalHeader()
        hdr_view.setDefaultAlignment(Qt.AlignCenter)
        hdr_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # Stretch all columns
        deviation_layout.addWidget(self.deviation_table)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        deviation_frame.setGraphicsEffect(shadow)
        right_column.addWidget(deviation_frame)
        right_column.addStretch()

        # Ensure no horizontal scroll by setting maximum width and flexible layout
        cont_layout.addLayout(left_column, 1)  # Left takes 50% of space
        cont_layout.addLayout(right_column, 1)  # Right takes 50% of space
        main_layout.addWidget(container)

    def load_data(self):
        self.load_revenue_analysis(self.revenue_plot, 'month')  # Default to month
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
        billed = df['billed_amount']
        collected = df['collected_amount']

        # Premium Look for Line Chart
        # Billed Amount (Blue with Gradient Fill)
        billed_curve = plot.plot(x, billed, pen=pg.mkPen(color=CHART_COLORS_DENTAL[0], width=3, capstyle=Qt.RoundCap), name='Billed')
        fill_billed = pg.FillBetweenItem(
            curve1=billed_curve,
            curve2=pg.PlotDataItem(x, np.zeros_like(x)),
            brush=pg.mkBrush(QColor(CHART_COLORS_DENTAL[0] + '40')),  # Semi-transparent fill
        )
        plot.addItem(fill_billed)

        # Collected Amount (Green with Gradient Fill)
        collected_curve = plot.plot(x, collected, pen=pg.mkPen(color=CHART_COLORS_DENTAL[1], width=3, capstyle=Qt.RoundCap), name='Collected')
        fill_collected = pg.FillBetweenItem(
            curve1=collected_curve,
            curve2=pg.PlotDataItem(x, np.zeros_like(x)),
            brush=pg.mkBrush(QColor(CHART_COLORS_DENTAL[1] + '40')),  # Semi-transparent fill
        )
        plot.addItem(fill_collected)

        # Customize Axes and Grid
        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setStyle(tickTextOffset=15, tickFont=QFont('Roboto', 8))
        plot.getAxis('left').setStyle(tickFont=QFont('Roboto', 8))
        plot.setTitle(f"Revenue Trends ({period.capitalize()})", color=COLOR_TEXT_DARK, size="14pt", bold=True)

        # Add Legend with Premium Styling and Ensure Visibility
        legend = plot.addLegend(offset=(10, 10))  # Positioned in top-right corner
        legend.setBrush(pg.mkBrush(COLOR_CHART_BG))
        legend.setPen(pg.mkPen(COLOR_BORDER, width=1))
        legend.setLabelTextColor(COLOR_TEXT_DARK)
        legend.setVisible(True)  # Ensure legend is visible

        # Enhance Grid and Background
        plot.showGrid(x=True, y=True, alpha=0.2)
        plot.setStyleSheet("border: none;")

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = FinancialAnalysis()
    window.show()
    sys.exit(app.exec())