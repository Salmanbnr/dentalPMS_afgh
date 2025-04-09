import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QApplication, QGraphicsDropShadowEffect, QComboBox, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QPalette
import pyqtgraph as pg
import pandas as pd
import numpy as np
import qtawesome as qta

from model.analysis_model import get_medication_trends

# --- New Premium Color Palette for Medication Analysis (Vibrant and Professional) ---
COLOR_PRIMARY = "#0f3460"  # Deep Teal Blue (Headers, Titles)
COLOR_SECONDARY = "#f8f9fa"  # Off-White (Background)
COLOR_ACCENT = "#e94560"  # Coral Red (Buttons, Highlights)
COLOR_SUCCESS = "#00c851"  # Bright Teal (Success, Normal Ranges) - Minimally used
COLOR_WARNING = "#ffbb33"  # Warm Yellow (Warnings, Medium Risk)
COLOR_DANGER = "#ff4444"  # Bright Red (Danger, Critical Conditions)
COLOR_INFO = "#6f42c1"  # Rich Purple (Optional Category)
COLOR_TEXT_LIGHT = "#ffffff"  # White (Light Text)
COLOR_TEXT_DARK = "#1a1a1a"  # Dark Charcoal (Body Text)
COLOR_TEXT_MUTED = "#6c757d"  # Medium Gray (Subtext)
COLOR_BORDER = "#dee2e6"  # Light Gray Border (UI Elements)
COLOR_CHART_BG = "#ffffff"  # White (Chart Background)
COLOR_TABLE_ALT_ROW = "#fefefe"  # Almost White (Alternating Rows)
COLOR_HOVER = "#d43f5a"  # Darker Coral Red (Hover State)

# New Chart Colors for Medication Trends (Vibrant and Premium)
CHART_COLORS_TRENDS = [
    "#e94560",  # Coral Red (Primary)
    "#9b59b6",  # Amethyst Purple (Secondary)
    "#ff9f43",  # Orange Peel (Highlight)
    "#4a90e2",  # Sky Blue (Unique Metrics)
    "#f4a261",  # Burnt Sienna (Additional Data)
]

# --- Stylesheet ---
MEDICATION_STYLESHEET = f"""
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
    background-color: {COLOR_PRIMARY};  /* Fixed deep teal header */
    color: {COLOR_TEXT_LIGHT};
    padding: 10px;
    font-weight: 600;
    border-bottom: 1px solid {COLOR_BORDER};
}}
QComboBox {{
    background-color: {CHART_COLORS_TRENDS[2]};  /* Orange Peel for filter */
    color: {COLOR_TEXT_DARK};  /* Dark text for visibility */
    border-radius: 8px;
    padding: 8px;
    font-size: 10pt;
}}
QComboBox:hover {{
    background-color: {COLOR_HOVER};
}}
QPushButton#refreshBtn {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT_LIGHT};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 10pt;
}}
QPushButton#refreshBtn:hover {{
    background-color: {COLOR_HOVER};
}}
QLabel#titleLabel {{
    font-size: 18pt;
    font-weight: bold;
    color: {COLOR_PRIMARY};
    margin-bottom: 10px;
}}
"""

class MedicationAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(MEDICATION_STYLESHEET)
        self.setWindowTitle("Medication Analysis Dashboard")
        self.setMinimumSize(800, 900)  # Reduced for side panel compatibility
        self.init_ui()
        self.load_data()  # Ensure this is called here

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header with refresh button
        header_layout = QHBoxLayout()
        refresh_btn = QPushButton(qta.icon('fa5s.sync', color=COLOR_TEXT_LIGHT), " Refresh Data", objectName="refreshBtn")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setIconSize(QSize(14, 14))
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        main_layout.addLayout(header_layout)

        # Title
        title = QLabel("Medication Analytics", objectName="titleLabel")
        main_layout.addWidget(title)

        # Main Content (No horizontal scroll, vertical scroll only if needed)
        container = QWidget()
        cont_layout = QHBoxLayout(container)
        cont_layout.setSpacing(15)
        cont_layout.setContentsMargins(0, 0, 0, 0)

        # Single Column for Premium Line Chart
        main_column = QVBoxLayout()
        main_column.setSpacing(15)

        # Premium Line Chart Frame
        trends_frame = QFrame()
        trends_frame.setMinimumHeight(600)  # Increased height for better visualization
        trends_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:12px;")
        trends_layout = QVBoxLayout(trends_frame)
        trends_layout.setContentsMargins(15, 15, 15, 15)

        # Add Period Filter (Day/Week/Month)
        self.period_combo = QComboBox()
        self.period_combo.addItems(['Day', 'Week', 'Month'])
        self.period_combo.currentTextChanged.connect(lambda text: self.load_medication_trends(self.trends_plot, text.lower()))
        trends_layout.addWidget(self.period_combo)

        self.trends_plot = pg.PlotWidget()
        self.trends_plot.setBackground(COLOR_CHART_BG)
        # Set dotted grid using PlotItem's showGrid with custom pens
      # Set dotted grid using PlotItem's showGrid with custom pens
        grid_pen = pg.mkPen(color=COLOR_TEXT_DARK, width=1, style=Qt.DotLine)
        plot_item = self.trends_plot.getPlotItem()
        plot_item.showGrid(x=True, y=True, alpha=0.2)
        # Apply the grid pen to the plot axes
        plot_item.getAxis('bottom').setGrid(100)  # Enable grid on bottom axis
        plot_item.getAxis('left').setGrid(100)    # Enable grid on left axis

        # Set the grid pen for the plot item
        # plot_item.setAxisPen('bottom', pg.mkPen(COLOR_TEXT_DARK, width=2))
        # plot_item.setAxisPen('left', pg.mkPen(COLOR_TEXT_DARK, width=2))

        self.trends_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK, width=2))
        self.trends_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK, width=2))
        self.trends_plot.setLabel('left', 'Usage Count', color=COLOR_TEXT_DARK, size='12pt', bold=True)
        self.trends_plot.setLabel('bottom', 'Time Period', color=COLOR_TEXT_DARK, size='12pt', bold=True)
        self.trends_plot.setMouseEnabled(x=False, y=False)
        trends_layout.addWidget(self.trends_plot)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 8)
        trends_frame.setGraphicsEffect(shadow)
        main_column.addWidget(trends_frame)
        main_column.addStretch()

        # Ensure no horizontal scroll
        cont_layout.addLayout(main_column, 1)  # Full width for the line chart
        main_layout.addWidget(container)

    def load_data(self):
        """Load initial data for the visualization."""
        self.load_medication_trends(self.trends_plot, 'month')

    def load_medication_trends(self, plot, period):
        plot.clear()
        data = get_medication_trends(period)
        if not data or pd.DataFrame(data).empty:
            return

        df = pd.DataFrame(data)

        # Pivot data to get medications as columns and time periods as rows
        pivot_df = df.pivot(index='time_period', columns='medication_name', values='usage_count').fillna(0)

        # Get unique time periods and medications
        unique_periods = pivot_df.index.tolist()
        medications = pivot_df.columns.tolist()

        # Create x indices for time periods
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        x = np.array([period_to_index[period] for period in unique_periods])

        # Premium Line Chart with Smooth Curves and Points
        for i, medication in enumerate(medications):
            y = pivot_df[medication].values

            # Create a smooth line with points
            pen = pg.mkPen(color=CHART_COLORS_TRENDS[i % len(CHART_COLORS_TRENDS)], width=3, style=Qt.SolidLine)
            curve = plot.plot(x, y, pen=pen, name=medication, symbol='o', symbolSize=10, symbolBrush=CHART_COLORS_TRENDS[i % len(CHART_COLORS_TRENDS)], symbolPen=pen)

            # Add subtle fill under the curve for premium look
            fill = pg.FillBetweenItem(curve1=curve, curve2=pg.PlotDataItem(x, np.zeros_like(x)), brush=pg.mkBrush(QColor(CHART_COLORS_TRENDS[i % len(CHART_COLORS_TRENDS)] + '20')))
            plot.addItem(fill)

        # Set x-axis ticks with rotated labels for readability
        plot.getAxis('bottom').setTicks([[(i, str(period)) for i, period in enumerate(unique_periods)]])
        plot.getAxis('bottom').setStyle(tickTextOffset=15, tickFont=QFont('Roboto', 10, QFont.Bold))
        plot.getAxis('left').setStyle(tickFont=QFont('Roboto', 10, QFont.Bold))

        # Set premium title with shadow effect
        plot.setTitle(f"Medication Usage Trends ({period.capitalize()})", color=COLOR_PRIMARY, size="16pt", bold=True)

        # Add Elegant Legend
        legend = plot.addLegend(offset=(20, 20), labelTextSize='12pt', labelTextColor=COLOR_TEXT_DARK)
        legend.setBrush(pg.mkBrush(COLOR_CHART_BG))
        legend.setPen(pg.mkPen(COLOR_BORDER, width=2))
        legend.setVisible(True)

        # Enhance grid and axes for premium look
        plot.showAxis('right')
        plot.showAxis('top')
        plot.getAxis('right').setPen(pg.mkPen(COLOR_TEXT_DARK, width=1, style=Qt.DashLine))
        plot.getAxis('top').setPen(pg.mkPen(COLOR_TEXT_DARK, width=1, style=Qt.DashLine))

        plot.setXRange(-0.5, len(unique_periods) - 0.5, padding=0.1)

    def refresh_data(self):
        self.load_medication_trends(self.trends_plot, self.period_combo.currentText().lower())

    def wheelEvent(self, event):
        event.ignore()  # Disable wheel scroll for the entire widget

class RotatedAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        """Override to rotate tick labels manually (handled by setting angle in TextItem)"""
        return [str(value) for value in values]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MedicationAnalysis()
    window.show()
    sys.exit(app.exec())