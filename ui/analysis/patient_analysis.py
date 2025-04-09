from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QScrollArea, QLabel,
    QPushButton, QFrame, QSizePolicy, QHeaderView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
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

# — Color palette —
COLOR_PRIMARY    = "#1e3d59"
COLOR_SECONDARY  = "#f5f5f5"
COLOR_ACCENT     = "#3498db"
COLOR_SUCCESS    = "#27ae60"
COLOR_WARNING    = "#f39c12"
COLOR_DANGER     = "#e74c3c"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK  = "#2c3e50"
COLOR_BORDER     = "#e0e0e0"
COLOR_CHART_BG   = "#ffffff"
COLOR_HOVER      = "#4a6fa5"

# — Stylesheet —
DASHBOARD_STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_TEXT_DARK};
    font-family: 'Segoe UI', 'Arial', sans-serif;
}}
QLabel#header {{
    font-size: 24pt;
    font-weight: bold;
    color: {COLOR_PRIMARY};
}}
QLabel#subtitle {{
    font-size: 12pt;
    color: {COLOR_TEXT_DARK};
}}
QPushButton#refreshBtn {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT_LIGHT};
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}}
QPushButton#refreshBtn:hover {{
    background-color: {COLOR_HOVER};
}}
QLabel#sectionTitle {{
    font-size: 14pt;
    font-weight: bold;
    color: {COLOR_PRIMARY};
    margin-bottom: 8px;
}}
QLabel#cardTitle {{
    font-size: 10pt;
    color: {COLOR_TEXT_DARK};
    margin-bottom: 4px;
}}
QFrame#metricCard {{
    background-color: {COLOR_CHART_BG};
    border-radius: 6px;
    border: 1px solid {COLOR_BORDER};
}}
QLabel#cardValue {{
    font-size: 20pt;
    font-weight: bold;
    color: {COLOR_PRIMARY};
}}
QFrame#chartFrame, QFrame#visitorsChartFrame, QFrame#visitorsTableFrame {{
    background-color: {COLOR_CHART_BG};
    border-radius: 6px;
    border: 1px solid {COLOR_BORDER};
    padding: 10px;
}}
QTableWidget {{
    background-color: white;
    border: 1px solid {COLOR_BORDER};
    gridline-color: {COLOR_BORDER};
    font-size: 9pt;
}}
QHeaderView::section {{
    background-color: {COLOR_PRIMARY};
    color: {COLOR_TEXT_LIGHT};
    padding: 4px;
    border: none;
    font-weight: bold;
}}
"""

class PatientAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Patient Analytics Dashboard")
        self.setMinimumSize(1200, 800)
        self.init_ui()

    def init_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(20,20,20,20)
        main.setSpacing(15)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.addWidget(QLabel("Patient Analytics Dashboard", objectName="header"))
        title_box.addWidget(QLabel("Monitor patient statistics and trends", objectName="subtitle"))
        hdr.addLayout(title_box)
        hdr.addStretch()
        btn = QPushButton(qta.icon('fa5s.sync', color=COLOR_TEXT_LIGHT), " Refresh", objectName="refreshBtn")
        btn.setIconSize(QSize(14,14))
        btn.clicked.connect(self.refresh_data)
        hdr.addWidget(btn)
        main.addLayout(hdr)

        # Overview cards
        main.addWidget(QLabel("Overview", objectName="sectionTitle"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(10)
        self.cards = {}
        metrics = [
            ("Total Patients",        "fa5s.users",      COLOR_ACCENT, self.get_total_patients),
            ("Active Patients",       "fa5s.user-check", COLOR_SUCCESS, self.get_active_patients),
            ("Single-Visit Patients", "fa5s.user-clock", COLOR_WARNING, self.get_single_visit_count),
            ("Inactive Patients",     "fa5s.user-times", COLOR_DANGER,  self.get_inactive_count),
        ]
        for i, (lbl, icon, col, fn) in enumerate(metrics):
            card = QFrame(objectName="metricCard")
            card.setFixedHeight(100)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12,8,12,8)
            row = QHBoxLayout()
            ico = QLabel()
            ico.setPixmap(qta.icon(icon, color=col).pixmap(24,24))
            row.addWidget(ico)
            row.addWidget(QLabel(lbl, objectName="cardTitle"))
            row.addStretch()
            cl.addLayout(row)
            val = QLabel("0", objectName="cardValue")
            cl.addWidget(val)
            cl.addStretch()
            grid.addWidget(card, 0, i)
            self.cards[lbl] = (val, fn)
        main.addLayout(grid)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        hl = QHBoxLayout(container)
        hl.setSpacing(15)

        # Left column
        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(QLabel("Patient Demographics", objectName="sectionTitle"))

        # Gender frame (larger pie)
        left.addWidget(QLabel("Gender Distribution", objectName="cardTitle"))
        gf = QFrame(objectName="chartFrame")
        gf.setMinimumHeight(300)
        gl = QVBoxLayout(gf)
        gl.setContentsMargins(0,0,0,0)
        self.gender_canvas = FigureCanvas(plt.Figure(figsize=(6,4)))
        self.gender_ax     = self.gender_canvas.figure.add_subplot(111)
        self.gender_canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.gender_canvas.wheelEvent = lambda e: None
        self.gender_canvas.figure.subplots_adjust(left=0.2, right=0.95, top=0.9, bottom=0.25)
        gl.addWidget(self.gender_canvas)
        left.addWidget(gf)

        # Age frame (taller)
        left.addWidget(QLabel("Age Distribution", objectName="cardTitle"))
        af = QFrame(objectName="chartFrame")
        af.setMinimumHeight(300)
        al = QVBoxLayout(af)
        al.setContentsMargins(0,0,0,0)
        self.age_canvas = FigureCanvas(plt.Figure(figsize=(6,4)))
        self.age_ax     = self.age_canvas.figure.add_subplot(111)
        self.age_canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.age_canvas.wheelEvent = lambda e: None
        self.age_canvas.figure.subplots_adjust(left=0.2, right=0.95, top=0.9, bottom=0.25)
        al.addWidget(self.age_canvas)
        left.addWidget(af)

        hl.addLayout(left, 1)

        # Right column
        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(QLabel("Visit Frequency", objectName="sectionTitle"))

        # Visitors chart frame (taller container)
        right.addWidget(QLabel("Top 10 Most Frequent Visitors", objectName="cardTitle"))
        cf = QFrame(objectName="visitorsChartFrame")
        cf.setMinimumHeight(350)
        clayout = QVBoxLayout(cf)
        clayout.setContentsMargins(0,0,0,0)
        self.visit_canvas = FigureCanvas(plt.Figure(figsize=(6,5)))
        self.visit_ax     = self.visit_canvas.figure.add_subplot(111)
        self.visit_canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.visit_canvas.wheelEvent = lambda e: None
        self.visit_canvas.figure.subplots_adjust(left=0.4, right=0.95, top=0.9, bottom=0.1)
        clayout.addWidget(self.visit_canvas)
        right.addWidget(cf)

        # Visitors table frame
        right.addWidget(QLabel("Frequent Visitors Details", objectName="cardTitle"))
        tf = QFrame(objectName="visitorsTableFrame")
        tf.setMinimumHeight(300)
        tl = QVBoxLayout(tf)
        tl.setContentsMargins(0,0,0,0)
        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(7)
        self.visit_table.setHorizontalHeaderLabels([
            'Patient ID','Name','Visit Count','First Visit',
            'Last Visit','Avg Days','Days Since Last'
        ])
        self.visit_table.verticalHeader().setVisible(False)
        self.visit_table.setAlternatingRowColors(True)
        hdr = self.visit_table.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tl.addWidget(self.visit_table)
        right.addWidget(tf)

        hl.addLayout(right, 1)
        main.addWidget(scroll)

        # initial load
        self.refresh_data()

    def refresh_data(self):
        for lbl, fn in self.cards.values():
            lbl.setText(str(fn()))
        self.load_demographics()
        self.load_visit_frequency()

    # Metric helpers
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
        # Gender pie
        gdf = pd.DataFrame(data['gender'], columns=['gender','count'])
        self.gender_ax.clear()
        wedges, texts, autos = self.gender_ax.pie(
            gdf['count'],
            labels=gdf['gender'],
            autopct='%1.1f%%',
            colors=[COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER][:len(gdf)],
            startangle=90,
            wedgeprops={'width':0.5, 'edgecolor':'w'}
        )
        for t in texts+autos:
            t.set_fontsize(10)
        self.gender_canvas.draw()

        # Age bar
        adf = pd.DataFrame(data['age'], columns=['age_group','count'])
        self.age_ax.clear()
        bars = self.age_ax.bar(adf['age_group'], adf['count'], color=COLOR_ACCENT)
        self.age_ax.set_xlabel('Age Group', fontsize=8)
        self.age_ax.set_ylabel('Count', fontsize=8)
        self.age_ax.tick_params(axis='x', rotation=45, labelsize=8)
        for bar in bars:
            h = bar.get_height()
            self.age_ax.annotate(f"{h}",
                                 xy=(bar.get_x()+bar.get_width()/2, h),
                                 xytext=(0,3), textcoords='offset points',
                                 ha='center', va='bottom', fontsize=8)
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
            nm.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.visit_table.setItem(r, 1, nm)
            vc = p['visit_count']
            vc_item = QTableWidgetItem(str(vc))
            if vc > 10:
                vc_item.setForeground(QColor(COLOR_SUCCESS))
                vc_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            elif vc > 5:
                vc_item.setForeground(QColor(COLOR_ACCENT))
            self.visit_table.setItem(r, 2, vc_item)
            self.visit_table.setItem(r, 3, QTableWidgetItem(p.get('first_visit','N/A')))
            self.visit_table.setItem(r, 4, QTableWidgetItem(p.get('last_visit','N/A')))
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

        # Horizontal bar chart
        df = pd.DataFrame(top10)
        ax = self.visit_ax
        ax.clear()
        y_pos = np.arange(len(df))
        bar_h = 0.6
        max_val = df['visit_count'].max()
        for y, val in zip(y_pos, df['visit_count']):
            rect = Rectangle((0, y - bar_h/2), val, bar_h,
                             color=COLOR_ACCENT, linewidth=0)
            ax.add_patch(rect)
            circ = Circle((val, y), bar_h/2, color=COLOR_ACCENT, linewidth=0)
            ax.add_patch(circ)
            offset = max_val * 0.05
            ax.text(val + offset, y, f"{val}", va='center', ha='left', fontsize=9)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['name'], fontsize=9)
        ax.set_ylim(-1, len(df))
        ax.invert_yaxis()
        ax.set_xlim(0, max_val * 1.1)
        ax.set_xlabel('Visit Count', fontsize=8)
        ax.tick_params(axis='x', labelsize=8)
        for s in ax.spines.values(): s.set_visible(False)
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')
        self.visit_canvas.draw()
