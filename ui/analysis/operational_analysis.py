# ui/analysis/operational_analysis_premium.py

import sys
import qtawesome as qta # Import Qtawesome
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QApplication, QGraphicsDropShadowEffect, QComboBox, QSizePolicy, QGridLayout,
    QHeaderView # Added QGridLayout, QSizePolicy, QHeaderView
)
from PyQt6.QtCore import Qt, QSize, QPointF
from PyQt6.QtGui import QColor, QFont, QPalette, QLinearGradient, QBrush, QPen, QIcon, QFontDatabase # Added QFontDatabase

import pyqtgraph as pg
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta

# --- Import your data fetching functions ---
try:
    from model.analysis_model import get_clinic_load_analysis, get_visit_trends
    MODEL_AVAILABLE = True
except ImportError as e:
    print(f"Error importing from analysis_model: {e}. Running with limited/no data.")
    MODEL_AVAILABLE = False
    # Define dummy functions if model is not available to prevent crashes
    def get_clinic_load_analysis(): return {'day_of_week': [], 'month': []}
    def get_visit_trends(period='month'): return []
# --- End Import ---


# --- Premium Color Palette & Theme (Teal, Gray, Gold Accents) ---
COLOR_PRIMARY = "#004D40" # Deep Teal Green
COLOR_SECONDARY = "#F5F5F5" # Light Gray Background
COLOR_ACCENT_TEAL = "#00897B" # Brighter Teal
COLOR_ACCENT_GOLD = "#FBC02D" # Gold/Amber Accent
COLOR_SUCCESS = "#4CAF50" # Green
COLOR_WARNING = "#FFA000" # Amber/Orange
COLOR_DANGER = "#D32F2F" # Red
COLOR_INFO = "#1976D2" # Blue Info
COLOR_TEXT_LIGHT = "#FFFFFF" # White
COLOR_TEXT_DARK = "#263238" # Very Dark Gray/Blue Text (Primary Dark)
COLOR_TEXT_MUTED = "#546E7A" # Muted Gray/Blue Text
COLOR_BORDER = "#CFD8DC" # Lighter Gray Border
COLOR_CHART_BG = "#FFFFFF" # White Chart Background
COLOR_HOVER_PRIMARY = "#00695C" # Darker Teal on hover
COLOR_HOVER_ACCENT = "#1DE9B6" # Lighter Teal/Aqua hover for accent elements
KPI_ICON_COLOR = COLOR_ACCENT_TEAL # Default Icon Color

# Chart Colors - Adjust as needed for specific charts
CHART_COLORS_OPERATIONAL = [COLOR_ACCENT_TEAL, COLOR_ACCENT_GOLD, "#4DD0E1", "#FF8A65", "#BA68C8", COLOR_PRIMARY]

# Font Setup (Similar to Financial Analysis)
# QFontDatabase.addApplicationFont("path/to/YourFont-Regular.ttf")
# QFontDatabase.addApplicationFont("path/to/YourFont-Medium.ttf")
# QFontDatabase.addApplicationFont("path/to/YourFont-Bold.ttf")
FONT_REGULAR = "Segoe UI" # Or your preferred font
FONT_MEDIUM = "Segoe UI Semibold"
FONT_BOLD = "Segoe UI Bold"


# --- Stylesheet (Premium) ---
DASHBOARD_STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_TEXT_DARK};
    font-family: '{FONT_REGULAR}', 'Arial', sans-serif;
    font-size: 10pt; /* Base font size */
}}
QFrame#MainFrame, QFrame#ChartFrame {{ /* Style the main content frames */
    border-radius: 10px;
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
}}
/* Style KPI Card Frame if you add StatCard later */
/*
QFrame#KpiCardFrame {{
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
}}
QLabel#KpiValueLabel {{ ... }}
QLabel#KpiTitleLabel {{ ... }}
QLabel#KpiIconLabel {{ ... }}
*/
QPushButton#refreshBtn {{
    background-color: {COLOR_ACCENT_TEAL};
    color: {COLOR_TEXT_LIGHT};
    border: none;
    border-radius: 6px;
    padding: 8px 18px; /* More padding */
    font-family: '{FONT_MEDIUM}', '{FONT_REGULAR}';
    font-size: 9pt;
    font-weight: 500;
    min-width: 120px;
}}
QPushButton#refreshBtn:hover {{
    background-color: {COLOR_HOVER_PRIMARY};
}}
QPushButton#refreshBtn:pressed {{
    background-color: {COLOR_PRIMARY};
}}
QComboBox {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    border-radius: 6px; padding: 7px 25px 7px 10px; /* Adjusted padding */
    font-size: 9pt; color: {COLOR_TEXT_DARK}; min-width: 120px;
    font-family: '{FONT_MEDIUM}', '{FONT_REGULAR}';
}}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: top right; width: 20px;
    border-left-width: 1px; border-left-color: {COLOR_BORDER}; border-left-style: solid;
    border-top-right-radius: 6px; border-bottom-right-radius: 6px;
    /* You might need a custom arrow icon here for premium feel */
}}
QComboBox:hover {{ border-color: {COLOR_ACCENT_TEAL}; }}
QComboBox QAbstractItemView {{
    background-color: {COLOR_CHART_BG}; border: 1px solid {COLOR_BORDER};
    selection-background-color: {COLOR_ACCENT_TEAL}30; selection-color: {COLOR_TEXT_DARK};
    color: {COLOR_TEXT_DARK}; padding: 4px; font-size: 9pt;
}}
PlotWidget {{ border-radius: 8px; border: none; }} /* Rounded corners inside frame */
AxisItem {{ /* Axis pen set via code */ }}
LabelItem {{ color: {COLOR_TEXT_MUTED}; font-size: 9pt; }}
ViewBox {{ border-radius: 8px; border: none; }}
QLabel#SectionTitleLabel {{ /* Style for titles above charts */
    font-family: '{FONT_BOLD}', '{FONT_REGULAR}';
    font-size: 12pt; /* Slightly larger */
    font-weight: 600;
    color: {COLOR_PRIMARY};
    margin-bottom: 8px; /* More space below title */
    margin-top: 5px;
    padding-left: 5px; /* Align slightly with chart padding */
}}
QLabel#MainTitleLabel {{ /* Style for the main dashboard title */
    font-family: '{FONT_BOLD}', '{FONT_REGULAR}';
    font-size: 18pt;
    font-weight: 700;
    color: {COLOR_PRIMARY};
    margin-bottom: 15px; /* Space below main title */
}}
"""


# --- Main Operational Analysis Widget (Premium) ---
class OperationalAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        # Configure pyqtgraph global options
        pg.setConfigOption('background', COLOR_CHART_BG)
        pg.setConfigOption('foreground', COLOR_TEXT_DARK) # Default foreground
        pg.setConfigOptions(antialias=True)             # Enable Antialiasing

        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Operational Analysis Dashboard")
        self.setMinimumSize(1000, 800) # Ensure enough space
        self.init_ui()
        self.load_data() # Load initial data

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20) # Generous margins
        main_layout.setSpacing(20) # Consistent spacing

    


        # --- Main Content Area (Consider QGridLayout for more complex layouts) ---
        # Using QVBoxLayout for now for Day / Month / Trend stacking
        content_layout = QVBoxLayout()
        content_layout.setSpacing(18)

        # --- Row 1: Visits by Day and Month (Side-by-side) ---
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(18)

        # Visits by Day of Week Chart
        day_frame = QFrame(objectName="ChartFrame")
        day_frame_layout = QVBoxLayout(day_frame)
        day_frame_layout.setContentsMargins(15, 15, 15, 15) # Inner padding
        day_title = QLabel("Visits by Day of Week", objectName="SectionTitleLabel")
        self.day_plot = self._create_plotwidget() # Helper to create plots
        self.day_plot.setMinimumHeight(280) # Ensure min height
        day_frame_layout.addWidget(day_title)
        day_frame_layout.addWidget(self.day_plot, 1) # Plot takes expanding space
        self._apply_shadow(day_frame) # Add shadow effect
        row1_layout.addWidget(day_frame, 1) # Equal width in this row

        # Visits by Month Chart
        month_frame = QFrame(objectName="ChartFrame")
        month_frame_layout = QVBoxLayout(month_frame)
        month_frame_layout.setContentsMargins(15, 15, 15, 15)
        month_title = QLabel("Visits by Month", objectName="SectionTitleLabel")
        self.month_plot = self._create_plotwidget()
        self.month_plot.setMinimumHeight(280)
        month_frame_layout.addWidget(month_title)
        month_frame_layout.addWidget(self.month_plot, 1)
        self._apply_shadow(month_frame)
        row1_layout.addWidget(month_frame, 1) # Equal width in this row

        content_layout.addLayout(row1_layout)


        # --- Row 2: Visit Trends Chart ---
        trends_frame = QFrame(objectName="ChartFrame")
        trends_layout = QVBoxLayout(trends_frame)
        trends_layout.setContentsMargins(15, 15, 15, 15)
        trends_layout.setSpacing(10)

        # Title and Filter Row for Trends
        trends_header_layout = QHBoxLayout()
        trends_title = QLabel("Visit Trends", objectName="SectionTitleLabel")
        trends_header_layout.addWidget(trends_title, 1) # Title takes space

        self.period_combo = QComboBox(objectName="periodCombo")
        self.period_combo.addItems(['Month', 'Week', 'Day']) # Default to Month
        self.period_combo.setCurrentText("Month")
        self.period_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        if MODEL_AVAILABLE:
             self.period_combo.currentTextChanged.connect(lambda text: self.load_visit_trends(text.lower()))
        else:
            self.period_combo.setEnabled(False)
        trends_header_layout.addWidget(self.period_combo, 0) # Combo aligns right
        trends_layout.addLayout(trends_header_layout)

        self.trends_plot = self._create_plotwidget()
        self.trends_plot.setMinimumHeight(300) # Slightly taller trend chart
        trends_layout.addWidget(self.trends_plot, 1) # Plot takes available space
        self._apply_shadow(trends_frame)

        content_layout.addWidget(trends_frame) # Add trend frame below row1

        main_layout.addLayout(content_layout, 1) # Content takes expanding space


    def _create_plotwidget(self):
        """Helper function to create and configure a PlotWidget."""
        plot = pg.PlotWidget(background=None) # Transparent background to see frame bg
        plot.getPlotItem().getViewBox().setBackgroundColor(COLOR_CHART_BG)
        plot.showGrid(x=True, y=True, alpha=0.15) # Subtle grid
        plot.getAxis('bottom').setPen(pg.mkPen(color=COLOR_BORDER, width=1))
        plot.getAxis('left').setPen(pg.mkPen(color=COLOR_BORDER, width=1))
        plot.getAxis('bottom').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))
        plot.getAxis('left').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED))
        plot.getPlotItem().getViewBox().setBorder(None) # Remove inner border
        plot.setAntialiasing(True)
        # Disable mouse interaction by default - enable if needed per plot
        plot.getPlotItem().getViewBox().setMouseEnabled(x=False, y=False)
        plot.getPlotItem().layout.setContentsMargins(5, 5, 10, 5) # T, R, B, L padding inside

        # --- Disable Scientific Notation ---
        plot.getAxis('left').enableAutoSIPrefix(False)
        plot.getAxis('bottom').enableAutoSIPrefix(False)
        # -----------------------------------
        return plot

    def _apply_shadow(self, widget):
        """Applies a standard shadow effect to a widget."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 40)) # Softer, larger shadow
        shadow.setOffset(0, 3)
        widget.setGraphicsEffect(shadow)

    def load_data(self):
        """Load data for all components."""
        if not MODEL_AVAILABLE:
            print("Analysis Model not available. Cannot load data.")
            # Optionally: Display a message overlay or disable UI elements further
            # Example: Show messages on plots
            self._show_no_data_message(self.day_plot, "Data Model Unavailable")
            self._show_no_data_message(self.month_plot, "Data Model Unavailable")
            self._show_no_data_message(self.trends_plot, "Data Model Unavailable")
            return

        print("Refreshing operational analysis data...")
        try:
            clinic_load_data = get_clinic_load_analysis()
            self.load_clinic_load_day(clinic_load_data.get('day_of_week', []))
            self.load_clinic_load_month(clinic_load_data.get('month', []))
        except Exception as e:
            print(f"ERROR loading clinic load data: {e}")
            self._show_no_data_message(self.day_plot, "Error Loading Data")
            self._show_no_data_message(self.month_plot, "Error Loading Data")

        try:
            # Load initial trend view (e.g., 'month')
            self.load_visit_trends(self.period_combo.currentText().lower())
        except Exception as e:
            print(f"ERROR loading initial visit trends: {e}")
            self._show_no_data_message(self.trends_plot, "Error Loading Data")
        print("Data refresh complete.")


    def _show_no_data_message(self, plot, message="No Data Available"):
        """Clears the plot and displays a centered message."""
        plot.clear()
        text = pg.TextItem(message, color=COLOR_TEXT_MUTED, anchor=(0.5, 0.5))
        # Position in the center (approximate)
        plot.addItem(text)
        # You might need to set plot limits manually if there's no data range
        plot.getViewBox().setLimits(xMin=0, xMax=1, yMin=0, yMax=1)
        text.setPos(0.5, 0.5)


    def load_clinic_load_day(self, data):
        plot = self.day_plot
        plot.clear() # Clear previous items

        if not data:
            self._show_no_data_message(plot, "No 'Day of Week' Data")
            return

        try:
            df = pd.DataFrame(data)
            if 'visit_count' not in df.columns or 'day_name' not in df.columns:
                 raise ValueError("Missing required columns in day data")
            df['visit_count'] = pd.to_numeric(df['visit_count'], errors='coerce').fillna(0)

            # Ensure consistent order (e.g., Mon-Sun) if possible, otherwise use data order
            # Example assuming 'day_name' provides the desired order/labels:
            day_names = df['day_name'].tolist()
            visit_counts = df['visit_count'].values
            x_indices = list(range(len(day_names)))

            if df.empty or visit_counts.sum() == 0:
                self._show_no_data_message(plot, "No 'Day of Week' Data")
                return

            bar_item = pg.BarGraphItem(x=x_indices, height=visit_counts, width=0.6,
                                       brush=pg.mkBrush(color=CHART_COLORS_OPERATIONAL[0]),
                                       pen=pg.mkPen(color=COLOR_PRIMARY, width=0)) # No border pen

            plot.addItem(bar_item)
            plot.getAxis('bottom').setTicks([list(zip(x_indices, day_names))])
            plot.getAxis('bottom').setStyle(tickTextOffset=5, tickFont=QFont(FONT_REGULAR, 8))
            plot.getAxis('left').setStyle(tickFont=QFont(FONT_REGULAR, 8))
            plot.getAxis('left').setWidth(45) # Adjust based on number scale
            plot.setLabel('left', 'Visit Count', units='', color=COLOR_TEXT_DARK, size='9pt')
            plot.setLabel('bottom', 'Day of Week', units='', color=COLOR_TEXT_DARK, size='9pt')

            # Adjust limits slightly for padding
            y_max = visit_counts.max()
            plot.getViewBox().setLimits(xMin=-0.5, xMax=len(x_indices)-0.5, yMin=0 - y_max*0.05, yMax=y_max*1.05)
            plot.getViewBox().autoRange(padding=0.02) # Apply padding

        except Exception as e:
            print(f"ERROR processing day data: {e}")
            self._show_no_data_message(plot, "Error Displaying Data")


    def load_clinic_load_month(self, data):
        plot = self.month_plot
        plot.clear()

        if not data:
             self._show_no_data_message(plot, "No 'Month' Data")
             return

        try:
            df = pd.DataFrame(data)
            if 'visit_count' not in df.columns or 'month_name' not in df.columns:
                 raise ValueError("Missing required columns in month data")
            df['visit_count'] = pd.to_numeric(df['visit_count'], errors='coerce').fillna(0)

            # Ensure consistent order (e.g., Jan-Dec) if possible
            # Example assuming 'month_name' provides desired order/labels:
            month_names = df['month_name'].tolist()
            visit_counts = df['visit_count'].values
            x_indices = list(range(len(month_names)))

            if df.empty or visit_counts.sum() == 0:
                self._show_no_data_message(plot, "No 'Month' Data")
                return

            bar_item = pg.BarGraphItem(x=x_indices, height=visit_counts, width=0.6,
                                       brush=pg.mkBrush(color=CHART_COLORS_OPERATIONAL[1]), # Use second color
                                       pen=pg.mkPen(color=COLOR_PRIMARY, width=0)) # No border pen

            plot.addItem(bar_item)
            plot.getAxis('bottom').setTicks([list(zip(x_indices, month_names))])
            plot.getAxis('bottom').setStyle(tickTextOffset=5, tickFont=QFont(FONT_REGULAR, 8))
            plot.getAxis('left').setStyle(tickFont=QFont(FONT_REGULAR, 8))
            plot.getAxis('left').setWidth(45)
            plot.setLabel('left', 'Visit Count', units='', color=COLOR_TEXT_DARK, size='9pt')
            plot.setLabel('bottom', 'Month', units='', color=COLOR_TEXT_DARK, size='9pt')

            y_max = visit_counts.max()
            plot.getViewBox().setLimits(xMin=-0.5, xMax=len(x_indices)-0.5, yMin=0 - y_max*0.05, yMax=y_max*1.05)
            plot.getViewBox().autoRange(padding=0.02)

        except Exception as e:
            print(f"ERROR processing month data: {e}")
            self._show_no_data_message(plot, "Error Displaying Data")


    def load_visit_trends(self, period):
        plot = self.trends_plot
        plot.clear()
        # Clear existing legend if any - addLegend creates a new one
        legend = plot.plotItem.legend
        if legend:
            legend.scene().removeItem(legend) # Remove old legend cleanly

        if not MODEL_AVAILABLE: # Check again in case model becomes unavailable later
             self._show_no_data_message(plot, "Data Model Unavailable")
             return

        try:
            data = get_visit_trends(period)
        except Exception as e:
            print(f"ERROR loading visit trends for period '{period}': {e}")
            self._show_no_data_message(plot, f"Error Loading '{period.capitalize()}' Data")
            return

        if not data:
            self._show_no_data_message(plot, f"No Visit Data for '{period.capitalize()}'")
            return

        try:
            df = pd.DataFrame(data)
            if 'visit_count' not in df.columns or 'time_period' not in df.columns:
                 raise ValueError("Missing required columns in trend data")
            df['visit_count'] = pd.to_numeric(df['visit_count'], errors='coerce').fillna(0)
            df['time_period'] = df['time_period'].astype(str) # Ensure string for ticks

            unique_periods = df['time_period'].unique()
            period_to_index = {p: i for i, p in enumerate(unique_periods)}
            df['x_index'] = df['time_period'].map(period_to_index)

            x = df['x_index'].values
            y = df['visit_count'].values

            if df.empty or y.sum() == 0:
                 self._show_no_data_message(plot, f"No Visit Data for '{period.capitalize()}'")
                 return

            # Styling - Thicker line, maybe gradient fill
            pen_visits = pg.mkPen(color=CHART_COLORS_OPERATIONAL[2], width=3) # Use third color
            gradient_visits = QLinearGradient(0,0,0,1); gradient_visits.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
            gradient_visits.setColorAt(0.0, QColor(CHART_COLORS_OPERATIONAL[2]+'50')); # Add transparency hex
            gradient_visits.setColorAt(1.0, QColor(CHART_COLORS_OPERATIONAL[2]+'05'));
            brush_visits = QBrush(gradient_visits)

            # Plot line and add fill
            visit_curve = plot.plot(x, y, pen=pen_visits, name='Visits')
            fill_item = pg.FillBetweenItem(visit_curve, pg.PlotDataItem(x, np.zeros_like(x)), brush=brush_visits)
            plot.addItem(fill_item)

            # Add markers if few data points for visibility
            if len(x) < 20:
                marker_size = 7
                marker_pen = pg.mkPen(color=COLOR_CHART_BG, width=1.5) # Outline matches bg
                marker_brush = pg.mkBrush(color=CHART_COLORS_OPERATIONAL[2])
                visit_curve.setSymbol('o')
                visit_curve.setSymbolSize(marker_size)
                visit_curve.setSymbolPen(marker_pen)
                visit_curve.setSymbolBrush(marker_brush)


            # Setup ticks - handle potential errors if period names are too long/complex
            try:
                 ticks = [[(i, p) for p, i in period_to_index.items()]]
                 plot.getAxis('bottom').setTicks(ticks)
                 # Rotate ticks if too many labels? Consider for 'day' view.
                 # if period == 'day' and len(ticks[0]) > 15:
                 #     plot.getAxis('bottom').setTextPen(pg.mkPen(color=COLOR_TEXT_MUTED)) # Ensure color set
                 #     plot.getAxis('bottom').setStyle(tickTextOrientation='vertical') # Or angle if preferred
                 # else:
                 #     plot.getAxis('bottom').setStyle(tickTextOrientation='horizontal')
            except Exception as e:
                 print(f"Tick setting error: {e}. Falling back to default ticks.")
                 plot.getAxis('bottom').setTicks(None) # Fallback


            plot.getAxis('bottom').setStyle(tickTextOffset=5, tickFont=QFont(FONT_REGULAR, 8))
            plot.getAxis('left').setStyle(tickFont=QFont(FONT_REGULAR, 8))
            plot.getAxis('left').setWidth(45)
            plot.setLabel('left', 'Visit Count', units='', color=COLOR_TEXT_DARK, size='9pt')
            plot.setLabel('bottom', 'Time Period', units='', color=COLOR_TEXT_DARK, size='9pt')

            # Add Legend
            legend = plot.addLegend(offset=(-15, 5), brush=pg.mkBrush(COLOR_CHART_BG+'E0'), pen=pg.mkPen(COLOR_BORDER, width=0.5), labelTextSize='8pt')
            legend.setLabelTextColor(COLOR_TEXT_DARK)


            # Adjust limits
            y_max = y.max() if len(y) > 0 else 1 # Avoid division by zero if y is empty
            plot.getViewBox().setLimits(xMin=-0.5, xMax=len(x)-0.5, yMin=0 - y_max*0.05, yMax=y_max*1.05)
            plot.getViewBox().autoRange(padding=0.02)

        except Exception as e:
            print(f"ERROR processing trend data for '{period}': {e}")
            self._show_no_data_message(plot, "Error Displaying Data")


    def wheelEvent(self, event):
        event.ignore() # Disable wheel scroll globally for the main widget


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Optional: Explicitly load font if needed and available
    # QFontDatabase.addApplicationFont("path/to/YourFont-Regular.ttf")
    # QFontDatabase.addApplicationFont("path/to/YourFont-Medium.ttf")
    # QFontDatabase.addApplicationFont("path/to/YourFont-Bold.ttf")

    window = OperationalAnalysis()
    window.showMaximized() # Show maximized for a better dashboard view
    # window.show() # Use this for non-maximized testing
    sys.exit(app.exec())