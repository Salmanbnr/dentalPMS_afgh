from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStatusBar, QScrollArea
from PyQt6.QtCore import Qt
import qtawesome as qta
from ui.analysis.patient_analysis import PatientAnalysis
from ui.analysis.service_analysis import ServiceAnalysis
from ui.analysis.financial_analysis import FinancialAnalysis
from ui.analysis.operational_analysis import OperationalAnalysis

# Color Definitions
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

# Stylesheet for Single Page Layout
ANALYSIS_WINDOW_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_SECONDARY};
    }}
    QStatusBar {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        border-top: 2px solid {COLOR_BORDER};
        padding: 8px;
        font-size: 10pt;
    }}
    QScrollArea {{
        border: none;
        background-color: {COLOR_SECONDARY};
    }}
    QScrollBar:vertical {{
        border: none;
        background: {COLOR_SECONDARY};
        width: 12px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 20px;
        border-radius: 6px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}
    QWidget#sectionWidget {{
        background-color: {COLOR_SECONDARY};
        border: 2px solid {COLOR_BORDER};
        border-radius: 6px;
        margin-bottom: 15px;
    }}
"""

class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clinic Analysis Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(ANALYSIS_WINDOW_STYLESHEET)

        # Central Widget with Scroll Area
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # Content Widget to hold all sections
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        # List of analysis sections
        sections = [
            ("Patient Analytics", PatientAnalysis(), qta.icon('fa5s.user', color=COLOR_TEXT_DARK)),
            ("Service Analytics", ServiceAnalysis(), qta.icon('fa5s.tooth', color=COLOR_TEXT_DARK)),
            ("Financial Analytics", FinancialAnalysis(), qta.icon('fa5s.dollar-sign', color=COLOR_TEXT_DARK)),
            ("Operational Analytics", OperationalAnalysis(), qta.icon('fa5s.calendar', color=COLOR_TEXT_DARK)),
        ]

        # Add each section to the content layout
        for title, widget, icon in sections:
            section_widget = QWidget(objectName="sectionWidget")
            section_layout = QVBoxLayout(section_widget)
            section_layout.setContentsMargins(15, 15, 15, 15)
            section_layout.setSpacing(10)
            section_layout.addWidget(widget)
            content_layout.addWidget(section_widget)

        # Add stretch to push content up
        content_layout.addStretch()

        # Set content widget into scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Analysis Dashboard Ready")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = AnalysisWindow()
    window.show()
    sys.exit(app.exec())