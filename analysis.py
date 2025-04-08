from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar, QScrollArea
from PyQt6.QtCore import Qt
import qtawesome as qta
from ui.analysis.patient_analysis import PatientAnalysis
from ui.analysis.service_analysis import ServiceAnalysis
from ui.analysis.medication_analysis import MedicationAnalysis
from ui.analysis.financial_analysis import FinancialAnalysis
from ui.analysis.operational_analysis import OperationalAnalysis
from ui.analysis.data_quality_analysis import DataQualityAnalysis

COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

ANALYSIS_WINDOW_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_SECONDARY};
    }}
    QTabWidget {{
        border: none;
        background-color: {COLOR_SECONDARY};
        padding: 5px;
    }}
    QTabBar::tab {{
        background-color: {COLOR_SECONDARY};
        border: 2px solid {COLOR_BORDER};
        border-bottom: none;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 15px 30px;
        color: {COLOR_TEXT_DARK};
        margin-right: 4px;
        min-width: 150px;
        font-size: 12pt;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border-bottom: 3px solid {COLOR_PRIMARY};
        border: 2px solid {COLOR_PRIMARY};
    }}
    QTabBar::tab:hover {{
        background-color: {COLOR_HOVER};
        color: {COLOR_TEXT_LIGHT};
        border: 2px solid {COLOR_ACCENT};
    }}
    QTabWidget::pane {{
        border: 2px solid {COLOR_BORDER};
        border-radius: 6px;
        background-color: {COLOR_SECONDARY};
        padding: 15px;
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
"""

class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clinic Analysis Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(ANALYSIS_WINDOW_STYLESHEET)

        # Tab Widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget { border: none; }")

        # Add Tabs with Scroll Areas
        tabs = [
            ("Patient Analytics", PatientAnalysis(), qta.icon('fa5s.user', color=COLOR_TEXT_DARK)),
            ("Service Analytics", ServiceAnalysis(), qta.icon('fa5s.tooth', color=COLOR_TEXT_DARK)),
            ("Medication Analytics", MedicationAnalysis(), qta.icon('fa5s.pills', color=COLOR_TEXT_DARK)),
            ("Financial Analytics", FinancialAnalysis(), qta.icon('fa5s.dollar-sign', color=COLOR_TEXT_DARK)),
            ("Operational Analytics", OperationalAnalysis(), qta.icon('fa5s.calendar', color=COLOR_TEXT_DARK)),
            ("Data Quality", DataQualityAnalysis(), qta.icon('fa5s.database', color=COLOR_TEXT_DARK)),
        ]

        for title, widget, icon in tabs:
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(widget)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                }
            """)
            tab_widget.addTab(scroll_area, icon, title)

        # Set Central Widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(tab_widget)
        central_widget.setLayout(layout)
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