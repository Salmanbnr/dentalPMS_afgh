# ui/analysis.py
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import qtawesome as qta
from ui.analysis.patient_analysis import PatientAnalysis
from ui.analysis.service_analysis import ServiceAnalysis
from ui.analysis.medication_analysis import MedicationAnalysis
from ui.analysis.financial_analysis import FinancialAnalysis
from ui.analysis.operational_analysis import OperationalAnalysis
from ui.analysis.data_quality_analysis import DataQualityAnalysis

class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clinic Analysis Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #1e1e2f;")

        # Tab Widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3e3e5f;
                background-color: #2d2d44;
            }
            QTabBar::tab {
                background-color: #3e3e5f;
                color: #ffffff;
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #42a5f5;
            }
        """)

        # Patient Analysis Tab
        patient_tab = PatientAnalysis()
        tab_widget.addTab(patient_tab, qta.icon('fa5s.user', color='white'), "Patient Analytics")

        # Service Analysis Tab
        service_tab = ServiceAnalysis()
        tab_widget.addTab(service_tab, qta.icon('fa5s.tooth', color='white'), "Service Analytics")

        # Medication Analysis Tab
        medication_tab = MedicationAnalysis()
        tab_widget.addTab(medication_tab, qta.icon('fa5s.pills', color='white'), "Medication Analytics")

        # Financial Analysis Tab
        financial_tab = FinancialAnalysis()
        tab_widget.addTab(financial_tab, qta.icon('fa5s.dollar-sign', color='white'), "Financial Analytics")

        # Operational Analysis Tab
        operational_tab = OperationalAnalysis()
        tab_widget.addTab(operational_tab, qta.icon('fa5s.calendar', color='white'), "Operational Analytics")

        # Data Quality Tab
        data_quality_tab = DataQualityAnalysis()
        tab_widget.addTab(data_quality_tab, qta.icon('fa5s.database', color='white'), "Data Quality")

        # Set Central Widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(tab_widget)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def wheelEvent(self, event):
        event.ignore()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = AnalysisWindow()
    window.show()
    sys.exit(app.exec())