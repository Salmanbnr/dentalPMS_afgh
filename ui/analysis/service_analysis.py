import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QApplication, QGraphicsDropShadowEffect, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QPalette
import pyqtgraph as pg
import pandas as pd
import numpy as np

from model.analysis_model import get_service_utilization, get_medication_utilization, get_tooth_number_analysis, get_medication_trends

# --- Updated Color Palette for Medical Analysis ---
COLOR_PRIMARY = "#2c3e50"       # Dark Blue (Headers, Titles)
COLOR_SECONDARY = "#ecf0f1"     # Light Gray (Background)
COLOR_ACCENT = "#3498db"        # Bright Blue (Buttons, Highlights)
COLOR_TEXT_LIGHT = "#ffffff"    # White (Light Text)
COLOR_TEXT_DARK = "#34495e"     # Dark Gray (Body Text)
COLOR_TEXT_MUTED = "#7f8c8d"    # Muted Gray (Subtext)
COLOR_BORDER = "#bdc3c7"        # Light Gray Border (UI Elements)
COLOR_CHART_BG = "#ffffff"      # White (Chart Background)
COLOR_TABLE_ALT_ROW = "#f8f9f9" # Very Light Gray (Alternating Rows)
COLOR_HOVER = "#4a6fa5"         # Hover State (Darker Accent Blue)
COLOR_BAR_SERVICE = "#4682B4"   # Steel Blue for Services
COLOR_BAR_MEDICAL = "#1abc9c"   # Solid Turquoise for Medications

# New Chart Colors for Medication Trends (from medication_analysis.py)
CHART_COLORS_TRENDS = [
    "#e94560",  # Coral Red (Primary)
    "#9b59b6",  # Amethyst Purple (Secondary)
    "#ff9f43",  # Orange Peel (Highlight)
    "#4a90e2",  # Sky Blue (Unique Metrics)
    "#f4a261",  # Burnt Sienna (Additional Data)
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
"""

class ServiceAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Combined Service and Medication Analysis Dashboard")
        self.setMinimumSize(800, 900)  # Reduced for side panel compatibility
        self.init_ui()
        self.load_data()  # Ensure this is called here

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Main Content (No horizontal scroll, vertical scroll only if needed)
        container = QWidget()
        cont_layout = QVBoxLayout(container)  # Changed to vertical to stack bar chart and two columns
        cont_layout.setSpacing(15)
        cont_layout.setContentsMargins(0, 0, 0, 0)

        # Top: Combined Utilization Chart (Bar Chart for both Services and Medications)
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
        self.utilization_plot.setLabel('left', 'Usage/Prescription Count', color=COLOR_TEXT_DARK, size='10pt')
        self.utilization_plot.setLabel('bottom', 'Item', color=COLOR_TEXT_DARK, size='10pt')
        self.utilization_plot.setMouseEnabled(x=False, y=False)
        utilization_layout.addWidget(self.utilization_plot)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        utilization_frame.setGraphicsEffect(shadow)
        cont_layout.addWidget(utilization_frame)

        # Bottom: Two-column layout for Tooth Table and Medication Trends
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)

        # Left Column: Tooth Number Analysis Table with Search Bar
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
        bottom_layout.addWidget(tooth_frame, 1)  # Stretch factor 1

        # Right Column: Medication Trends Line Chart (Imported from medication_analysis.py)
        trends_frame = QFrame()
        trends_frame.setMinimumHeight(400)  # Adjusted height to match table
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
        grid_pen = pg.mkPen(color=COLOR_TEXT_DARK, width=1, style=Qt.DotLine)
        plot_item = self.trends_plot.getPlotItem()
        plot_item.showGrid(x=True, y=True, alpha=0.2)
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
        bottom_layout.addWidget(trends_frame, 1)  # Stretch factor 1

        cont_layout.addLayout(bottom_layout)
        main_layout.addWidget(container)

    def load_data(self):
        """Load initial data for all visualizations."""
        self.load_combined_utilization(self.utilization_plot)
        self.load_tooth_number(self.tooth_table)
        self.load_medication_trends(self.trends_plot, 'month')  # Load default month view

    def load_combined_utilization(self, plot):
        plot.clear()

        # Load service utilization data
        service_data = get_service_utilization()
        service_df = pd.DataFrame(service_data)
        if not service_df.empty:
            service_df = service_df.sort_values(by='usage_count', ascending=False).head(5)
            service_df['type'] = 'Service'
            service_df['value'] = service_df['usage_count']
            service_df['name'] = service_df['name']

        # Load medication utilization data
        med_data = get_medication_utilization()
        med_df = pd.DataFrame(med_data)
        if not med_df.empty:
            med_df = med_df.sort_values(by='prescription_count', ascending=False).head(5)
            med_df['type'] = 'Medication'
            med_df['value'] = med_df['prescription_count']
            med_df['name'] = med_df['name']

        # Combine both datasets
        combined_df = pd.concat([service_df, med_df], ignore_index=True)
        if combined_df.empty:
            return

        combined_df = combined_df.sort_values(by='value', ascending=False)
        x = np.arange(len(combined_df))

        # Use solid colors for bars, no gradient
        bars_service = pg.BarGraphItem(
            x=x[combined_df['type'] == 'Service'],
            height=combined_df[combined_df['type'] == 'Service']['value'],
            width=0.3,
            brush=pg.mkBrush(COLOR_BAR_SERVICE),  # Steel Blue for Services
            pen=pg.mkPen(COLOR_BORDER)
        )

        bars_med = pg.BarGraphItem(
            x=x[combined_df['type'] == 'Medication'],
            height=combined_df[combined_df['type'] == 'Medication']['value'],
            width=0.3,
            brush=pg.mkBrush(COLOR_BAR_MEDICAL),  # Solid Turquoise for Medications
            pen=pg.mkPen(COLOR_BORDER)
        )

        plot.addItem(bars_service)
        plot.addItem(bars_med)

        # Replace x-axis with custom axis
        rotated_axis = RotatedAxis(orientation='bottom')
        plot.setAxisItems({'bottom': rotated_axis})

        # Create and manually add text labels at correct positions
        for i, label in enumerate(combined_df['name']):
            text = pg.TextItem(text=str(label), anchor=(0, 0), angle=90)  # Rotated 90 degrees
            text.setFont(QFont("Roboto", 8))
            text.setColor(QColor(COLOR_TEXT_DARK))
            plot.addItem(text)
            text.setPos(i - 0.1, 0)

        plot.getAxis('left').setStyle(tickFont=QFont('Roboto', 8))

        plot.setTitle("Combined Service and Medication Utilization", color=COLOR_TEXT_DARK, size="14pt", bold=True)

        legend = plot.addLegend(offset=(10, 10))
        legend.addItem(bars_service, "Services")
        legend.addItem(bars_med, "Medications")
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

class RotatedAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        """Override to rotate tick labels manually (handled by setting angle in TextItem)"""
        return [str(value) for value in values]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ServiceAnalysis()
    window.show()
    sys.exit(app.exec())