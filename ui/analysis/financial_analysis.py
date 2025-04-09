import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QApplication, QGraphicsDropShadowEffect, QComboBox,
    QLineEdit, QLabel, QSizePolicy  # Added QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QPointF
from PyQt6.QtGui import QColor, QFont, QPalette, QLinearGradient, QBrush, QPen, QIcon # Added QIcon
import pyqtgraph as pg
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta # For date calculations if needed here

# --- Import your data fetching functions ---
# Make sure analysis_model.py is accessible (e.g., in the same directory or added to sys.path)
try:
    from model.analysis_model import (
        get_revenue_analysis,
        get_price_deviation_analysis,
        get_revenue_today,
        get_revenue_this_week,
        get_revenue_this_month,
        get_revenue_by_service # Import the new function
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


# --- Color Palette (keep as is) ---
COLOR_PRIMARY = "#2c3e50"; COLOR_SECONDARY = "#ecf0f1"; COLOR_ACCENT = "#3498db"
COLOR_SUCCESS = "#27ae60"; COLOR_WARNING = "#e67e22"; COLOR_DANGER = "#e74c3c"
COLOR_INFO = "#8e44ad"; COLOR_TEXT_LIGHT = "#ffffff"; COLOR_TEXT_DARK = "#34495e"
COLOR_TEXT_MUTED = "#7f8c8d"; COLOR_BORDER = "#bdc3c7"; COLOR_CHART_BG = "#ffffff"
COLOR_TABLE_ALT_ROW = "#f8f9f9"; COLOR_HOVER = "#4a6fa5"
CHART_COLORS_DENTAL = ["#1E90FF","#32CD32","#FFD700","#FF4500","#C0C0C0","#20B2AA"]
# Add colors for KPI cards
KPI_BG_COLOR = COLOR_CHART_BG
KPI_BORDER_COLOR = COLOR_BORDER
KPI_ICON_COLOR = COLOR_ACCENT
KPI_VALUE_COLOR = COLOR_PRIMARY
KPI_TITLE_COLOR = COLOR_TEXT_MUTED


# --- Stylesheet (Minor Adjustments) ---
DASHBOARD_STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_TEXT_DARK};
    font-family: 'Roboto', 'Segoe UI', sans-serif;
    font-size: 11pt;
}}
QFrame {{ /* General frame styling */
    border-radius: 12px;
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
}}
/* Style specific frames using object names */
#KpiCard QFrame {{
    background-color: {KPI_BG_COLOR};
    border: 1px solid {KPI_BORDER_COLOR};
    border-radius: 10px;
}}
#KpiCard QLabel#ValueLabel {{
    font-size: 20pt;
    font-weight: 600;
    color: {KPI_VALUE_COLOR};
}}
#KpiCard QLabel#TitleLabel {{
    font-size: 9pt;
    color: {KPI_TITLE_COLOR};
    font-weight: 500;
}}
#KpiCard QLabel#IconLabel {{
    font-size: 24pt; /* Adjust icon size if using text/emoji */
    color: {KPI_ICON_COLOR};
    min-width: 30px; /* Ensure space for icon */
}}
QTableWidget {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    gridline-color: {COLOR_BORDER}; alternate-background-color: {COLOR_TABLE_ALT_ROW};
    border-radius: 8px; font-size: 10pt;
}}
QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {COLOR_BORDER}; }}
QTableWidget::item:selected {{
    background-color: {COLOR_ACCENT}30; color: {COLOR_TEXT_DARK};
    border-left: 3px solid {COLOR_ACCENT};
}}
QHeaderView::section {{
    background-color: {COLOR_PRIMARY}; color: {COLOR_TEXT_LIGHT};
    padding: 12px 8px; font-weight: 600; border: none;
    border-bottom: 1px solid {COLOR_PRIMARY}; font-size: 10pt;
}}
QHeaderView {{ border: none; border-bottom: 1px solid {COLOR_BORDER}; }}
QTableCornerButton::section {{ background-color: {COLOR_PRIMARY}; border: none; }}
QComboBox {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    border-radius: 6px; padding: 8px 25px 8px 12px; font-size: 10pt;
    color: {COLOR_TEXT_DARK}; min-width: 150px;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: top right; width: 20px;
    border-left-width: 1px; border-left-color: {COLOR_BORDER}; border-left-style: solid;
    border-top-right-radius: 6px; border-bottom-right-radius: 6px;
}}
/* QComboBox::down-arrow - Consider using QStyle standard arrow or qtawesome */
QComboBox:hover {{ background-color: {COLOR_SECONDARY}; border-color: {COLOR_ACCENT}; }}
QComboBox QAbstractItemView {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    selection-background-color: {COLOR_ACCENT}30; selection-color: {COLOR_TEXT_DARK};
    color: {COLOR_TEXT_DARK}; padding: 5px;
}}
QLineEdit {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    border-radius: 6px; padding: 8px 12px; font-size: 10pt; color: {COLOR_TEXT_DARK};
}}
QLineEdit:focus {{ border: 1px solid {COLOR_ACCENT}; }}
PlotWidget {{ border-radius: 12px; border: none; }}
AxisItem {{ /* Styling done via code */ }}
LabelItem {{ color: {COLOR_TEXT_MUTED}; }}
ViewBox {{ border-radius: 8px; border: none; }}
"""

# --- Reusable KPI Card Widget ---
class StatCard(QWidget):
    def __init__(self, title, icon_placeholder="[I]", parent=None):
        super().__init__(parent)
        self.setObjectName("KpiCard") # For specific styling
        self.setMinimumWidth(180) # Ensure cards have some width
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Expand horizontally

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10) # Padding L,T,R,B
        layout.setSpacing(10)

        # Frame for background and border
        frame = QFrame(self)
        frame.setObjectName("CardFrame") # If needed for more specific frame styling
        frame_layout = QHBoxLayout(frame) # Layout inside the frame
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(10)

        # Icon Label (using placeholder text)
        self.icon_label = QLabel(icon_placeholder)
        self.icon_label.setObjectName("IconLabel")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # TODO: Replace placeholder with actual icon:
        # self.icon_label.setPixmap(QIcon("path/to/icon.png").pixmap(QSize(24, 24)))
        # self.icon_label.setScaledContents(True)
        frame_layout.addWidget(self.icon_label, 0) # Icon takes minimal space

        # Value and Title Layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.addStretch(1) # Push text down slightly

        self.value_label = QLabel("0")
        self.value_label.setObjectName("ValueLabel")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_layout.addWidget(self.value_label)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_layout.addWidget(self.title_label)
        text_layout.addStretch(1)

        frame_layout.addLayout(text_layout, 1) # Text takes expanding space
        layout.addWidget(frame) # Add styled frame to main layout

    def set_value(self, value):
        try:
            # Format without currency symbol, with commas, no decimals
            self.value_label.setText(f"{int(value):,}")
        except (ValueError, TypeError):
            self.value_label.setText("N/A")

# --- Main Financial Analysis Widget ---
class FinancialAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        pg.setConfigOption('background', COLOR_CHART_BG)
        pg.setConfigOption('foreground', COLOR_TEXT_DARK)
        pg.setConfigOptions(antialias=True)

        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Financial Analysis Dashboard")
        self.setMinimumSize(1000, 850) # Increased min height for KPIs + new chart
        self.init_ui()
        if MODEL_AVAILABLE:
            self.load_data()
        else:
            print("Analysis Model not available. Cannot load data.")
            # Optionally display a message to the user in the UI

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- KPI Section ---
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)

        self.kpi_today = StatCard("Revenue Today", "[📅]") # Placeholder icons
        self.kpi_week = StatCard("Revenue This Week", "[ W ]")
        self.kpi_month = StatCard("Revenue This Month", "[ M ]")

        kpi_layout.addWidget(self.kpi_today)
        kpi_layout.addWidget(self.kpi_week)
        kpi_layout.addWidget(self.kpi_month)
        kpi_layout.addStretch(1) # Push cards to the left

        main_layout.addLayout(kpi_layout)

        # --- Filters Row ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)
        filter_layout.addStretch(1) # Push filters to the right

        self.period_combo = QComboBox()
        self.period_combo.addItems(['Month', 'Week', 'Day'])
        self.period_combo.setCurrentText("Month")
        self.period_combo.setMinimumWidth(180)
        if MODEL_AVAILABLE:
             self.period_combo.currentTextChanged.connect(lambda text: self.load_revenue_analysis(self.revenue_plot, text.lower()))
        filter_layout.addWidget(self.period_combo, 0, Qt.AlignmentFlag.AlignRight)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Deviations...")
        self.search_bar.setFixedWidth(220) # Slightly wider search
        if MODEL_AVAILABLE:
             self.search_bar.textChanged.connect(self.filter_table)
        filter_layout.addWidget(self.search_bar, 0, Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(filter_layout)


        # --- Main Content Area (Charts/Tables) ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left: Revenue Trend Chart
        revenue_frame = QFrame()
        revenue_frame.setMinimumHeight(280) # Adjusted height
        revenue_frame.setMaximumHeight(350)
        revenue_layout = QVBoxLayout(revenue_frame)
        revenue_layout.setContentsMargins(5, 5, 5, 5) # Reduced margins slightly
        revenue_layout.setSpacing(0)

        self.revenue_plot = pg.PlotWidget(background=None)
        self.revenue_plot.getPlotItem().getViewBox().setBackgroundColor(COLOR_CHART_BG)
        self.revenue_plot.showGrid(x=True, y=True, alpha=0.15)
        self.revenue_plot.getAxis('bottom').setPen(pg.mkPen(color=COLOR_BORDER, width=1))
        self.revenue_plot.getAxis('left').setPen(pg.mkPen(color=COLOR_BORDER, width=1))
        self.revenue_plot.getAxis('bottom').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))
        self.revenue_plot.getAxis('left').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))
        # Remove currency symbol from label
        self.revenue_plot.setLabel('left', 'Amount', color=COLOR_TEXT_DARK, **{'font-size': '10pt'})
        self.revenue_plot.setLabel('bottom', 'Time Period', color=COLOR_TEXT_DARK, **{'font-size': '10pt'})
        self.revenue_plot.getPlotItem().getViewBox().setBorder(None)
        self.revenue_plot.setAntialiasing(True)
        self.revenue_plot.getPlotItem().getViewBox().setMouseEnabled(x=False, y=False) # Disable scroll/pan
        revenue_layout.addWidget(self.revenue_plot)
        self.revenue_plot.getPlotItem().layout.setContentsMargins(10, 10, 10, 10) # T, R, B, L Adjusted margins

        shadow_rev = QGraphicsDropShadowEffect(blurRadius=15, xOffset=0, yOffset=2, color=QColor(0,0,0,40))
        revenue_frame.setGraphicsEffect(shadow_rev)
        content_layout.addWidget(revenue_frame, 1) # Equal stretch


        # Right: Price Deviation Table
        deviation_frame = QFrame()
        deviation_frame.setMinimumHeight(280) # Match chart height
        deviation_frame.setMaximumHeight(350)
        deviation_layout = QVBoxLayout(deviation_frame)
        deviation_layout.setContentsMargins(15, 15, 15, 15)
        deviation_layout.setSpacing(10)

        deviation_title = QLabel("Price Deviation Analysis", styleSheet=f"font-size: 12pt; font-weight: bold; color: {COLOR_TEXT_DARK}; margin-bottom: 5px;")
        deviation_layout.addWidget(deviation_title)

        self.deviation_table = QTableWidget()
        self.deviation_table.setColumnCount(5)
        # Remove currency symbol from headers
        self.deviation_table.setHorizontalHeaderLabels(['Name', 'Default Price', 'Avg Charged', 'Avg Deviation', 'Count'])
        self.deviation_table.verticalHeader().setVisible(False)
        self.deviation_table.setAlternatingRowColors(True); self.deviation_table.setShowGrid(False)
        self.deviation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.deviation_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.deviation_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.deviation_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hdr_view = self.deviation_table.horizontalHeader()
        hdr_view.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hdr_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setFixedHeight(40) # Reduced header height slightly
        deviation_layout.addWidget(self.deviation_table)

        shadow_dev = QGraphicsDropShadowEffect(blurRadius=15, xOffset=0, yOffset=2, color=QColor(0,0,0,40))
        deviation_frame.setGraphicsEffect(shadow_dev)
        content_layout.addWidget(deviation_frame, 1) # Equal stretch

        main_layout.addLayout(content_layout) # Add row for chart/table


        # --- Additional Analysis Section ---
        service_rev_frame = QFrame()
        service_rev_frame.setMinimumHeight(250) # Height for the new chart
        service_rev_layout = QVBoxLayout(service_rev_frame)
        service_rev_layout.setContentsMargins(5, 5, 5, 5)

        self.service_rev_plot = pg.PlotWidget(background=None)
        self.service_rev_plot.getPlotItem().getViewBox().setBackgroundColor(COLOR_CHART_BG)
        self.service_rev_plot.getAxis('bottom').setPen(pg.mkPen(color=COLOR_BORDER, width=1))
        self.service_rev_plot.getAxis('left').setPen(pg.mkPen(color=COLOR_BORDER, width=1))
        self.service_rev_plot.getAxis('bottom').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))
        self.service_rev_plot.getAxis('left').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))
        self.service_rev_plot.setLabel('left', 'Revenue', color=COLOR_TEXT_DARK, **{'font-size': '10pt'})
        self.service_rev_plot.setLabel('bottom', 'Service', color=COLOR_TEXT_DARK, **{'font-size': '10pt'})
        self.service_rev_plot.getPlotItem().getViewBox().setBorder(None)
        self.service_rev_plot.setAntialiasing(True)
        self.service_rev_plot.getPlotItem().getViewBox().setMouseEnabled(x=False, y=False) # Disable scroll/pan
        service_rev_layout.addWidget(self.service_rev_plot)
        self.service_rev_plot.getPlotItem().layout.setContentsMargins(10, 10, 10, 10)

        shadow_srv = QGraphicsDropShadowEffect(blurRadius=15, xOffset=0, yOffset=2, color=QColor(0,0,0,40))
        service_rev_frame.setGraphicsEffect(shadow_srv)

        main_layout.addWidget(service_rev_frame) # Add the new chart frame below

        main_layout.addStretch(1) # Add stretch at the end


    def load_data(self):
        """Load data for all components."""
        if not MODEL_AVAILABLE: return

        # Load KPIs
        try:
            rev_today = get_revenue_today()
            rev_week = get_revenue_this_week()
            rev_month = get_revenue_this_month()
            self.kpi_today.set_value(rev_today)
            self.kpi_week.set_value(rev_week)
            self.kpi_month.set_value(rev_month)
        except Exception as e:
            print(f"Error loading KPI data: {e}")
            self.kpi_today.set_value("Error")
            self.kpi_week.set_value("Error")
            self.kpi_month.set_value("Error")

        # Load main revenue chart (default period)
        self.load_revenue_analysis(self.revenue_plot, self.period_combo.currentText().lower())

        # Load deviation table
        self.load_price_deviation(self.deviation_table)

        # Load revenue by service chart
        self.load_revenue_by_service(self.service_rev_plot)


    def load_revenue_analysis(self, plot, period):
        plot.clear(); plot.setTitle("")
        if not MODEL_AVAILABLE: return

        try: data = get_revenue_analysis(period)
        except Exception as e: print(f"ERROR loading revenue data: {e}"); data = []

        if not data or pd.DataFrame(data).empty:
            text = pg.TextItem(f"No data for {period} view.", color=COLOR_TEXT_MUTED, anchor=(0.5, 0.5))
            plot.addItem(text); plot.setTitle(f"Revenue Trends ({period.capitalize()})", color=COLOR_PRIMARY, size="12pt", bold=True)
            return

        try:
            df = pd.DataFrame(data)
            if not all(col in df.columns for col in ['time_period', 'billed_amount', 'collected_amount']):
                 print("ERROR: Revenue data missing columns."); return
            df['billed_amount'] = pd.to_numeric(df['billed_amount'], errors='coerce').fillna(0)
            df['collected_amount'] = pd.to_numeric(df['collected_amount'], errors='coerce').fillna(0)
            unique_periods = df['time_period'].astype(str).unique()
            period_to_index = {p: i for i, p in enumerate(unique_periods)}
            df['x_index'] = df['time_period'].astype(str).map(period_to_index)
            x = df['x_index'].values
            billed = df['billed_amount'].values
            collected = df['collected_amount'].values
        except Exception as e: print(f"ERROR processing revenue data: {e}"); return

        # --- Styling ---
        pen_billed = pg.mkPen(color=CHART_COLORS_DENTAL[0], width=3)
        pen_collected = pg.mkPen(color=CHART_COLORS_DENTAL[1], width=3)
        gradient_billed = QLinearGradient(0, 0, 0, 1); gradient_billed.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        gradient_billed.setColorAt(0.0, QColor(CHART_COLORS_DENTAL[0] + '50')); gradient_billed.setColorAt(1.0, QColor(CHART_COLORS_DENTAL[0] + '05'))
        brush_billed = QBrush(gradient_billed)
        gradient_collected = QLinearGradient(0, 0, 0, 1); gradient_collected.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        gradient_collected.setColorAt(0.0, QColor(CHART_COLORS_DENTAL[1] + '50')); gradient_collected.setColorAt(1.0, QColor(CHART_COLORS_DENTAL[1] + '05'))
        brush_collected = QBrush(gradient_collected)

        billed_curve = plot.plot(x, billed, pen=pen_billed, name='Billed')
        fill_billed = pg.FillBetweenItem(billed_curve, pg.PlotDataItem(x, np.zeros_like(x)), brush=brush_billed); plot.addItem(fill_billed)
        collected_curve = plot.plot(x, collected, pen=pen_collected, name='Collected')
        fill_collected = pg.FillBetweenItem(collected_curve, pg.PlotDataItem(x, np.zeros_like(x)), brush=brush_collected); plot.addItem(fill_collected)

        if len(x) < 25: # Markers
             marker_size = 7; marker_pen = pg.mkPen(color=COLOR_CHART_BG, width=1)
             billed_curve.setSymbol('o'); billed_curve.setSymbolSize(marker_size); billed_curve.setSymbolPen(marker_pen); billed_curve.setSymbolBrush(pg.mkBrush(color=CHART_COLORS_DENTAL[0]))
             collected_curve.setSymbol('o'); collected_curve.setSymbolSize(marker_size); collected_curve.setSymbolPen(marker_pen); collected_curve.setSymbolBrush(pg.mkBrush(color=CHART_COLORS_DENTAL[1]))

        ticks = [[(i, p) for p, i in period_to_index.items()]]
        try: plot.getAxis('bottom').setTicks(ticks)
        except Exception as tick_error: print(f"Tick Error: {tick_error}"); plot.getAxis('bottom').setTicks(None)

        plot.getAxis('bottom').setStyle(tickTextOffset=10, tickFont=QFont('Roboto', 7)) # Smaller font for ticks
        plot.getAxis('left').setStyle(tickFont=QFont('Roboto', 8), tickTextWidth=40)
        plot.getAxis('left').setWidth(50)
        # Remove currency symbol from label
        plot.getAxis('left').setLabel('Amount', color=COLOR_TEXT_DARK, **{'font-size': '10pt'})
        plot.getAxis('bottom').setLabel('Time Period', color=COLOR_TEXT_DARK, **{'font-size': '10pt'})

        plot.setTitle(f"Revenue Trends ({period.capitalize()})", color=COLOR_PRIMARY, size="12pt", bold=True) # Slightly smaller title

        legend = plot.addLegend(offset=(-10, 10), brush=pg.mkBrush(COLOR_CHART_BG+'E0'), pen=pg.mkPen(COLOR_BORDER, width=0.5))
        legend.setLabelTextColor(COLOR_TEXT_DARK)

        plot.showGrid(x=True, y=True, alpha=0.15)
        y_max = max(billed.max() if len(billed)>0 else 0, collected.max() if len(collected)>0 else 0)
        plot.getViewBox().setLimits(xMin=-0.5, xMax=len(x)-0.5, yMin=0 - y_max*0.05, yMax=y_max*1.05)


    def load_price_deviation(self, table):
        table.setRowCount(0)
        if not MODEL_AVAILABLE: return

        try: data = get_price_deviation_analysis()
        except Exception as e: print(f"ERROR loading price deviation: {e}"); data = {'services': [], 'medications': []}

        if not isinstance(data, dict): print("ERROR: Price deviation data format invalid."); return
        self.all_data = data.get('services', []) + data.get('medications', [])
        if not self.all_data: print("No price deviation data."); return

        table.setRowCount(len(self.all_data))
        number_font = QFont('Roboto', 9)

        for row, entry in enumerate(self.all_data):
             name = entry.get('name', 'N/A')
             default_price = entry.get('default_price', 0)
             avg_charged = entry.get('avg_charged', 0)
             # Use the signed deviation from the model
             avg_deviation = entry.get('avg_deviation', 0) # Already calculated in updated model
             count = entry.get('count', 0)

             # Format without currency symbols
             name_item = QTableWidgetItem(str(name))
             default_price_item = QTableWidgetItem(f"{default_price:,.2f}")
             avg_charged_item = QTableWidgetItem(f"{avg_charged:,.2f}")
             avg_deviation_item = QTableWidgetItem(f"{avg_deviation:,.2f}")
             count_item = QTableWidgetItem(str(count))

             default_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); default_price_item.setFont(number_font)
             avg_charged_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); avg_charged_item.setFont(number_font)
             avg_deviation_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) # Font set below
             count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); count_item.setFont(number_font)

             if avg_deviation > 1: # Overcharged
                 avg_deviation_item.setForeground(QColor(COLOR_SUCCESS)); avg_deviation_item.setFont(number_font)
             elif avg_deviation < -1: # Undercharged
                 avg_deviation_item.setForeground(QColor(COLOR_WARNING)); avg_deviation_item.setFont(number_font)
             else: # Minimal deviation
                 avg_deviation_item.setForeground(QColor(COLOR_TEXT_MUTED)); avg_deviation_item.setFont(number_font)

             table.setItem(row, 0, name_item); table.setItem(row, 1, default_price_item)
             table.setItem(row, 2, avg_charged_item); table.setItem(row, 3, avg_deviation_item)
             table.setItem(row, 4, count_item)

        table.horizontalHeader().resizeSections(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)


    def load_revenue_by_service(self, plot, limit=10):
        """Loads data into the revenue-by-service bar chart."""
        plot.clear(); plot.setTitle("")
        if not MODEL_AVAILABLE: return

        try:
            data = get_revenue_by_service(limit=limit)
        except Exception as e:
            print(f"ERROR loading revenue by service: {e}")
            data = []

        if not data:
            text = pg.TextItem("No service revenue data", color=COLOR_TEXT_MUTED, anchor=(0.5, 0.5))
            plot.addItem(text)
            plot.setTitle("Revenue by Top Service", color=COLOR_PRIMARY, size="12pt", bold=True)
            return

        try:
            df = pd.DataFrame(data)
            if not all(col in df.columns for col in ['name', 'total_revenue']):
                print("ERROR: Service revenue data missing columns."); return
            df['total_revenue'] = pd.to_numeric(df['total_revenue'], errors='coerce').fillna(0)
            df = df.sort_values('total_revenue', ascending=True) # Sort for horizontal bar chart

            service_names = df['name'].tolist()
            revenues = df['total_revenue'].values
            y_ticks = list(range(len(service_names)))

        except Exception as e:
            print(f"ERROR processing service revenue data: {e}")
            return

        # Create Bar Chart
        bar_item = pg.BarGraphItem(
            x0=0, y=y_ticks, height=0.6, width=revenues, # x0=0 for horizontal bars starting at 0
            brush=pg.mkBrush(color=CHART_COLORS_DENTAL[2] + 'A0'), # Gold-ish, semi-transparent
            pen=pg.mkPen(color=CHART_COLORS_DENTAL[2], width=1)
        )
        plot.addItem(bar_item)

        # Customize Axes for Bar Chart
        plot.getAxis('left').setTicks([list(zip(y_ticks, service_names))])
        plot.getAxis('left').setStyle(tickFont=QFont('Roboto', 8))
        plot.getAxis('bottom').setStyle(tickFont=QFont('Roboto', 8))
        # Remove currency symbol from label
        plot.getAxis('bottom').setLabel('Total Revenue', color=COLOR_TEXT_DARK, **{'font-size': '10pt'})
        plot.getAxis('left').setLabel('Service', color=COLOR_TEXT_DARK, **{'font-size': '10pt'})
        plot.setTitle(f"Revenue by Top {len(service_names)} Services", color=COLOR_PRIMARY, size="12pt", bold=True)

        # Adjust view limits
        plot.getViewBox().setLimits(xMin=0, yMin=-0.5, yMax=len(y_ticks)-0.5)
        plot.getViewBox().autoRange(padding=0.05) # Add slight padding


    def filter_table(self, txt):
        search_term = txt.lower().strip()
        if not hasattr(self, 'all_data') or not self.all_data: return

        for r in range(self.deviation_table.rowCount()):
            item = self.deviation_table.item(r, 0)
            should_hide = True
            if item and search_term in item.text().lower(): should_hide = False
            self.deviation_table.setRowHidden(r, should_hide)

    def wheelEvent(self, event):
        # Prevent wheel scroll on the main widget background
        event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setStyle('Fusion') # Optional

    window = FinancialAnalysis()
    window.show()
    sys.exit(app.exec())