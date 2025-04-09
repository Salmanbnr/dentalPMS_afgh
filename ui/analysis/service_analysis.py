import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QApplication, QGraphicsDropShadowEffect, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QPalette
import pyqtgraph as pg
import pandas as pd
import numpy as np

from model.analysis_model import get_service_utilization, get_medication_utilization, get_tooth_number_analysis

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
        cont_layout = QHBoxLayout(container)
        cont_layout.setSpacing(15)
        cont_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Combined Utilization and Tooth Analysis
        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        # Combined Utilization Chart (Bar Chart for both Services and Medications)
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

        # Ensure no horizontal scroll by setting maximum width and flexible layout
        cont_layout.addLayout(left_column, 1)  # Left takes 100% of space
        main_layout.addWidget(container)

    def load_data(self):
        """Load initial data for all visualizations."""
        self.load_combined_utilization(self.utilization_plot)
        self.load_tooth_number(self.tooth_table)

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