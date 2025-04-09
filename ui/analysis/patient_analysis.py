import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QScrollArea, QLabel,
    QFrame, QSizePolicy, QHeaderView, QApplication
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush, QPalette, QLinearGradient, QPainter
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import qtawesome as qta
from model.analysis_model import (  # Assuming these functions exist and return data
    get_patient_demographics,
    get_patient_visit_frequency,
    get_inactive_patients,
    get_single_visit_patients
)

# --- Enhanced Color Palette ---
COLOR_PRIMARY = "#2c3e50"  # Midnight Blue (Darker Primary)
COLOR_SECONDARY = "#ecf0f1"  # Clouds (Very Light Gray Background)
COLOR_ACCENT = "#3498db"  # Peter River (Bright Blue)
COLOR_SUCCESS = "#2ecc71"  # Emerald (Green)
COLOR_WARNING = "#f39c12"  # Orange
COLOR_DANGER = "#e74c3c"  # Alizarin (Red)
COLOR_INFO = "#9b59b6"  # Amethyst (Purple) - Added for variety
COLOR_TEXT_LIGHT = "#ffffff"  # White
COLOR_TEXT_DARK = "#34495e"  # Wet Asphalt (Dark Gray Text)
COLOR_TEXT_MUTED = "#7f8c8d" # Graydient (Muted Gray Text)
COLOR_BORDER = "#bdc3c7"  # Silver (Light Border)
COLOR_CHART_BG = "#ffffff"  # White (Chart Background)
COLOR_HOVER = "#34495e"  # Wet Asphalt (Darker Hover for Primary elements)
COLOR_TABLE_HEADER = "#34495e" # Wet Asphalt
COLOR_TABLE_ALT_ROW = "#f8f9f9" # Slightly off-white


# --- Modern Stylesheet ---
DASHBOARD_STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_TEXT_DARK};
    font-family: 'Segoe UI', 'Helvetica Neue', 'Arial', sans-serif; /* Modern font stack */
    font-size: 10pt;
}}

/* Main Window Background */
PatientAnalysis {{
    background-color: {COLOR_SECONDARY};
}}

/* Header */
QLabel#header {{
    font-size: 26pt; /* Slightly reduced for balance */
    font-weight: 600; /* Semibold */
    color: {COLOR_PRIMARY};
    padding-bottom: 5px; /* Add spacing below header */
}}

QLabel#subtitle {{
    font-size: 12pt; /* Reduced for subtlety */
    color: {COLOR_TEXT_MUTED};
    font-style: normal; /* Removed italic */
    padding-bottom: 15px; /* Add spacing below subtitle */
}}

/* Section Titles */
QLabel#sectionTitle {{
    font-size: 15pt; /* Adjusted size */
    font-weight: 600; /* Semibold */
    color: {COLOR_PRIMARY};
    margin-bottom: 10px; /* Reduced margin */
    padding-left: 5px;
    border-left: 3px solid {COLOR_ACCENT}; /* Accent line */
}}

/* Overview Metric Cards */
QFrame#metricCard {{
    background-color: {COLOR_CHART_BG};
    border-radius: 8px;
    border: 1px solid {COLOR_BORDER};
    padding: 15px;
    /* Subtle shadow effect (requires custom painting or platform specifics) */
    /* For simplicity, using border */
}}

QFrame#metricCard:hover {{
    border: 1px solid {COLOR_ACCENT}; /* Highlight on hover */
}}

QLabel#cardTitle {{
    font-size: 11pt; /* Adjusted size */
    font-weight: 500; /* Medium weight */
    color: {COLOR_TEXT_MUTED};
    margin-bottom: 5px;
}}

QLabel#cardValue {{
    font-size: 22pt; /* Adjusted size */
    font-weight: 600; /* Semibold */
    color: {COLOR_PRIMARY}; /* Default color, override per card */
}}

/* Chart and Table Containers */
QFrame#chartFrame, QFrame#visitorsChartFrame, QFrame#visitorsTableFrame {{
    background-color: {COLOR_CHART_BG};
    border-radius: 8px;
    border: 1px solid {COLOR_BORDER};
    padding: 5px; /* Reduced padding around canvas */
    margin-bottom: 15px; /* Increased spacing between elements */
}}

/* Table Styling */
QTableWidget {{
    background-color: {COLOR_CHART_BG};
    border: none; /* Remove QTableWidget's own border */
    gridline-color: {COLOR_BORDER};
    font-size: 10pt;
    border-radius: 6px; /* Apply radius to content area */
    selection-background-color: {COLOR_ACCENT};
    selection-color: {COLOR_TEXT_LIGHT};
    alternate-background-color: {COLOR_TABLE_ALT_ROW}; /* Subtle alternating row color */
}}

QTableWidget::item {{
    padding: 8px 10px; /* Increase cell padding */
    border-bottom: 1px solid {COLOR_BORDER}; /* Row separator */
}}

QTableWidget::item:selected {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT_LIGHT};
}}

QHeaderView::section {{
    background-color: {COLOR_TABLE_HEADER};
    color: {COLOR_TEXT_LIGHT};
    padding: 10px 8px; /* Increased padding */
    border: none;
    font-weight: 600; /* Semibold */
    font-size: 10pt;
    border-top-left-radius: 6px; /* Match table radius */
    border-top-right-radius: 6px;
}}

QHeaderView {{
    border: none; /* Remove header border */
    border-bottom: 1px solid {COLOR_BORDER}; /* Separator line */
}}


/* ScrollArea Styling */
QScrollArea {{
    border: none; /* Remove scroll area border */
}}

QScrollBar:vertical {{
    border: none;
    background: {COLOR_SECONDARY};
    width: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    border: none;
    background: {COLOR_SECONDARY};
    height: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:horizontal {{
    background: {COLOR_BORDER};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
    width: 0px;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}
"""

class PatientAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Patient Analytics Dashboard")
        self.setMinimumSize(1300, 850) # Slightly larger minimum size
        self.init_ui()
        # Use a QTimer to load data after the UI is shown, allowing animations to be smoother
        QTimer.singleShot(100, self.load_all_data_with_animation)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25) # Increased margins
        main_layout.setSpacing(20) # Increased spacing

        # --- Header ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(0)
        title_label = QLabel("Patient Analytics Dashboard", objectName="header")
        subtitle_label = QLabel("Monitor key patient statistics, demographics, and visit trends", objectName="subtitle")
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addLayout(header_layout)

        # --- Overview Cards ---
        overview_section_title = QLabel("Real-time Overview", objectName="sectionTitle")
        main_layout.addWidget(overview_section_title)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(20) # Increased spacing
        cards_layout.setVerticalSpacing(20)   # Increased spacing
        self.cards = {}
        metrics = [
            ("Total Patients", "fa5s.users", COLOR_INFO, self.get_total_patients), # Changed color
            ("Active Patients", "fa5s.user-check", COLOR_SUCCESS, self.get_active_patients),
            ("Single-Visit Patients", "fa5s.user-clock", COLOR_WARNING, self.get_single_visit_count),
            ("Inactive Patients", "fa5s.user-times", COLOR_DANGER, self.get_inactive_count),
        ]

        for i, (label_text, icon_name, color, data_func) in enumerate(metrics):
            card = QFrame(objectName="metricCard")
            card.setMinimumHeight(110) # Slightly taller cards
            card_v_layout = QVBoxLayout(card)
            card_v_layout.setContentsMargins(15, 15, 15, 15)
            card_v_layout.setSpacing(8) # Space between title row and value

            title_row_layout = QHBoxLayout()
            title_row_layout.setSpacing(10)
            icon_label = QLabel()
            icon_label.setPixmap(qta.icon(icon_name, color=color, color_disabled=COLOR_TEXT_MUTED).pixmap(28, 28)) # Larger icon
            title_row_layout.addWidget(icon_label)
            title_label = QLabel(label_text, objectName="cardTitle")
            title_row_layout.addWidget(title_label)
            title_row_layout.addStretch()
            card_v_layout.addLayout(title_row_layout)

            value_label = QLabel("...", objectName="cardValue") # Placeholder
            value_label.setStyleSheet(f"font-size: 24pt; font-weight: 600; color: {color};")
            card_v_layout.addWidget(value_label)
            card_v_layout.addStretch() # Push value down slightly if needed

            cards_layout.addWidget(card, 0, i)
            self.cards[label_text] = (value_label, data_func, card) # Store card for animation

        main_layout.addLayout(cards_layout)

        # --- Scroll Area for Charts and Table ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("mainScrollArea")
        scroll_area.setFrameShape(QFrame.Shape.NoFrame) # No border for the scroll area itself

        scroll_content_widget = QWidget()
        scroll_area.setWidget(scroll_content_widget)

        content_layout = QHBoxLayout(scroll_content_widget) # Main layout inside scroll area
        content_layout.setContentsMargins(0, 10, 0, 0) # Top margin
        content_layout.setSpacing(20) # Spacing between left and right columns

        # --- Left Column: Demographics ---
        left_column_layout = QVBoxLayout()
        left_column_layout.setSpacing(20)

        demographics_title = QLabel("Patient Demographics", objectName="sectionTitle")
        left_column_layout.addWidget(demographics_title)

        # Gender Chart Container
        gender_frame = QFrame(objectName="chartFrame")
        gender_frame.setMinimumHeight(320) # Adjusted minimum height
        gender_layout = QVBoxLayout(gender_frame)
        gender_layout.setContentsMargins(10, 10, 10, 10) # Padding inside the frame
        self.gender_canvas = FigureCanvas(plt.Figure(figsize=(5, 4), facecolor=COLOR_CHART_BG))
        # Use constrained_layout for better automatic spacing
        self.gender_canvas.figure.set_constrained_layout(True)
        self.gender_ax = self.gender_canvas.figure.add_subplot(111)
        gender_layout.addWidget(self.gender_canvas)
        left_column_layout.addWidget(gender_frame)
        self.gender_frame = gender_frame # Store for animation

        # Age Chart Container
        age_frame = QFrame(objectName="chartFrame")
        age_frame.setMinimumHeight(380) # Adjusted minimum height
        age_layout = QVBoxLayout(age_frame)
        age_layout.setContentsMargins(10, 10, 10, 10) # Padding inside the frame
        self.age_canvas = FigureCanvas(plt.Figure(figsize=(5, 4), facecolor=COLOR_CHART_BG))
        # Use constrained_layout for better automatic spacing
        self.age_canvas.figure.set_constrained_layout(True)
        self.age_ax = self.age_canvas.figure.add_subplot(111)
        age_layout.addWidget(self.age_canvas)
        left_column_layout.addWidget(age_frame)
        self.age_frame = age_frame # Store for animation

        left_column_layout.addStretch() # Push charts up if space allows

        # --- Right Column: Visit Frequency ---
        right_column_layout = QVBoxLayout()
        right_column_layout.setSpacing(20)

        visits_title = QLabel("Visit Frequency Analysis", objectName="sectionTitle")
        right_column_layout.addWidget(visits_title)

        # Visitors Bar Chart Container
        visitors_chart_frame = QFrame(objectName="visitorsChartFrame")
        visitors_chart_frame.setMinimumHeight(380) # Adjusted minimum height
        chart_layout = QVBoxLayout(visitors_chart_frame)
        chart_layout.setContentsMargins(10, 10, 10, 10) # Padding inside the frame
        self.visit_canvas = FigureCanvas(plt.Figure(figsize=(6, 4.5), facecolor=COLOR_CHART_BG))
        # Use constrained_layout for better automatic spacing
        self.visit_canvas.figure.set_constrained_layout(True)
        self.visit_ax = self.visit_canvas.figure.add_subplot(111)
        chart_layout.addWidget(self.visit_canvas)
        right_column_layout.addWidget(visitors_chart_frame)
        self.visitors_chart_frame = visitors_chart_frame # Store for animation


        # Visitors Table Container
        visitors_table_frame = QFrame(objectName="visitorsTableFrame")
        # Let table determine its height, set a reasonable minimum
        visitors_table_frame.setMinimumHeight(320)
        table_layout = QVBoxLayout(visitors_table_frame)
        table_layout.setContentsMargins(10, 10, 10, 10) # Padding inside the frame
        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(7)
        self.visit_table.setHorizontalHeaderLabels([
            'Patient ID', 'Name', 'Visits', 'First Visit',
            'Last Visit', 'Avg Days', 'Days Since Last'
        ])
        self.visit_table.verticalHeader().setVisible(False)
        self.visit_table.setAlternatingRowColors(True)
        self.visit_table.setShowGrid(False) # Cleaner look
        self.visit_table.setWordWrap(False)
        self.visit_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.visit_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.visit_table.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Prevent focus rectangle

        header = self.visit_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Stretch Name column
        for i in [0, 2, 3, 4, 5, 6]:
             header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents) # Resize others to content

        table_layout.addWidget(self.visit_table)
        right_column_layout.addWidget(visitors_table_frame)
        self.visitors_table_frame = visitors_table_frame # Store for animation

        right_column_layout.addStretch() # Push content up

        # Add columns to the main content layout
        content_layout.addLayout(left_column_layout, 1) # 1 stretch factor
        content_layout.addLayout(right_column_layout, 1) # 1 stretch factor

        main_layout.addWidget(scroll_area, 1) # Add scroll area, allow it to stretch


    def load_all_data_with_animation(self):
        """Loads data and triggers animations."""
        # Load data first
        try:
            self.update_overview_cards()
            self.load_demographics_charts()
            self.load_visit_frequency_data()
        except Exception as e:
            print(f"Error loading data: {e}")
            # Handle error display if needed

        # Animate widgets after data is ready
        self.animate_widgets()


    def update_overview_cards(self):
        """Fetches data and updates the overview card labels."""
        for label_text, (value_label, data_func, card) in self.cards.items():
            try:
                value = data_func()
                value_label.setText(f"{value:,}") # Format with comma for thousands
            except Exception as e:
                print(f"Error getting data for card '{label_text}': {e}")
                value_label.setText("Error")


    def load_demographics_charts(self):
        """Loads and plots patient demographics data."""
        try:
            data = get_patient_demographics()
            if not data:
                print("No demographic data found.")
                return

            # --- Gender Pie Chart ---
            gender_data = data.get('gender')
            if gender_data:
                gdf = pd.DataFrame(gender_data, columns=['gender', 'count'])
                self.gender_ax.clear()
                self.gender_ax.set_facecolor(COLOR_CHART_BG) # Ensure background color

                pie_colors = [COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_INFO] # More colors if needed
                wedges, texts, autotexts = self.gender_ax.pie(
                    gdf['count'],
                    # labels=gdf['gender'], # Labels inside or legend? Legend is better for space.
                    autopct='%1.1f%%',
                    colors=pie_colors[:len(gdf)],
                    startangle=90,
                    wedgeprops={'width': 0.4, 'edgecolor': 'w', 'linewidth': 1.5}, # Donut chart style
                    pctdistance=0.8 # Place percentage inside wedge
                )
                # Style autopct text
                for autotext in autotexts:
                    autotext.set_color(COLOR_TEXT_LIGHT)
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')

                self.gender_ax.set_title("Gender Distribution", fontsize=13, pad=15, color=COLOR_PRIMARY, weight='semibold')

                # Add legend outside the pie chart
                self.gender_ax.legend(wedges, gdf['gender'],
                                    title="Gender",
                                    loc="center left",
                                    bbox_to_anchor=(0.95, 0, 0.5, 1), # Adjust bbox to fit
                                    fontsize=10, frameon=False)

                self.gender_canvas.draw_idle() # Use draw_idle for efficiency
            else:
                 self.gender_ax.clear()
                 self.gender_ax.text(0.5, 0.5, 'No Gender Data', ha='center', va='center', fontsize=12, color=COLOR_TEXT_MUTED)
                 self.gender_canvas.draw_idle()


            # --- Age Bar Chart ---
            age_data = data.get('age')
            if age_data:
                adf = pd.DataFrame(age_data, columns=['age_group', 'count']).sort_values('age_group') # Ensure order
                self.age_ax.clear()
                self.age_ax.set_facecolor(COLOR_CHART_BG) # Ensure background color

                bars = self.age_ax.bar(adf['age_group'], adf['count'], color=COLOR_SUCCESS, # Changed color
                                       edgecolor=COLOR_TEXT_DARK, linewidth=0.5, width=0.6)
                self.age_ax.set_ylabel('Number of Patients', fontsize=11, color=COLOR_TEXT_DARK, labelpad=10)
                # No X label needed if groups are clear
                self.age_ax.tick_params(axis='x', rotation=30, labelsize=10, colors=COLOR_TEXT_DARK)
                self.age_ax.tick_params(axis='y', labelsize=10, colors=COLOR_TEXT_DARK)
                self.age_ax.set_title("Age Distribution", fontsize=13, pad=15, color=COLOR_PRIMARY, weight='semibold')

                # Remove top and right spines for cleaner look
                self.age_ax.spines['top'].set_visible(False)
                self.age_ax.spines['right'].set_visible(False)
                self.age_ax.spines['left'].set_color(COLOR_BORDER)
                self.age_ax.spines['bottom'].set_color(COLOR_BORDER)

                # Add data labels above bars
                for bar in bars:
                    height = bar.get_height()
                    if height > 0: # Only label bars with value
                        self.age_ax.annotate(f'{int(height)}',
                                             xy=(bar.get_x() + bar.get_width() / 2, height),
                                             xytext=(0, 3),  # 3 points vertical offset
                                             textcoords="offset points",
                                             ha='center', va='bottom', fontsize=9, color=COLOR_TEXT_DARK)

                # Adjust Y limit for padding above bars
                if not adf['count'].empty:
                    self.age_ax.set_ylim(0, adf['count'].max() * 1.15)

                self.age_canvas.draw_idle()
            else:
                 self.age_ax.clear()
                 self.age_ax.text(0.5, 0.5, 'No Age Data', ha='center', va='center', fontsize=12, color=COLOR_TEXT_MUTED)
                 self.age_canvas.draw_idle()

        except Exception as e:
            print(f"Error loading demographics charts: {e}")
            # Optionally display error on charts


    def load_visit_frequency_data(self):
        """Loads visit frequency data into the table and chart."""
        try:
            data = get_patient_visit_frequency()
            if not data:
                print("No visit frequency data found.")
                # Clear table and chart if needed
                self.visit_table.setRowCount(0)
                self.visit_ax.clear()
                self.visit_ax.text(0.5, 0.5, 'No Visit Data', ha='center', va='center', fontsize=12, color=COLOR_TEXT_MUTED)
                self.visit_canvas.draw_idle()
                return

            # Consider sorting and limiting data if it's very large
            top_visitors = sorted(data, key=lambda x: x['visit_count'], reverse=True) # Keep all or slice [:N]

            # --- Populate Table ---
            self.visit_table.setRowCount(len(top_visitors))
            for row, patient in enumerate(top_visitors):
                self.set_table_item(row, 0, str(patient.get('patient_id', 'N/A')))
                self.set_table_item(row, 1, patient.get('name', 'N/A'), bold=True)

                visit_count = patient.get('visit_count', 0)
                vc_item = self.set_table_item(row, 2, str(visit_count))
                if visit_count > 10: vc_item.setForeground(QColor(COLOR_SUCCESS))
                elif visit_count > 5: vc_item.setForeground(QColor(COLOR_ACCENT))

                self.set_table_item(row, 3, patient.get('first_visit', 'N/A'))
                self.set_table_item(row, 4, patient.get('last_visit', 'N/A'))

                avg_days = patient.get('avg_days_between_visits')
                self.set_table_item(row, 5, f"{avg_days:.1f}" if avg_days is not None else "N/A")

                dslv = patient.get('days_since_last_visit')
                dslv_item = self.set_table_item(row, 6, str(dslv) if dslv is not None else "N/A")
                if dslv is not None:
                    if dslv > 90: dslv_item.setForeground(QColor(COLOR_DANGER))
                    elif dslv > 60: dslv_item.setForeground(QColor(COLOR_WARNING))

            # Adjust column widths after populating
            self.visit_table.resizeColumnsToContents()
            # Ensure Name column still stretches
            self.visit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)


            # --- Populate Horizontal Bar Chart (Top N Visitors) ---
            top_n_for_chart = 10
            chart_data = top_visitors[:top_n_for_chart]
            if chart_data:
                df = pd.DataFrame(chart_data)
                ax = self.visit_ax
                ax.clear()
                ax.set_facecolor(COLOR_CHART_BG)

                y_pos = np.arange(len(df))
                counts = df['visit_count']
                max_count = counts.max() if not counts.empty else 1 # Avoid division by zero

                bars = ax.barh(y_pos, counts, align='center', height=0.6,
                               color=COLOR_ACCENT, edgecolor=COLOR_TEXT_DARK, linewidth=0.5)

                ax.set_yticks(y_pos)
                ax.set_yticklabels(df['name'], fontsize=10, color=COLOR_TEXT_DARK)
                ax.invert_yaxis()  # labels read top-to-bottom

                ax.set_xlabel('Number of Visits', fontsize=11, color=COLOR_TEXT_DARK, labelpad=10)
                ax.tick_params(axis='x', labelsize=10, colors=COLOR_TEXT_DARK)
                ax.tick_params(axis='y', length=0) # Hide y-axis ticks

                ax.set_title(f"Top {top_n_for_chart} Most Frequent Visitors", fontsize=13, pad=15, color=COLOR_PRIMARY, weight='semibold')

                # Remove spines for cleaner look
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_visible(False) # Remove Y axis line too
                ax.spines['bottom'].set_color(COLOR_BORDER)

                # Add data labels to the right of bars
                for i, count in enumerate(counts):
                     if count > 0:
                         ax.text(count + (max_count * 0.02), i, f' {count}', # Add slight offset
                                 va='center', ha='left', fontsize=9, color=COLOR_TEXT_DARK)

                # Adjust X limit for labels
                if max_count > 0:
                    ax.set_xlim(0, max_count * 1.15) # Add 15% padding

                self.visit_canvas.draw_idle()
            else:
                self.visit_ax.clear()
                self.visit_ax.text(0.5, 0.5, 'Not Enough Data for Chart', ha='center', va='center', fontsize=12, color=COLOR_TEXT_MUTED)
                self.visit_canvas.draw_idle()


        except Exception as e:
            print(f"Error loading visit frequency data: {e}")
            # Optionally display error message

    def set_table_item(self, row, col, text, bold=False):
        """Helper to create and set a QTableWidgetItem."""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable) # Make read-only
        if bold:
            font = item.font()
            font.setWeight(QFont.Weight.Bold)
            item.setFont(font)
        self.visit_table.setItem(row, col, item)
        return item # Return item for further styling if needed

    def animate_widgets(self):
        """Applies a subtle fade-in/grow animation to key elements."""
        widgets_to_animate = [self.cards[key][2] for key in self.cards] # Get card frames
        widgets_to_animate.extend([
            self.gender_frame, self.age_frame,
            self.visitors_chart_frame, self.visitors_table_frame
        ])

        for i, widget in enumerate(widgets_to_animate):
            if not isinstance(widget, QFrame): continue

            # Option 1: Fade-in (Requires more complex handling of opacity or graphics effects)
            # Option 2: Subtle Grow/Slide-in (Using geometry or size)

            # Simple grow animation using minimumHeight (like original but refined)
            start_height = max(10, widget.minimumHeight() - 40) # Start smaller
            end_height = widget.minimumHeight()

            if end_height <= start_height: continue # Skip if no effective change

            anim = QPropertyAnimation(widget, b"minimumHeight")
            anim.setDuration(500 + i * 50) # Stagger animations slightly
            anim.setStartValue(start_height)
            anim.setEndValue(end_height)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic) # Smoother curve
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


    # --- Metric Data Fetching Helper Methods ---
    # (These assume your model functions exist and return appropriate types)
    def get_total_patients(self):
        try:
            data = get_patient_demographics()
            return sum(item['count'] for item in data.get('gender', [])) if data else 0
        except Exception:
            return 0 # Default value on error

    def get_active_patients(self):
        # Example: Active = Total - Inactive (adjust logic as needed)
        try:
            total = self.get_total_patients()
            inactive = self.get_inactive_count()
            return total - inactive
        except Exception:
            return 0

    def get_inactive_count(self):
        try:
            # Assuming get_inactive_patients returns a list or similar iterable
            return len(get_inactive_patients())
        except Exception:
            return 0

    def get_single_visit_count(self):
        try:
             # Assuming get_single_visit_patients returns a list or similar iterable
            return len(get_single_visit_patients())
        except Exception:
            return 0


# --- Main Execution ---
if __name__ == '__main__':
    # Mock data functions if 'model.analysis_model' doesn't exist
    # This is crucial for running the example standalone
    try:
        # Check if functions exist, if not, define mocks
        get_patient_demographics
        get_patient_visit_frequency
        get_inactive_patients
        get_single_visit_patients
    except NameError:
        print("Mocking analysis functions...")
        def get_patient_demographics():
            return {
                'gender': [
                    {'gender': 'Male', 'count': 120},
                    {'gender': 'Female', 'count': 180},
                    {'gender': 'Other', 'count': 5}
                ],
                'age': [
                    {'age_group': '0-18', 'count': 30},
                    {'age_group': '19-35', 'count': 90},
                    {'age_group': '36-50', 'count': 110},
                    {'age_group': '51-65', 'count': 55},
                    {'age_group': '65+', 'count': 20}
                ]
            }
        def get_patient_visit_frequency():
            # Return more data points for table scroll testing if needed
            base_data = [
                {'patient_id': 101, 'name': 'Alice Johnson', 'visit_count': 15, 'first_visit': '2023-01-10', 'last_visit': '2024-03-01', 'avg_days_between_visits': 25.5, 'days_since_last_visit': 40},
                {'patient_id': 102, 'name': 'Bob Williams', 'visit_count': 12, 'first_visit': '2022-11-05', 'last_visit': '2024-02-15', 'avg_days_between_visits': 40.2, 'days_since_last_visit': 55},
                {'patient_id': 103, 'name': 'Charlie Brown', 'visit_count': 8, 'first_visit': '2023-05-20', 'last_visit': '2024-01-10', 'avg_days_between_visits': 30.0, 'days_since_last_visit': 90},
                {'patient_id': 104, 'name': 'Diana Miller', 'visit_count': 22, 'first_visit': '2023-02-01', 'last_visit': '2024-04-01', 'avg_days_between_visits': 18.1, 'days_since_last_visit': 8},
                {'patient_id': 105, 'name': 'Ethan Davis', 'visit_count': 5, 'first_visit': '2023-08-11', 'last_visit': '2023-12-20', 'avg_days_between_visits': 25.8, 'days_since_last_visit': 111},
                {'patient_id': 106, 'name': 'Fiona Garcia', 'visit_count': 9, 'first_visit': '2023-03-15', 'last_visit': '2024-03-10', 'avg_days_between_visits': 35.0, 'days_since_last_visit': 31},
                {'patient_id': 107, 'name': 'George Rodriguez', 'visit_count': 3, 'first_visit': '2024-01-05', 'last_visit': '2024-03-05', 'avg_days_between_visits': 30.0, 'days_since_last_visit': 36},
                {'patient_id': 108, 'name': 'Hannah Smith', 'visit_count': 18, 'first_visit': '2022-09-01', 'last_visit': '2024-03-20', 'avg_days_between_visits': 28.5, 'days_since_last_visit': 21},
                {'patient_id': 109, 'name': 'Ian Martinez', 'visit_count': 1, 'first_visit': '2024-02-28', 'last_visit': '2024-02-28', 'avg_days_between_visits': None, 'days_since_last_visit': 42},
                {'patient_id': 110, 'name': 'Jane Doe', 'visit_count': 7, 'first_visit': '2023-06-01', 'last_visit': '2024-01-30', 'avg_days_between_visits': 42.0, 'days_since_last_visit': 70},
                 {'patient_id': 111, 'name': 'Kyle Wilson', 'visit_count': 11, 'first_visit': '2023-01-15', 'last_visit': '2024-02-25', 'avg_days_between_visits': 33.3, 'days_since_last_visit': 45},
                 {'patient_id': 112, 'name': 'Laura Taylor', 'visit_count': 6, 'first_visit': '2023-07-01', 'last_visit': '2024-03-12', 'avg_days_between_visits': 48.0, 'days_since_last_visit': 29},
            ]
            # Simulate some N/A values
            base_data[2]['avg_days_between_visits'] = None
            base_data[6]['last_visit'] = 'N/A'
            base_data[6]['days_since_last_visit'] = None
            return base_data

        def get_inactive_patients():
            # Patients whose days_since_last_visit > 90 (example definition)
            freq_data = get_patient_visit_frequency()
            return [p for p in freq_data if p.get('days_since_last_visit', 0) is not None and p['days_since_last_visit'] > 90]

        def get_single_visit_patients():
             # Patients whose visit_count == 1
            freq_data = get_patient_visit_frequency()
            return [p for p in freq_data if p.get('visit_count', 0) == 1]

        # Make mock functions available globally if needed within the class scope
        # (Better practice is dependency injection, but this works for the example)
        model = sys.modules[__name__]
        model.get_patient_demographics = get_patient_demographics
        model.get_patient_visit_frequency = get_patient_visit_frequency
        model.get_inactive_patients = get_inactive_patients
        model.get_single_visit_patients = get_single_visit_patients


    app = QApplication(sys.argv)
    # Set global font smoothing/antialiasing if desired
    # font = QFont("Segoe UI", 10)
    # app.setFont(font)

    window = PatientAnalysis()
    window.show()
    sys.exit(app.exec())