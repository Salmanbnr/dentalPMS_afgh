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
    # Signal to notify when the back button is clicked
    back_button_clicked = pyqtSignal()
    # Signal to notify when data has been changed
    data_changed = pyqtSignal(int)

    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        self.current_patient_id = patient_id  # Store the patient ID

        self.setWindowTitle(f"Patient Details & Visits (ID: {patient_id})")
        self.setGeometry(150, 150, 700, 600)
        self.setWindowIcon(qta.icon('fa5s.notes-medical'))

        # --- Central Widget and Main Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Back Button ---
        self.back_button = QPushButton(qta.icon('fa5s.arrow-left', color='white'), " Back")
        self.back_button.setStyleSheet("background-color: #3498db; color: white;")
        self.back_button.clicked.connect(self.on_back_button_clicked)
        self.main_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Patient Detail Widget ---
        self.detail_area = PatientDetailWidget()
        self.main_layout.addWidget(self.detail_area)

        # --- Load Specific Patient Data ---
        self.load_patient_data(self.current_patient_id)

    def load_patient_data(self, patient_id):
        """Load the patient data using the PatientDetailWidget."""
        if patient_id:
            self.detail_area.load_patient(patient_id)
        else:
            self.detail_area.clear_details()
            self.detail_area.patient_info_group.setTitle("No Patient ID Provided")

    def on_back_button_clicked(self):
        """Emit the signal when the back button is clicked."""
        self.back_button_clicked.emit()

    def closeEvent(self, event):
        """Handle any cleanup or signal emission when the window is closed."""
        print(f"Closing PatientViewEditWindow for patient ID: {self.current_patient_id}")
        self.data_changed.emit(self.current_patient_id)  # Emit signal if data might have changed
        super().closeEvent(event)
