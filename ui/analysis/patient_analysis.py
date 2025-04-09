import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QScrollArea, QLabel,
    QFrame, QHeaderView, QApplication,
    QLineEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QFont, QPalette, QLinearGradient
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import pandas as pd
import qtawesome as qta
from model.analysis_model import (
    get_patient_demographics,
    get_patient_visit_frequency,
    get_inactive_patients,
    get_single_visit_patients
)

# --- New Color Palette (Warm and Professional) ---
COLOR_PRIMARY = "#4A90E2"  # Soft Blue
COLOR_SECONDARY = "#F7F9FC"  # Very Light Gray Background
COLOR_ACCENT = "#D4A017"  # Gold Accent
COLOR_SUCCESS = "#28A745"  # Green
COLOR_WARNING = "#FFC107"  # Amber
COLOR_DANGER = "#DC3545"  # Red
COLOR_INFO = "#6C757D"  # Gray
COLOR_TEXT_LIGHT = "#FFFFFF"  # White
COLOR_TEXT_DARK = "#333333"  # Dark Gray
COLOR_TEXT_MUTED = "#6C757D"  # Muted Gray
COLOR_BORDER = "#DEE2E6"  # Light Gray Border
COLOR_CHART_BG = "#FFFFFF"  # White Chart Background
COLOR_TABLE_ALT_ROW = "#F8F9FA"  # Light Gray for Alternating Rows

# --- Stylesheet ---
DASHBOARD_STYLESHEET = f"""
QWidget {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_TEXT_DARK};
    font-family: 'Roboto', 'Segoe UI', sans-serif;
    font-size: 11pt;
}}
QLineEdit {{
    background-color: {COLOR_CHART_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
}}
QLineEdit:focus {{ border: 2px solid {COLOR_ACCENT}; }}
QTableWidget {{
    background-color: {COLOR_CHART_BG};
    border: none;
    gridline-color: {COLOR_BORDER};
    alternate-background-color: {COLOR_TABLE_ALT_ROW};
    border-radius: 8px;
}}
QHeaderView::section {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLOR_PRIMARY}, stop:1 {COLOR_INFO});
    color: {COLOR_TEXT_LIGHT};
    padding: 10px;
    font-weight: 600;
    border-bottom: 1px solid {COLOR_BORDER};
}}
QFrame {{
    border-radius: 12px;
    background-color: {COLOR_CHART_BG};
}}
"""

class PatientAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DASHBOARD_STYLESHEET)
        self.setWindowTitle("Patient Analytics Dashboard")
        self.setMinimumSize(800, 900)  # Reduced minimum width for side panel compatibility
        self.init_ui()
        QTimer.singleShot(100, self.load_all_data)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Reduced margins for compactness
        main_layout.setSpacing(15)

        # Header with Shadow
        header_frame = QFrame()
        header_frame.setMaximumHeight(80)
        header_layout = QVBoxLayout(header_frame)
        title = QLabel("Patient Analytics Dashboard")
        title.setFont(QFont('Roboto', 24, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        subtitle = QLabel("Real-time insights into patient demographics and visit trends")
        subtitle.setFont(QFont('Roboto', 10))
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        header_frame.setGraphicsEffect(shadow)
        main_layout.addWidget(header_frame)

        # Overview Cards (Reduced size and number for compactness)
        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(15)
        cards_layout.setVerticalSpacing(15)
        self.cards = {}
        metrics = [
            ("Total Patients", "fa5s.users", COLOR_INFO, self.get_total_patients),
            ("Active Patients", "fa5s.user-check", COLOR_SUCCESS, self.get_active_patients),
            ("Single-Visit", "fa5s.user-clock", COLOR_WARNING, self.get_single_visit_count),
            ("Inactive", "fa5s.user-times", COLOR_DANGER, self.get_inactive_count),
        ]
        for i, (text, icon, color, func) in enumerate(metrics):
            card = QFrame()
            card.setMinimumHeight(100)  # Reduced height
            layout = QVBoxLayout(card)
            layout.setContentsMargins(15, 15, 15, 15)
            row = QHBoxLayout()
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon(icon, color=color).pixmap(30, 30))  # Smaller icons
            row.addWidget(icon_lbl)
            lbl = QLabel(text)
            lbl.setFont(QFont('Roboto', 10, QFont.Weight.Medium))
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
            row.addWidget(lbl)
            row.addStretch()
            layout.addLayout(row)
            val = QLabel("--")
            val.setFont(QFont('Roboto', 18, QFont.Weight.Bold))  # Reduced font size
            val.setStyleSheet(f"color: {color};")
            layout.addWidget(val)
            self.cards[text] = (val, func)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 20))
            shadow.setOffset(0, 3)
            card.setGraphicsEffect(shadow)
            cards_layout.addWidget(card, 0, i)
        main_layout.addLayout(cards_layout)

        # Main Content (No horizontal scroll, vertical scroll only if needed)
        container = QWidget()
        cont_layout = QHBoxLayout(container)
        cont_layout.setSpacing(15)
        cont_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Charts (Flexible width)
        left = QVBoxLayout()
        left.setSpacing(15)

        # Gender Chart
        self.gender_frame = QFrame()
        self.gender_frame.setMinimumHeight(300)  # Reduced height
        self.gender_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:10px;")
        g_layout = QVBoxLayout(self.gender_frame)
        g_layout.setContentsMargins(10, 10, 10, 10)
        self.gender_canvas = FigureCanvas(plt.Figure(facecolor=COLOR_CHART_BG, tight_layout=True))
        self.gender_ax = self.gender_canvas.figure.add_subplot(111)
        g_layout.addWidget(self.gender_canvas)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        self.gender_frame.setGraphicsEffect(shadow)
        left.addWidget(self.gender_frame)

        # Age Chart
        self.age_frame = QFrame()
        self.age_frame.setMinimumHeight(350)  # Reduced height
        self.age_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:10px;")
        a_layout = QVBoxLayout(self.age_frame)
        a_layout.setContentsMargins(10, 10, 10, 10)
        self.age_canvas = FigureCanvas(plt.Figure(facecolor=COLOR_CHART_BG, tight_layout=True))
        self.age_ax = self.age_canvas.figure.add_subplot(111)
        a_layout.addWidget(self.age_canvas)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        self.age_frame.setGraphicsEffect(shadow)
        left.addWidget(self.age_frame)
        left.addStretch()

        # Right: Visits (Flexible width)
        right = QVBoxLayout()
        right.setSpacing(15)

        # Visitors Bar Chart
        chart_frame = QFrame()
        chart_frame.setMinimumHeight(350)  # Reduced height
        chart_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:10px;")
        c_layout = QVBoxLayout(chart_frame)
        c_layout.setContentsMargins(10, 10, 10, 10)
        self.visit_canvas = FigureCanvas(plt.Figure(facecolor=COLOR_CHART_BG, tight_layout=True))
        self.visit_ax = self.visit_canvas.figure.add_subplot(111)
        c_layout.addWidget(self.visit_canvas)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        chart_frame.setGraphicsEffect(shadow)
        right.addWidget(chart_frame)

        # Visitors Table + Search
        table_frame = QFrame()
        table_frame.setMinimumHeight(300)  # Reduced height
        table_frame.setStyleSheet(f"background-color: {COLOR_CHART_BG}; border-radius:10px;")
        t_layout = QVBoxLayout(table_frame)
        t_layout.setContentsMargins(10, 10, 10, 10)
        hdr = QHBoxLayout()
        tbl_lbl = QLabel("Top Visitors")
        tbl_lbl.setFont(QFont('Roboto', 12, QFont.Weight.Bold))
        tbl_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")
        hdr.addWidget(tbl_lbl)
        hdr.addStretch()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by name...")
        self.search_bar.setFixedWidth(200)  # Fixed width for search bar
        self.search_bar.setStyleSheet(f"border-radius: 8px; padding: 6px;")
        self.search_bar.textChanged.connect(self.filter_table)
        hdr.addWidget(self.search_bar)
        t_layout.addLayout(hdr)
        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(7)
        self.visit_table.setHorizontalHeaderLabels([
            'ID', 'Name', 'Visits', 'First', 'Last', 'Avg Days', 'Days Since'
        ])  # Shortened labels
        self.visit_table.verticalHeader().setVisible(False)
        self.visit_table.setAlternatingRowColors(True)
        self.visit_table.setShowGrid(False)
        self.visit_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        hdr_view = self.visit_table.horizontalHeader()
        hdr_view.setDefaultAlignment(Qt.AlignCenter)
        hdr_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # Stretch all columns
        t_layout.addWidget(self.visit_table)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        table_frame.setGraphicsEffect(shadow)
        right.addWidget(table_frame)
        right.addStretch()

        # Ensure no horizontal scroll by setting maximum width and flexible layout
        cont_layout.addLayout(left, 1)  # Left takes 50% of space
        cont_layout.addLayout(right, 1)  # Right takes 50% of space
        main_layout.addWidget(container)

    def load_all_data(self):
        self.update_overview()
        self.load_demographics()
        self.load_visits()

    def update_overview(self):
        for text, (lbl, func) in self.cards.items():
            try:
                lbl.setText(f"{func():,}")
            except:
                lbl.setText("N/A")

    def load_demographics(self):
        data = get_patient_demographics() or {}
        ax = self.gender_ax
        ax.clear()
        gd = data.get('gender', [])
        if gd:
            df = pd.DataFrame(gd, columns=['gender', 'count'])
            colors = [COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_INFO][:len(df)]
            wedges, _, autotexts = ax.pie(
                df['count'], autopct='%1.1f%%', pctdistance=0.7,
                colors=colors, startangle=90, wedgeprops={'width': 0.4, 'edgecolor': 'white', 'linewidth': 1},
                textprops={'color': COLOR_TEXT_LIGHT, 'fontsize': 10, 'weight': 'bold'}
            )
            ax.legend(wedges, df['gender'], title="Gender", loc='center left', bbox_to_anchor=(1, 0.5),
                      facecolor=COLOR_SECONDARY, edgecolor=COLOR_BORDER, title_fontsize=10)
            ax.set_title('Gender Distribution', fontsize=14, color=COLOR_PRIMARY, pad=15)
            ax.axis('equal')
        else:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', color=COLOR_TEXT_MUTED, fontsize=12)
        self.gender_canvas.draw_idle()

        ax = self.age_ax
        ax.clear()
        ad = data.get('age', [])
        if ad:
            df = pd.DataFrame(ad, columns=['age_group', 'count']).sort_values('age_group')
            bars = ax.bar(df['age_group'], df['count'], color=COLOR_SUCCESS, edgecolor='white', linewidth=1)
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height, f'{int(height)}', ha='center', va='bottom',
                        fontsize=8, color=COLOR_TEXT_DARK)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color(COLOR_BORDER)
            ax.spines['left'].set_color(COLOR_BORDER)
            ax.set_title('Age Distribution', fontsize=14, color=COLOR_PRIMARY, pad=15)
            ax.tick_params(axis='both', colors=COLOR_TEXT_MUTED, labelsize=8)
        else:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', color=COLOR_TEXT_MUTED, fontsize=12)
        self.age_canvas.draw_idle()

    def load_visits(self):
        data = get_patient_visit_frequency() or []
        top = sorted(data, key=lambda x: x.get('visit_count') or 0, reverse=True)[:8]  # Reduced to 8 for space

        # Populate Table
        tbl = self.visit_table
        tbl.clearContents()
        tbl.setRowCount(len(top))
        for r, p in enumerate(top):
            pid = p.get('patient_id', '')
            name = p.get('name', '')
            vc = p.get('visit_count') or 0
            fv = p.get('first_visit', '')
            lv = p.get('last_visit', '')
            avg = p.get('avg_days_between_visits') or 0
            dsl = p.get('days_since_last_visit') or 0
            self.set_item(r, 0, str(pid), align=Qt.AlignCenter)
            self.set_item(r, 1, name, bold=True)
            iv = self.set_item(r, 2, str(vc), align=Qt.AlignRight)
            if vc > 10: iv.setForeground(QColor(COLOR_SUCCESS))
            self.set_item(r, 3, fv, align=Qt.AlignCenter)
            self.set_item(r, 4, lv, align=Qt.AlignCenter)
            self.set_item(r, 5, f"{avg:.1f}", align=Qt.AlignRight)
            idl = self.set_item(r, 6, str(dsl), align=Qt.AlignRight)
            if dsl > 90: idl.setForeground(QColor(COLOR_DANGER))
            elif dsl > 60: idl.setForeground(QColor(COLOR_WARNING))

        tbl.resizeColumnsToContents()

        # Horizontal Bar Chart
        ax = self.visit_ax
        ax.clear()
        if top:
            df = pd.DataFrame(top)
            names = df['name']
            counts = df['visit_count'].fillna(0)
            y_pos = range(len(names))
            bars = ax.barh(y_pos, counts, height=0.3, align='center', color=COLOR_ACCENT, edgecolor='white', linewidth=1)
            for bar in bars:
                bar.set_linewidth(0)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names, fontsize=8, color=COLOR_TEXT_DARK)
            ax.invert_yaxis()
            ax.set_xlabel('Total Visits', color=COLOR_TEXT_MUTED, fontsize=10)
            ax.set_title('Top Visitors', fontsize=14, color=COLOR_PRIMARY, pad=15)
            max_count = counts.max() if not counts.empty else 1
            for i, v in enumerate(counts):
                ax.text(v + max_count*0.02, i, str(int(v)), va='center', ha='left', fontsize=8, color=COLOR_TEXT_DARK)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_color(COLOR_BORDER)
            ax.tick_params(axis='both', colors=COLOR_TEXT_MUTED, labelsize=8)
        else:
            ax.text(0.5, 0.5, 'No Visit Data', ha='center', va='center', color=COLOR_TEXT_MUTED, fontsize=12)
        self.visit_canvas.draw_idle()

    def set_item(self, row, col, text, bold=False, align=Qt.AlignLeft):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        font = QFont('Roboto', 9)
        if bold: font.setWeight(QFont.Weight.Bold)
        item.setFont(font)
        item.setTextAlignment(int(align) | int(Qt.AlignVCenter))
        self.visit_table.setItem(row, col, item)
        return item

    def filter_table(self, txt):
        txt = txt.lower()
        for r in range(self.visit_table.rowCount()):
            itm = self.visit_table.item(r, 1)
            hide = txt not in itm.text().lower()
            self.visit_table.setRowHidden(r, hide)

    # metrics
    def get_total_patients(self):
        return sum(x['count'] for x in (get_patient_demographics() or {}).get('gender', []))
    def get_active_patients(self):
        return self.get_total_patients() - len(get_inactive_patients() or [])
    def get_single_visit_count(self):
        return len(get_single_visit_patients() or [])
    def get_inactive_count(self):
        return len(get_inactive_patients() or [])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = PatientAnalysis()
    window.show()
    sys.exit(app.exec())