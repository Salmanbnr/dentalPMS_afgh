from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QScrollArea, QLabel,
    QPushButton, QFrame, QSizePolicy, QHeaderView
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont, QBrush, QPalette
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Circle
from model.analysis_model import (
    get_patient_demographics,
    get_patient_visit_frequency,
    get_inactive_patients,
    get_single_visit_patients
)
import pandas as pd
import qtawesome as qta

# — Enhanced Color Palette —
COLOR_PRIMARY    = "#1e3d59"    # Deep Blue
COLOR_SECONDARY  = "#f8f9fa"    # Light Grayish White
COLOR_ACCENT     = "#3498db"    # Bright Blue
COLOR_SUCCESS    = "#27ae60"    # Green
COLOR_WARNING    = "#f39c12"    # Orange
COLOR_DANGER     = "#e74c3c"    # Red
COLOR_TEXT_LIGHT = "#ffffff"    # White
COLOR_TEXT_DARK  = "#2c3e50"    # Dark Gray
COLOR_BORDER     = "#e0e0e0"    # Light Gray
COLOR_CHART_BG   = "#ffffff"    # White
COLOR_HOVER      = "#4a6fa5"    # Darker Blue
COLOR_SHADOW     = "rgba(0, 0, 0, 0.1)"  # Subtle Shadow

# — Enhanced Stylesheet —
DASHBOARD_STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_TEXT_DARK};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    border-radius: 8px;
}}
QLabel#header {{
    font-size: 28pt;
    font-weight: bold;
    color: {COLOR_PRIMARY};
    text-shadow: 1px 1px 2px {COLOR_SHADOW};
}}
QLabel#subtitle {{
    font-size: 14pt;
    color: {COLOR_TEXT_DARK};
    font-style: italic;
}}
QPushButton#refreshBtn {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLOR_ACCENT}, stop:1 {COLOR_HOVER});
    color: {COLOR_TEXT_LIGHT};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
    box-shadow: 0 2px 4px {COLOR_SHADOW};
}}
QPushButton#refreshBtn:hover {{
    background-color: {COLOR_HOVER};
    box-shadow: 0 4px 8px {COLOR_SHADOW};
}}
QLabel#sectionTitle {{
    font-size: 16pt;
    font-weight: bold;
    color: {COLOR_PRIMARY};
    margin-bottom: 12px;
    text-shadow: 1px 1px 1px {COLOR_SHADOW};
}}
QLabel#cardTitle {{
    font-size: 12pt;
    color: {COLOR_TEXT_DARK};
    margin-bottom: 6px;
}}
QFrame#metricCard {{
    background-color: {COLOR_CHART_BG};
    border-radius: 10px;
    border: 1px solid {COLOR_BORDER};
    box-shadow: 0 4px 6px {COLOR_SHADOW};
    padding: 15px;
}}
QFrame#chartFrame, QFrame#visitorsChartFrame, QFrame#visitorsTableFrame {{
    background-color: {COLOR_CHART_BG};
    border-radius: 10px;
    border: 1px solid {COLOR_BORDER};
    box-shadow: 0 4px 6px {COLOR_SHADOW};
    padding: 15px;
    margin-bottom: 15px;
}}
QTableWidget {{
    background-color: white;
    border: 1px solid {COLOR_BORDER};
    gridline-color: {COLOR_BORDER};
    font-size: 10pt;
    border-radius: 8px;
    box-shadow: 0 2px 4px {COLOR_SHADOW};
}}
QHeaderView::section {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLOR_PRIMARY}, stop:1 {COLOR_HOVER});
    color: {COLOR_TEXT_LIGHT};
    padding: 6px;
    border: none;
    font-weight: bold;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}
"""

class PatientAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Patient Analytics Dashboard")
        self.setMinimumSize(1200, 800)  # Reduced size to avoid horizontal scrollbar
        self.init_ui()

    def init_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(15)

        # Header with animation
        hdr = QHBoxLayout()
        hdr.setSpacing(15)
        title_box = QVBoxLayout()
        title_label = QLabel("Patient Analytics Dashboard", objectName="header")
        subtitle_label = QLabel("Monitor patient statistics and trends", objectName="subtitle")
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        hdr.addLayout(title_box)
        hdr.addStretch()
        btn = QPushButton(qta.icon('fa5s.sync', color=COLOR_TEXT_LIGHT), " Refresh", objectName="refreshBtn")
        btn.setIconSize(QSize(16, 16))
        btn.clicked.connect(self.refresh_data)
        self.animate_button(btn)
        hdr.addWidget(btn)
        main.addLayout(hdr)

        # Overview cards with improved layout
        main.addWidget(QLabel("Overview", objectName="sectionTitle"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(10)
        self.cards = {}
        metrics = [
            ("Total Patients", "fa5s.users", COLOR_ACCENT, self.get_total_patients),
            ("Active Patients", "fa5s.user-check", COLOR_SUCCESS, self.get_active_patients),
            ("Single-Visit Patients", "fa5s.user-clock", COLOR_WARNING, self.get_single_visit_count),
            ("Inactive Patients", "fa5s.user-times", COLOR_DANGER, self.get_inactive_count),
        ]
        for i, (lbl, icon, col, fn) in enumerate(metrics):
            card = QFrame(objectName="metricCard")
            card.setFixedHeight(100)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 8, 12, 8)
            row = QHBoxLayout()
            ico = QLabel()
            ico.setPixmap(qta.icon(icon, color=col).pixmap(24, 24))
            row.addWidget(ico)
            row.addWidget(QLabel(lbl, objectName="cardTitle"))
            row.addStretch()
            cl.addLayout(row)
            val = QLabel("0", objectName="cardValue")
            val.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {col};")
            cl.addWidget(val)
            cl.addStretch()
            grid.addWidget(card, 0, i)
            self.cards[lbl] = (val, fn)
        main.addLayout(grid)

        # Scroll area with no individual scrollbars
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        hl = QHBoxLayout(container)
        hl.setSpacing(15)

        # Left column - Independent Demographics Charts
        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(QLabel("Patient Demographics", objectName="sectionTitle"))

        # Gender Chart (Smaller, Independent)
        gender_frame = QFrame(objectName="chartFrame")
        gender_frame.setMinimumHeight(300)  # Reduced height
        gender_layout = QVBoxLayout(gender_frame)
        gender_layout.setContentsMargins(0, 0, 0, 0)
        self.gender_canvas = FigureCanvas(plt.Figure(figsize=(4, 3)))  # Smaller figure
        self.gender_ax = self.gender_canvas.figure.add_subplot(111)
        self.gender_canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.gender_canvas.wheelEvent = lambda e: None
        gender_layout.addWidget(self.gender_canvas)
        left.addWidget(gender_frame)

        # Age Chart (Smaller, Independent)
        age_frame = QFrame(objectName="chartFrame")
        age_frame.setMinimumHeight(300)  # Reduced height
        age_layout = QVBoxLayout(age_frame)
        age_layout.setContentsMargins(0, 0, 0, 0)
        self.age_canvas = FigureCanvas(plt.Figure(figsize=(4, 3)))  # Smaller figure
        self.age_ax = self.age_canvas.figure.add_subplot(111)
        self.age_canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.age_canvas.wheelEvent = lambda e: None
        age_layout.addWidget(self.age_canvas)
        left.addWidget(age_frame)

        hl.addLayout(left, 1)

        # Right column - Independent Visit Frequency
        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(QLabel("Visit Frequency", objectName="sectionTitle"))

        # Visitors Chart (Smaller, Independent)
        visitors_chart_frame = QFrame(objectName="visitorsChartFrame")
        visitors_chart_frame.setMinimumHeight(350)  # Reduced height
        chart_layout = QVBoxLayout(visitors_chart_frame)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        self.visit_canvas = FigureCanvas(plt.Figure(figsize=(5, 3)))  # Smaller figure
        self.visit_ax = self.visit_canvas.figure.add_subplot(111)
        self.visit_canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.visit_canvas.wheelEvent = lambda e: None
        chart_layout.addWidget(self.visit_canvas)
        right.addWidget(visitors_chart_frame)

        # Visitors Table (Smaller, Independent)
        visitors_table_frame = QFrame(objectName="visitorsTableFrame")
        visitors_table_frame.setMinimumHeight(300)  # Reduced height
        table_layout = QVBoxLayout(visitors_table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.visit_table = QTableWidget()
        self.visit_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.visit_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.visit_table.setColumnCount(7)
        self.visit_table.setHorizontalHeaderLabels([
            'Patient ID', 'Name', 'Visit Count', 'First Visit',
            'Last Visit', 'Avg Days', 'Days Since Last'
        ])
        self.visit_table.verticalHeader().setVisible(False)
        self.visit_table.setAlternatingRowColors(True)
        hdr = self.visit_table.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.visit_table)
        right.addWidget(visitors_table_frame)

        hl.addLayout(right, 1)
        main.addWidget(scroll)

        # Initial load with animations
        self.refresh_data()
        self.animate_widgets()

    def animate_button(self, button):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(200)
        anim.setStartValue(button.geometry())
        anim.setEndValue(button.geometry().adjusted(0, 0, 5, 5))
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        button.enterEvent = lambda event: anim.start()
        button.leaveEvent = lambda event: anim.setEndValue(button.geometry().adjusted(0, 0, -5, -5)) or anim.start()

    def animate_widgets(self):
        for widget in self.findChildren(QFrame):
            anim = QPropertyAnimation(widget, b"minimumHeight")
            anim.setDuration(500)
            anim.setStartValue(widget.minimumHeight() - 50)
            anim.setEndValue(widget.minimumHeight())
            anim.setEasingCurve(QEasingCurve.Type.OutBack)
            anim.start()

    def refresh_data(self):
        for lbl, fn in self.cards.values():
            lbl.setText(str(fn()))
        self.load_demographics()
        self.load_visit_frequency()

    # Metric helpers (unchanged)
    def get_total_patients(self):
        data = get_patient_demographics()
        return sum(x['count'] for x in data['gender'])

    def get_active_patients(self):
        return self.get_total_patients() - self.get_inactive_count()

    def get_inactive_count(self):
        return len(get_inactive_patients())

    def get_single_visit_count(self):
        return len(get_single_visit_patients())

    def load_demographics(self):
        data = get_patient_demographics()
        # Gender Pie (Smaller, with Legend)
        gdf = pd.DataFrame(data['gender'], columns=['gender', 'count'])
        self.gender_ax.clear()
        wedges, texts, autos = self.gender_ax.pie(
            gdf['count'],
            labels=None,  # Removed labels from pie for legend
            autopct='%1.0f%%',  # Simplified percentage
            colors=[COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER][:len(gdf)],
            startangle=90,
            wedgeprops={'width': 0.3, 'edgecolor': 'w', 'linewidth': 1}
        )
        self.gender_ax.legend(wedges, gdf['gender'], title="Gender", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10, frameon=False)
        for t in texts + autos:
            t.set_fontsize(8)
            t.set_color(COLOR_TEXT_DARK)
        self.gender_ax.set_title("Gender Distribution", fontsize=12, pad=10, color=COLOR_PRIMARY)
        self.gender_canvas.draw()

        # Age Bar (Smaller, with Space)
        adf = pd.DataFrame(data['age'], columns=['age_group', 'count'])
        self.age_ax.clear()
        bars = self.age_ax.bar(adf['age_group'], adf['count'], color=COLOR_ACCENT, edgecolor='black', linewidth=0.5, width=0.6)
        self.age_ax.set_xlabel('Age Group', fontsize=8, color=COLOR_TEXT_DARK)
        self.age_ax.set_ylabel('Count', fontsize=8, color=COLOR_TEXT_DARK)
        self.age_ax.tick_params(axis='x', rotation=45, labelsize=8, colors=COLOR_TEXT_DARK)
        self.age_ax.tick_params(axis='y', labelsize=8, colors=COLOR_TEXT_DARK)
        self.age_ax.set_title("Age Distribution", fontsize=12, pad=10, color=COLOR_PRIMARY)
        for bar in bars:
            h = bar.get_height()
            self.age_ax.annotate(f"{int(h)}",
                                 xy=(bar.get_x() + bar.get_width() / 2, h),
                                 xytext=(0, 3), textcoords='offset points',
                                 ha='center', va='bottom', fontsize=8, color=COLOR_TEXT_DARK)
        self.age_ax.set_ylim(0, max(adf['count']) * 1.2)  # Add space at top
        self.age_canvas.draw()

    def load_visit_frequency(self):
        data = get_patient_visit_frequency()
        top10 = sorted(data, key=lambda x: x['visit_count'], reverse=True)[:10]

        # Table
        self.visit_table.clearContents()
        self.visit_table.setRowCount(len(top10))
        for r, p in enumerate(top10):
            self.visit_table.setItem(r, 0, QTableWidgetItem(str(p['patient_id'])))
            nm = QTableWidgetItem(p['name'])
            nm.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.visit_table.setItem(r, 1, nm)
            vc = p['visit_count']
            vc_item = QTableWidgetItem(str(vc))
            if vc > 10:
                vc_item.setForeground(QColor(COLOR_SUCCESS))
                vc_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif vc > 5:
                vc_item.setForeground(QColor(COLOR_ACCENT))
            self.visit_table.setItem(r, 2, vc_item)
            self.visit_table.setItem(r, 3, QTableWidgetItem(p.get('first_visit', 'N/A')))
            self.visit_table.setItem(r, 4, QTableWidgetItem(p.get('last_visit', 'N/A')))
            avg = p.get('avg_days_between_visits')
            self.visit_table.setItem(r, 5, QTableWidgetItem(f"{avg:.1f}" if avg else "N/A"))
            dsl = p.get('days_since_last_visit')
            d_item = QTableWidgetItem(str(dsl) if dsl is not None else "N/A")
            if dsl is not None:
                if dsl > 90:
                    d_item.setForeground(QColor(COLOR_DANGER))
                elif dsl > 60:
                    d_item.setForeground(QColor(COLOR_WARNING))
                elif dsl < 30:
                    d_item.setForeground(QColor(COLOR_SUCCESS))
            self.visit_table.setItem(r, 6, d_item)
        self.visit_table.resizeColumnsToContents()

        # Horizontal Bar Chart (Smaller, with Space)
        df = pd.DataFrame(top10)
        ax = self.visit_ax
        ax.clear()
        y_pos = np.arange(len(df))
        bar_h = 0.4
        max_val = df['visit_count'].max()
        for y, val in zip(y_pos, df['visit_count']):
            rect = Rectangle((0, y - bar_h / 2), val, bar_h,
                             color=COLOR_ACCENT, edgecolor='black', linewidth=0.5)
            ax.add_patch(rect)
            ax.text(val * 1.05, y, f"{val}", va='center', ha='left', fontsize=8, color=COLOR_TEXT_DARK)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['name'], fontsize=8, color=COLOR_TEXT_DARK)
        ax.set_ylim(-0.5, len(df) - 0.5)
        ax.invert_yaxis()
        ax.set_xlim(0, max_val * 1.3)  # Add more space on the right
        ax.set_xlabel('Visit Count', fontsize=8, color=COLOR_TEXT_DARK)
        ax.tick_params(axis='x', labelsize=8, colors=COLOR_TEXT_DARK)
        ax.set_title("Top 10 Most Frequent Visitors", fontsize=12, pad=10, color=COLOR_PRIMARY)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        self.visit_canvas.draw()