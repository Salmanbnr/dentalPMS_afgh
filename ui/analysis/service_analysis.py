import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QApplication, QGraphicsDropShadowEffect, QComboBox, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QPalette, QLinearGradient,QBrush
import pyqtgraph as pg
import pandas as pd
import numpy as np

from model.analysis_model import get_service_trends, get_service_utilization, get_tooth_number_analysis

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

# New Chart Colors for Service Analysis (Premium, No Green Tones)
CHART_COLORS_SERVICE = [
    "#4682B4",  # Steel Blue (Primary Service Data)
    "#FF69B4",  # Hot Pink (Secondary Service Data)
    "#DAA520",  # Goldenrod (Highlight Trends)
    "#9932CC",  # Dark Orchid (Unique Metrics)
    "#F08080",  # Light Coral (Additional Data)
    "#4169E1"   # Royal Blue (Extra Trend)
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
    background-color: {CHART_COLORS_SERVICE[2]};  /* Goldenrod for filter */
    color: {COLOR_TEXT_DARK};  /* Dark text for visibility */
    border-radius: 8px;
    padding: 8px;
    font-size: 10pt;
}}
QComboBox:hover {{
    background-color: {COLOR_HOVER};
}}
QLineEdit {{
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 10pt;
}}
QLineEdit:focus {{
    border: 2px solid {COLOR_ACCENT};
}}
"""

class ServiceAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Service Analysis Dashboard")
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

        # Left: Service Utilization and Tooth Analysis
        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        # Service Utilization Chart (Bar Chart with Gradient Fill)
        utilization_frame = QFrame()
        utilization_frame.setMinimumHeight(400)
        utilization_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:12px;")
        utilization_layout = QVBoxLayout(utilization_frame)
        utilization_layout.setContentsMargins(15, 15, 15, 15)

        self.utilization_plot = pg.PlotWidget()
        self.utilization_plot.setBackground(COLOR_CHART_BG)
        self.utilization_plot.showGrid(x=True, y=True, alpha=0.3)
        self.utilization_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.utilization_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.utilization_plot.setLabel('left', 'Usage Count', color=COLOR_TEXT_DARK, size='10pt')
        self.utilization_plot.setLabel('bottom', 'Service', color=COLOR_TEXT_DARK, size='10pt')
        self.utilization_plot.setMouseEnabled(x=False, y=False)
        utilization_layout.addWidget(self.utilization_plot)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        utilization_frame.setGraphicsEffect(shadow)
        left_column.addWidget(utilization_frame)
        left_column.addStretch()

        # Tooth Number Analysis Table with Search Bar
        tooth_frame = QFrame()
        tooth_frame.setMinimumHeight(400)
        tooth_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:12px;")
        tooth_layout = QVBoxLayout(tooth_frame)
        tooth_layout.setContentsMargins(15, 15, 15, 15)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by tooth number...")
        self.search_bar.setFixedWidth(200)
        self.search_bar.textChanged.connect(self.filter_table)
        tooth_layout.addWidget(self.search_bar)

        self.tooth_table = QTableWidget()
        self.tooth_table.setColumnCount(3)
        self.tooth_table.setHorizontalHeaderLabels(['Tooth Number', 'Treatment Count', 'Common Treatments'])
        self.tooth_table.verticalHeader().setVisible(False)
        self.tooth_table.setAlternatingRowColors(True)
        self.tooth_table.setShowGrid(False)
        self.tooth_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        hdr_view = self.tooth_table.horizontalHeader()
        hdr_view.setDefaultAlignment(Qt.AlignCenter)
        hdr_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Tooth Number fixed
        hdr_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Treatment Count fixed
        hdr_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Common Treatments stretched
        self.tooth_table.setColumnWidth(0, 100)  # Tooth Number
        self.tooth_table.setColumnWidth(1, 120)  # Treatment Count
        self.tooth_table.doubleClicked.connect(self.show_row_details)
        tooth_layout.addWidget(self.tooth_table)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        tooth_frame.setGraphicsEffect(shadow)
        left_column.addWidget(tooth_frame)

        # Right: Service Trends
        right_column = QVBoxLayout()
        right_column.setSpacing(15)

        trends_frame = QFrame()
        trends_frame.setMinimumHeight(400)
        trends_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:12px;")
        trends_layout = QVBoxLayout(trends_frame)
        trends_layout.setContentsMargins(15, 15, 15, 15)

        # Add Period Filter (Day/Week/Month)
        self.period_combo = QComboBox()
        self.period_combo.addItems(['Day', 'Week', 'Month'])
        self.period_combo.setPlaceholderText("Filter by Day, Week, Month")
        self.period_combo.currentTextChanged.connect(lambda text: self.load_service_trends(self.trends_plot, text.lower()))
        trends_layout.addWidget(self.period_combo)

        self.trends_plot = pg.PlotWidget()
        self.trends_plot.setBackground(COLOR_CHART_BG)
        self.trends_plot.showGrid(x=True, y=True, alpha=0.3)
        self.trends_plot.getAxis('bottom').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.trends_plot.getAxis('left').setPen(pg.mkPen(COLOR_TEXT_DARK))
        self.trends_plot.setLabel('left', 'Usage Count', color=COLOR_TEXT_DARK, size='10pt')
        self.trends_plot.setLabel('bottom', 'Time Period', color=COLOR_TEXT_DARK, size='10pt')
        self.trends_plot.setMouseEnabled(x=False, y=False)
        trends_layout.addWidget(self.trends_plot)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        trends_frame.setGraphicsEffect(shadow)
        right_column.addWidget(trends_frame)
        right_column.addStretch()

        # Ensure no horizontal scroll by setting maximum width and flexible layout
        cont_layout.addLayout(left_column, 1)  # Left takes 50% of space
        cont_layout.addLayout(right_column, 1)  # Right takes 50% of space
        main_layout.addWidget(container)

    def load_data(self):
        self.load_service_utilization(self.utilization_plot)
        self.load_tooth_number(self.tooth_table)
        self.load_service_trends(self.trends_plot, 'month')

    def load_service_utilization(self, plot):
        plot.clear()
        data = get_service_utilization()
        df = pd.DataFrame(data)
        if df.empty:
            return

        x = np.arange(len(df['name']))

        # Create gradient brush for bars
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.ObjectMode)
        gradient.setColorAt(0, QColor(CHART_COLORS_SERVICE[0]))
        gradient.setColorAt(1, QColor(CHART_COLORS_SERVICE[0] + '80'))

        # Create a QBrush from the gradient
        brush = QBrush(gradient)

        bars = pg.BarGraphItem(
            x=x,
            height=df['usage_count'],
            width=0.6,
            brush=brush,
            pen=pg.mkPen(COLOR_BORDER)
        )
        plot.addItem(bars)

        # Set axis ticks and styles
        plot.getAxis('bottom').setTicks([[(i, str(s)) for i, s in enumerate(df['name'])]])
        plot.getAxis('bottom').setStyle(tickTextOffset=15, tickFont=QFont('Roboto', 8))
        plot.getAxis('left').setStyle(tickFont=QFont('Roboto', 8))

        # Set chart title
        plot.setTitle("Service Utilization", color=COLOR_TEXT_DARK, size="14pt", bold=True)

        # Add legend
        legend = plot.addLegend(offset=(10, 10))
        legend.addItem(bars, "Usage")
        legend.setBrush(pg.mkBrush(COLOR_CHART_BG))
        legend.setPen(pg.mkPen(COLOR_BORDER, width=1))
        legend.setLabelTextColor(COLOR_TEXT_DARK)
    def load_tooth_number(self, table):
        data = get_tooth_number_analysis()
        self.tooth_data = data

        table.setRowCount(len(data))
        for row, entry in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(str(entry['tooth_number'])))
            table.setItem(row, 1, QTableWidgetItem(str(entry['treatment_count'])))
            table.setItem(row, 2, QTableWidgetItem(entry['common_treatments']))
        table.resizeColumnsToContents()

    def load_service_trends(self, plot, period):
        plot.clear()
        data = get_service_trends(period)
        if not data or pd.DataFrame(data).empty:
            return

        df = pd.DataFrame(data)
        unique_periods = df['time_period'].unique()
        period_to_index = {period: i for i, period in enumerate(unique_periods)}
        df['x_index'] = df['time_period'].map(period_to_index)

        # Premium Line Chart with Gradient Fills
        for i, service in enumerate(df['service_name'].unique()):
            service_data = df[df['service_name'] == service]
            x = service_data['x_index'].values
            y = service_data['usage_count'].values
            curve = plot.plot(x, y, pen=pg.mkPen(color=CHART_COLORS_SERVICE[i % len(CHART_COLORS_SERVICE)], width=3, capstyle=Qt.RoundCap), name=service)
            fill = pg.FillBetweenItem(
                curve1=curve,
                curve2=pg.PlotDataItem(x, np.zeros_like(x)),
                brush=pg.mkBrush(QColor(CHART_COLORS_SERVICE[i % len(CHART_COLORS_SERVICE)] + '40')),
            )
            plot.addItem(fill)

        plot.getAxis('bottom').setTicks([[(i, period) for period, i in period_to_index.items()]])
        plot.getAxis('bottom').setStyle(tickTextOffset=15, tickFont=QFont('Roboto', 8))
        plot.getAxis('left').setStyle(tickFont=QFont('Roboto', 8))
        plot.setTitle(f"Service Trends ({period.capitalize()})", color=COLOR_TEXT_DARK, size="14pt", bold=True)

        # Add Legend
        legend = plot.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(COLOR_CHART_BG))
        legend.setPen(pg.mkPen(COLOR_BORDER, width=1))
        legend.setLabelTextColor(COLOR_TEXT_DARK)
        legend.setVisible(True)

        plot.showGrid(x=True, y=True, alpha=0.2)

    def filter_table(self, txt):
        txt = txt.lower()
        for r in range(self.tooth_table.rowCount()):
            itm = self.tooth_table.item(r, 0)  # Filter by tooth number (column 0)
            hide = txt not in itm.text().lower()
            self.tooth_table.setRowHidden(r, hide)

    def show_row_details(self, index):
        row = index.row()
        tooth_number = self.tooth_table.item(row, 0).text()
        treatment_count = self.tooth_table.item(row, 1).text()
        common_treatments = self.tooth_table.item(row, 2).text()
        
        details = f"Tooth Number: {tooth_number}\nTreatment Count: {treatment_count}\nCommon Treatments: {common_treatments}"
        QMessageBox.information(self, "Tooth Details", details)

    def wheelEvent(self, event):
        event.ignore()  # Disable wheel scroll for the entire widget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ServiceAnalysis()
    window.show()
    sys.exit(app.exec())