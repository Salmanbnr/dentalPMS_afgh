# financial_analysis.py (Enhanced Version)

import sys
import qtawesome as qta # Import Qtawesome
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QApplication, QGraphicsDropShadowEffect, QComboBox,
    QLineEdit, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QPointF
from PyQt6.QtGui import QColor, QFont, QPalette, QLinearGradient, QBrush, QPen, QIcon, QFontDatabase # Added QFontDatabase
import pyqtgraph as pg
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta

# --- Import your data fetching functions ---
try:
    from model.analysis_model import (
        get_revenue_analysis,
        get_price_deviation_analysis,
        get_revenue_today,
        get_revenue_this_week,
        get_revenue_this_month,
        get_revenue_by_service
    )
    MODEL_AVAILABLE = True
except ImportError as e:
    print(f"Error importing from analysis_model: {e}. Running with limited/no data.")
    MODEL_AVAILABLE = False
    # Define dummy functions if model is not available to prevent crashes
    def get_revenue_analysis(period='month'): return []
    def get_price_deviation_analysis(): return {'services': [], 'medications': []}
    def get_revenue_today(): return 0
    def get_revenue_this_week(): return 0
    def get_revenue_this_month(): return 0
    def get_revenue_by_service(limit=10): return []
# --- End Import ---


# --- Enhanced Color Palette & Theme ---
COLOR_PRIMARY = "#1A5276" # Slightly adjusted Dark Blue
COLOR_SECONDARY = "#F4F6F6" # Lighter Gray Background
COLOR_ACCENT = "#3498DB" # Bright Blue
COLOR_SUCCESS = "#27AE60" # Green
COLOR_WARNING = "#F39C12" # Brighter Orange
COLOR_DANGER = "#E74C3C" # Red
COLOR_INFO = "#8E44AD" # Purple
COLOR_TEXT_LIGHT = "#FFFFFF" # White
COLOR_TEXT_DARK = "#2C3E50" # Darker Gray Text (Primary Dark)
COLOR_TEXT_MUTED = "#707B7C" # Muted Gray Text
COLOR_BORDER = "#D5DBDB" # Lighter Border
COLOR_CHART_BG = "#FFFFFF" # White
COLOR_TABLE_ALT_ROW = "#F8F9F9"
COLOR_HOVER = "#5DADE2" # Lighter blue hover
KPI_ICON_COLOR = COLOR_ACCENT # Default Icon Color

CHART_COLORS_DENTAL = ["#3498DB", "#2ECC71", "#F1C40F", "#E74C3C", "#95A5A6", "#1ABC9C"] # Refreshed Palette

# Font Setup (Optional but recommended for consistency)
# QFontDatabase.addApplicationFont("path/to/Roboto-Regular.ttf")
# QFontDatabase.addApplicationFont("path/to/Roboto-Medium.ttf")
# QFontDatabase.addApplicationFont("path/to/Roboto-Bold.ttf")
FONT_REGULAR = "Roboto" # Use "Segoe UI" or system default if Roboto not available
FONT_MEDIUM = "Roboto Medium"
FONT_BOLD = "Roboto Bold"


# --- Stylesheet ---
DASHBOARD_STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_TEXT_DARK};
    font-family: '{FONT_REGULAR}', 'Segoe UI', sans-serif;
    font-size: 10pt; /* Base font size */
}}
QFrame#MainFrame {{ /* Style the main content frames */
    border-radius: 10px;
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
}}
QFrame#KpiCardFrame {{ /* Style KPI Card Frame */
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
}}
QLabel#KpiValueLabel {{
    font-family: '{FONT_BOLD}', '{FONT_REGULAR}';
    font-size: 18pt; /* Adjusted size */
    font-weight: 700;
    color: {COLOR_PRIMARY}; /* Use primary color for value */
    padding-bottom: 2px;
}}
QLabel#KpiTitleLabel {{
    font-size: 9pt;
    font-weight: 500; /* Medium weight */
    font-family: '{FONT_MEDIUM}', '{FONT_REGULAR}';
    color: {COLOR_TEXT_MUTED};
}}
QLabel#KpiIconLabel {{
    /* Icon color set via code */
    min-width: 35px;
    max-width: 35px; /* Fixed width for alignment */
    qproperty-alignment: 'AlignCenter'; /* Center icon */
}}
QTableWidget {{
    background-color: {COLOR_CHART_BG}; border: none; /* Remove border */
    gridline-color: {COLOR_BORDER}; alternate-background-color: {COLOR_TABLE_ALT_ROW};
    border-radius: 8px; font-size: 9pt; /* Slightly smaller table font */
    selection-background-color: {COLOR_ACCENT}30; /* Lighter selection */
    selection-color: {COLOR_TEXT_DARK};
}}
QTableWidget::item {{
    padding: 9px 12px; /* Adjusted padding */
    border-bottom: 1px solid {COLOR_BORDER};
}}
QTableWidget::item:selected {{
    border-left: 3px solid {COLOR_ACCENT}; /* Keep indicator */
}}
QHeaderView::section {{
    background-color: {COLOR_PRIMARY}; color: {COLOR_TEXT_LIGHT};
    padding: 10px 12px; font-weight: 600; border: none;
    font-size: 9pt; text-transform: uppercase; /* Uppercase headers */
    font-family: '{FONT_MEDIUM}', '{FONT_REGULAR}';
}}
QHeaderView {{ border: none; border-bottom: 1px solid {COLOR_BORDER}; }}
QTableCornerButton::section {{ background-color: {COLOR_PRIMARY}; border: none; }}
QComboBox {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    border-radius: 6px; padding: 7px 25px 7px 10px; /* Adjusted padding */
    font-size: 9pt; color: {COLOR_TEXT_DARK}; min-width: 130px;
    font-family: '{FONT_MEDIUM}', '{FONT_REGULAR}';
}}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: top right; width: 20px;
    border-left-width: 1px; border-left-color: {COLOR_BORDER}; border-left-style: solid;
    border-top-right-radius: 6px; border-bottom-right-radius: 6px;
}}
QComboBox:hover {{ border-color: {COLOR_ACCENT}; }}
QComboBox QAbstractItemView {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    selection-background-color: {COLOR_ACCENT}30; selection-color: {COLOR_TEXT_DARK};
    color: {COLOR_TEXT_DARK}; padding: 4px; font-size: 9pt;
}}
QLineEdit {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    border-radius: 6px; padding: 7px 10px; font-size: 9pt; color: {COLOR_TEXT_DARK};
}}
QLineEdit:focus {{ border: 1px solid {COLOR_ACCENT}; }}
PlotWidget {{ border-radius: 10px; border: none; }}
AxisItem {{ /* Axis pen set via code */ }}
LabelItem {{ color: {COLOR_TEXT_MUTED}; font-size: 9pt; }}
ViewBox {{ border-radius: 8px; border: none; }}
QLabel#SectionTitleLabel {{ /* Style for titles above table/chart */
    font-family: '{FONT_BOLD}', '{FONT_REGULAR}';
    font-size: 11pt;
    font-weight: 600;
    color: {COLOR_PRIMARY};
    margin-bottom: 5px;
    margin-top: 5px;
}}
"""

# --- Reusable KPI Card Widget (Premium Style) ---
class StatCard(QWidget):
    def __init__(self, title, icon_name="fa5s.question-circle", icon_color=KPI_ICON_COLOR, parent=None):
        super().__init__(parent)
        self.setObjectName("KpiCard")
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        main_layout = QVBoxLayout(self) # Use QVBoxLayout for the card itself
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins on the widget itself

        # Frame for background, border, and shadow
        frame = QFrame(self)
        frame.setObjectName("KpiCardFrame")
        frame_layout = QHBoxLayout(frame) # Use QHBoxLayout inside the frame
        frame_layout.setContentsMargins(12, 12, 12, 12) # Padding inside frame
        frame_layout.setSpacing(10)

        # Icon Label
        self.icon_label = QLabel()
        self.icon_label.setObjectName("KpiIconLabel")
        try:
            # Use qtawesome for icons
            icon = qta.icon(icon_name, color=icon_color)
            self.icon_label.setPixmap(icon.pixmap(QSize(32, 32))) # Adjust size as needed
        except Exception as e:
            print(f"Qtawesome Error: {e}. Using placeholder.")
            self.icon_label.setText("[?]") # Fallback text icon
            self.icon_label.setStyleSheet(f"color: {icon_color}; font-size: 24pt;")

        frame_layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignCenter) # Center vertically

        # Value and Title Layout (Vertical)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2) # Minimal spacing between value and title
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight) # Align text right

        self.value_label = QLabel("0")
        self.value_label.setObjectName("KpiValueLabel")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_layout.addWidget(self.value_label)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("KpiTitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_layout.addWidget(self.title_label)

        frame_layout.addLayout(text_layout, 1) # Text takes remaining space
        main_layout.addWidget(frame) # Add styled frame to main layout

        # Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 35)) # Slightly softer shadow
        shadow.setOffset(0, 2)
        frame.setGraphicsEffect(shadow)


    def set_value(self, value):
        try:
            # Format without currency symbol, with commas, no decimals
            formatted_value = f"{int(value):,}"
        except (ValueError, TypeError):
            formatted_value = "N/A"
        self.value_label.setText(formatted_value)


# --- Main Financial Analysis Widget ---
class FinancialAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        # Configure pyqtgraph global options
        pg.setConfigOption('background', COLOR_CHART_BG)
        pg.setConfigOption('foreground', COLOR_TEXT_DARK) # Default foreground for text items
        pg.setConfigOptions(antialias=True)             # Enable Antialiasing
        
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Financial Analysis Dashboard")
        self.setMinimumSize(1000, 800) # Adjusted min height
        self.init_ui()
        if MODEL_AVAILABLE:
            self.load_data()
        else:
            print("Analysis Model not available. Cannot load data.")
            # TODO: Display a message in the UI if model is unavailable

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15) # Slightly reduced margins
        main_layout.setSpacing(18) # Consistent spacing

        # --- KPI Section ---
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)

        # Use relevant icons and colors
        self.kpi_today = StatCard("Collected Today", "fa5s.sun", COLOR_WARNING)
        self.kpi_week = StatCard("Collected This Week", "fa5s.calendar-week", COLOR_SUCCESS)
        self.kpi_month = StatCard("Collected This Month", "fa5s.calendar-alt", COLOR_ACCENT)

        kpi_layout.addWidget(self.kpi_today)
        kpi_layout.addWidget(self.kpi_week)
        kpi_layout.addWidget(self.kpi_month)
        kpi_layout.addStretch(1)

        main_layout.addLayout(kpi_layout)

        # --- Filters Row ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        filter_layout.addStretch(1) # Push filters to the right

        combo_label = QLabel("Trend Period:")
        combo_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9pt;")
        filter_layout.addWidget(combo_label)

        self.period_combo = QComboBox()
        self.period_combo.addItems(['Month', 'Week', 'Day'])
        self.period_combo.setCurrentText("Month")
        self.period_combo.setMinimumWidth(120) # Reduced width
        if MODEL_AVAILABLE:
             self.period_combo.currentTextChanged.connect(lambda text: self.load_revenue_analysis(self.revenue_plot, text.lower()))
        filter_layout.addWidget(self.period_combo)

        filter_layout.addSpacing(20) # Space between controls

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Price Deviations...")
        self.search_bar.setFixedWidth(200)
        if MODEL_AVAILABLE:
             self.search_bar.textChanged.connect(self.filter_table)
        filter_layout.addWidget(self.search_bar)

        main_layout.addLayout(filter_layout)


        # --- Main Content Area (Charts/Tables in a QHBoxLayout) ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        # Left Column (Revenue Trend + Service Revenue)
        left_col_layout = QVBoxLayout()
        left_col_layout.setSpacing(18)

        # Revenue Trend Chart
        revenue_frame = QFrame()
        revenue_frame.setObjectName("MainFrame")
        # revenue_frame.setMinimumHeight(300) # Remove fixed min heights for flexibility
        revenue_layout = QVBoxLayout(revenue_frame)
        revenue_layout.setContentsMargins(8, 8, 8, 8) # Inner padding
        self.revenue_plot = self._create_plotwidget() # Helper to create plots
        revenue_layout.addWidget(self.revenue_plot)
        left_col_layout.addWidget(revenue_frame, 1) # Takes expanding space vertically


        # Revenue by Service Chart
        service_rev_frame = QFrame()
        service_rev_frame.setObjectName("MainFrame")
        # service_rev_frame.setMinimumHeight(280)
        service_rev_layout = QVBoxLayout(service_rev_frame)
        service_rev_layout.setContentsMargins(8, 8, 8, 8)
        self.service_rev_plot = self._create_plotwidget() # Helper
        service_rev_layout.addWidget(self.service_rev_plot)
        left_col_layout.addWidget(service_rev_frame, 1) # Takes expanding space vertically

        content_layout.addLayout(left_col_layout, 6) # Left column takes 60% width


        # Right Column (Price Deviation Table)
        deviation_frame = QFrame()
        deviation_frame.setObjectName("MainFrame")
        deviation_layout = QVBoxLayout(deviation_frame)
        deviation_layout.setContentsMargins(15, 15, 15, 15) # More padding for table frame
        deviation_layout.setSpacing(10)

        deviation_title = QLabel("Price Deviation Analysis")
        deviation_title.setObjectName("SectionTitleLabel")
        deviation_layout.addWidget(deviation_title)

        self.deviation_table = QTableWidget()
        self.deviation_table.setColumnCount(5)
        self.deviation_table.setHorizontalHeaderLabels(['Name', 'Default Price', 'Avg Charged', 'Avg Deviation', 'Count'])
        self.deviation_table.verticalHeader().setVisible(False)
        self.deviation_table.setAlternatingRowColors(True); self.deviation_table.setShowGrid(False)
        self.deviation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.deviation_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.deviation_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.deviation_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hdr_view = self.deviation_table.horizontalHeader()
        hdr_view.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hdr_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Name column stretches
        for i in range(1, 5): # Resize other columns to contents
             hdr_view.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setFixedHeight(35) # Slimmer header
        deviation_layout.addWidget(self.deviation_table, 1) # Table takes available space

        content_layout.addWidget(deviation_frame, 4) # Right column takes 40% width

        main_layout.addLayout(content_layout, 1) # Content takes expanding space

    def _create_plotwidget(self):
        """Helper function to create and configure a PlotWidget."""
        plot = pg.PlotWidget(background=None)
        plot.getPlotItem().getViewBox().setBackgroundColor(COLOR_CHART_BG)
        plot.showGrid(x=True, y=True, alpha=0.15)
        plot.getAxis('bottom').setPen(pg.mkPen(color=COLOR_BORDER, width=1))
        plot.getAxis('left').setPen(pg.mkPen(color=COLOR_BORDER, width=1))
        plot.getAxis('bottom').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))
        plot.getAxis('left').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))
        plot.getPlotItem().getViewBox().setBorder(None)
        plot.setAntialiasing(True)
        plot.getPlotItem().getViewBox().setMouseEnabled(x=False, y=False) # Disable scroll/pan
        plot.getPlotItem().layout.setContentsMargins(5, 5, 5, 5) # T, R, B, L - minimal padding inside plot

        # --- Disable Scientific Notation ---
        plot.getAxis('left').enableAutoSIPrefix(False)
        plot.getAxis('bottom').enableAutoSIPrefix(False)
        # -----------------------------------
        return plot

    def load_data(self):
        """Load data for all components."""
        if not MODEL_AVAILABLE: return

        # Load KPIs
        try:
            self.kpi_today.set_value(get_revenue_today())
            self.kpi_week.set_value(get_revenue_this_week())
            self.kpi_month.set_value(get_revenue_this_month())
        except Exception as e:
            print(f"Error loading KPI data: {e}")
            self.kpi_today.set_value("Error") # Show error on card
            self.kpi_week.set_value("Error")
            self.kpi_month.set_value("Error")

        self.load_revenue_analysis(self.revenue_plot, self.period_combo.currentText().lower())
        self.load_price_deviation(self.deviation_table)
        self.load_revenue_by_service(self.service_rev_plot)


    def load_revenue_analysis(self, plot, period):
        plot.clear(); plot.setTitle("")
        if not MODEL_AVAILABLE: return

        try: data = get_revenue_analysis(period)
        except Exception as e: print(f"ERROR loading revenue data: {e}"); data = []

        if not data or pd.DataFrame(data).empty:
            text = pg.TextItem(f"No data for {period} view", color=COLOR_TEXT_MUTED, anchor=(0.5, 0.5)); plot.addItem(text)
            plot.setTitle(f"Revenue Trends ({period.capitalize()})", color=COLOR_PRIMARY, size="11pt", bold=True); return

        try:
            df = pd.DataFrame(data)
            if not all(col in df.columns for col in ['time_period', 'billed_amount', 'collected_amount']):
                 print("ERROR: Revenue data missing columns."); return
            df['billed_amount'] = pd.to_numeric(df['billed_amount'], errors='coerce').fillna(0)
            df['collected_amount'] = pd.to_numeric(df['collected_amount'], errors='coerce').fillna(0)
            unique_periods = df['time_period'].astype(str).unique()
            period_to_index = {p: i for i, p in enumerate(unique_periods)}
            df['x_index'] = df['time_period'].astype(str).map(period_to_index)
            x = df['x_index'].values; billed = df['billed_amount'].values; collected = df['collected_amount'].values
        except Exception as e: print(f"ERROR processing revenue data: {e}"); return

        # Styling
        pen_billed = pg.mkPen(color=CHART_COLORS_DENTAL[0], width=3); pen_collected = pg.mkPen(color=CHART_COLORS_DENTAL[1], width=3)
        gradient_billed = QLinearGradient(0,0,0,1); gradient_billed.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        gradient_billed.setColorAt(0.0, QColor(CHART_COLORS_DENTAL[0]+'60')); gradient_billed.setColorAt(1.0, QColor(CHART_COLORS_DENTAL[0]+'05')); brush_billed = QBrush(gradient_billed)
        gradient_collected = QLinearGradient(0,0,0,1); gradient_collected.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        gradient_collected.setColorAt(0.0, QColor(CHART_COLORS_DENTAL[1]+'60')); gradient_collected.setColorAt(1.0, QColor(CHART_COLORS_DENTAL[1]+'05')); brush_collected = QBrush(gradient_collected)

        billed_curve = plot.plot(x, billed, pen=pen_billed, name='Billed'); fill_billed = pg.FillBetweenItem(billed_curve, pg.PlotDataItem(x, np.zeros_like(x)), brush=brush_billed); plot.addItem(fill_billed)
        collected_curve = plot.plot(x, collected, pen=pen_collected, name='Collected'); fill_collected = pg.FillBetweenItem(collected_curve, pg.PlotDataItem(x, np.zeros_like(x)), brush=brush_collected); plot.addItem(fill_collected)

        if len(x) < 25: # Markers
             marker_size = 6; marker_pen = pg.mkPen(color=COLOR_CHART_BG, width=1.5)
             billed_curve.setSymbol('o'); billed_curve.setSymbolSize(marker_size); billed_curve.setSymbolPen(marker_pen); billed_curve.setSymbolBrush(pg.mkBrush(color=CHART_COLORS_DENTAL[0]))
             collected_curve.setSymbol('o'); collected_curve.setSymbolSize(marker_size); collected_curve.setSymbolPen(marker_pen); collected_curve.setSymbolBrush(pg.mkBrush(color=CHART_COLORS_DENTAL[1]))

        ticks = [[(i, p) for p, i in period_to_index.items()]];
        try: plot.getAxis('bottom').setTicks(ticks)
        except Exception as e: print(f"Tick Error: {e}"); plot.getAxis('bottom').setTicks(None)

        plot.getAxis('bottom').setStyle(tickTextOffset=8, tickFont=QFont(FONT_REGULAR, 7)) # Smaller tick font
        plot.getAxis('left').setStyle(tickFont=QFont(FONT_REGULAR, 8))
        plot.getAxis('left').setWidth(55) # Adjust width needed for numbers without SI prefix
        plot.setLabel('left', 'Amount', color=COLOR_TEXT_DARK, size='9pt')
        plot.setLabel('bottom', 'Time Period', color=COLOR_TEXT_DARK, size='9pt')
        plot.setTitle(f"Revenue Trends ({period.capitalize()})", color=COLOR_PRIMARY, size="11pt", bold=True)

        # Add legend only if there's data
        if len(x) > 0:
            legend = plot.addLegend(offset=(-15, 5), brush=pg.mkBrush(COLOR_CHART_BG+'D0'), pen=pg.mkPen(COLOR_BORDER, width=0.5), labelTextSize='8pt')
            legend.setLabelTextColor(COLOR_TEXT_DARK)

        plot.showGrid(x=True, y=True, alpha=0.15)
        y_max = max(billed.max() if len(billed)>0 else 0, collected.max() if len(collected)>0 else 0)
        plot.getViewBox().setLimits(xMin=-0.5, xMax=len(x)-0.5, yMin=0 - y_max*0.05, yMax=y_max*1.05)
        plot.getViewBox().autoRange(padding=0.02) # Adjust padding

    def load_price_deviation(self, table):
        table.setRowCount(0)
        if not MODEL_AVAILABLE: return

        try: data = get_price_deviation_analysis()
        except Exception as e: print(f"ERROR loading price deviation: {e}"); data = {'services': [], 'medications': []}

        if not isinstance(data, dict): print("ERROR: Price deviation data format invalid."); return
        self.all_data = data.get('services', []) + data.get('medications', [])
        if not self.all_data: print("No price deviation data."); return

        table.setRowCount(len(self.all_data))
        number_font = QFont(FONT_REGULAR, 9)
        bold_font = QFont(FONT_MEDIUM, 9) # Use medium for name

        for row, entry in enumerate(self.all_data):
             name = entry.get('name', 'N/A')
             default_price = entry.get('default_price', 0); avg_charged = entry.get('avg_charged', 0)
             avg_deviation = entry.get('avg_deviation', 0); count = entry.get('count', 0)

             name_item = QTableWidgetItem(str(name)); name_item.setFont(bold_font)
             default_price_item = QTableWidgetItem(f"{default_price:,.2f}")
             avg_charged_item = QTableWidgetItem(f"{avg_charged:,.2f}")
             avg_deviation_item = QTableWidgetItem(f"{avg_deviation:,.2f}")
             count_item = QTableWidgetItem(str(count))

             # Align and set font for numeric columns
             for item in [default_price_item, avg_charged_item, avg_deviation_item, count_item]:
                 item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                 item.setFont(number_font)

             # Color deviation
             if avg_deviation > 1: avg_deviation_item.setForeground(QColor(COLOR_SUCCESS))
             elif avg_deviation < -1: avg_deviation_item.setForeground(QColor(COLOR_WARNING))
             else: avg_deviation_item.setForeground(QColor(COLOR_TEXT_MUTED))

             table.setItem(row, 0, name_item); table.setItem(row, 1, default_price_item)
             table.setItem(row, 2, avg_charged_item); table.setItem(row, 3, avg_deviation_item)
             table.setItem(row, 4, count_item)

        # Resize columns after populating
        table.resizeColumnsToContents()
        # Ensure name column stretches if there's extra space
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)


    def load_revenue_by_service(self, plot, limit=10):
        plot.clear(); plot.setTitle("")
        if not MODEL_AVAILABLE: return

        try: data = get_revenue_by_service(limit=limit)
        except Exception as e: print(f"ERROR loading revenue by service: {e}"); data = []

        if not data:
            text = pg.TextItem("No service revenue data", color=COLOR_TEXT_MUTED, anchor=(0.5, 0.5)); plot.addItem(text)
            plot.setTitle("Revenue by Top Service", color=COLOR_PRIMARY, size="11pt", bold=True); return

        try:
            df = pd.DataFrame(data);
            if not all(col in df.columns for col in ['name', 'total_revenue']): print("ERROR: Service revenue data missing columns."); return
            df['total_revenue'] = pd.to_numeric(df['total_revenue'], errors='coerce').fillna(0)
            df = df[df['total_revenue'] > 0].sort_values('total_revenue', ascending=True) # Only show services with revenue
            if df.empty: raise ValueError("No services with positive revenue found")

            service_names = df['name'].tolist(); revenues = df['total_revenue'].values
            y_ticks = list(range(len(service_names)))
        except Exception as e: print(f"ERROR processing service revenue data: {e}"); return

        bar_item = pg.BarGraphItem(x0=0, y=y_ticks, height=0.6, width=revenues,
            brush=pg.mkBrush(color=CHART_COLORS_DENTAL[5]+'B0'), # Use another theme color
            pen=pg.mkPen(color=CHART_COLORS_DENTAL[5], width=1))
        plot.addItem(bar_item)

        plot.getAxis('left').setTicks([list(zip(y_ticks, service_names))])
        plot.getAxis('left').setStyle(tickFont=QFont(FONT_REGULAR, 8))
        plot.getAxis('bottom').setStyle(tickFont=QFont(FONT_REGULAR, 8))
        plot.setLabel('left', 'Service', color=COLOR_TEXT_DARK, size='9pt')
        plot.setLabel('bottom', 'Total Revenue', color=COLOR_TEXT_DARK, size='9pt')
        plot.setTitle(f"Revenue by Top {len(service_names)} Services", color=COLOR_PRIMARY, size="11pt", bold=True)

        plot.getViewBox().setLimits(xMin=0, yMin=-0.5, yMax=len(y_ticks)-0.5)
        plot.getViewBox().autoRange(padding=0.05)


    def filter_table(self, txt):
        search_term = txt.lower().strip()
        if not hasattr(self, 'all_data') or not self.all_data: return
        for r in range(self.deviation_table.rowCount()):
            item = self.deviation_table.item(r, 0)
            should_hide = not (item and search_term in item.text().lower())
            self.deviation_table.setRowHidden(r, should_hide)

    def wheelEvent(self, event): event.ignore() # Disable wheel scroll globally

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Optional: Explicitly load font if needed
    # QFontDatabase.addApplicationFont("path/to/Roboto-Regular.ttf") # etc.
    window = FinancialAnalysis()
    window.showMaximized() # Show maximized for better view of dashboard
    # window.show()
    sys.exit(app.exec())