import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta
from pathlib import Path

# Use absolute imports assuming running from project root
try:
    from database.data_manager import get_all_patients
    from ui.patient.patient_detail_widget import PatientDetailWidget
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from database.data_manager import get_all_patients
    from ui.patient.patient_detail_widget import PatientDetailWidget

class PatientViewEditWindow(QMainWindow):
    """
    Window displaying detailed patient information and visit management.
    Uses a PatientDetailWidget to show patient details and manage visits.
    """
    back_button_clicked = pyqtSignal()
    data_changed = pyqtSignal(int)

    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        self.current_patient_id = patient_id
        self.setWindowTitle(f"Patient Details & Visits (ID: {patient_id})")
        self.resize(800, 650)
        self.setWindowIcon(qta.icon('fa5s.notes-medical'))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)  # Adjust margins if needed
        self.main_layout.setSpacing(15)

        self.back_button = QPushButton(qta.icon('fa5s.arrow-left', color='white'), " Back")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.back_button.clicked.connect(self.on_back_button_clicked)
        self.main_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.detail_area = PatientDetailWidget()
        self.main_layout.addWidget(self.detail_area)

        self.load_patient_data(self.current_patient_id)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QWidget {
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                color: #333;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 15px;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
            }
            QLabel {
                padding: 5px;
            }
        """)

    def load_patient_data(self, patient_id):
        if patient_id:
            self.detail_area.load_patient(patient_id)
        else:
            self.detail_area.clear_details()
            self.detail_area.patient_info_group.setTitle("No Patient ID Provided")

    def on_back_button_clicked(self):
        self.back_button_clicked.emit()

    def closeEvent(self, event):
        print(f"Closing PatientViewEditWindow for patient ID: {self.current_patient_id}")
        self.data_changed.emit(self.current_patient_id)
        super().closeEvent(event)
