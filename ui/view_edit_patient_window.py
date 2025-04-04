# dental_clinic/ui/view_edit_patient_window.py
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                             QMessageBox, QSplitter, QFrame)
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta
from pathlib import Path

# Use absolute imports assuming running from project root
try:
    from database.data_manager import get_all_patients # Keep this? Maybe not needed directly
    from ui.patient.patient_detail_widget import PatientDetailWidget
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from database.data_manager import get_all_patients
    from ui.patient.patient_detail_widget import PatientDetailWidget

class PatientViewEditWindow(QMainWindow): # Changed class name
    """
    Window displaying detailed patient information and visit management.
    Uses a splitter view with a patient list (optional/can be adapted)
    and the PatientDetailWidget.
    """
    def __init__(self, patient_id, parent=None): # Added patient_id to __init__
        super().__init__(parent)
        self.current_patient_id_to_load = patient_id # Store ID to load

        self.setWindowTitle(f"Patient Details & Visits (ID: {patient_id})") # Dynamic title
        self.setGeometry(150, 150, 700, 600) # Adjusted default size
        self.setWindowIcon(qta.icon('fa5s.notes-medical')) # Changed icon maybe

        # --- Central Widget and Main Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # Using QHBoxLayout directly might be simpler if we remove the list part
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5,5,5,5)

        # --- Remove Left Panel (Patient List) ---
        # This window is now focused on ONE patient passed via patient_id
        # So, the list and search from the previous version are removed.

        # --- Right Panel: Patient Details (Becomes the main content) ---
        # Instantiate the detail widget directly
        self.detail_area = PatientDetailWidget()

        # --- Add Detail Area directly to layout ---
        # No splitter needed if it's just the detail view
        self.main_layout.addWidget(self.detail_area)

        # --- Load Specific Patient Data ---
        # Load the patient passed during initialization
        if self.current_patient_id_to_load:
            self.detail_area.load_patient(self.current_patient_id_to_load)
        else:
            # Handle case where no ID was passed (though constructor requires it now)
             self.detail_area.clear_details()
             self.detail_area.patient_info_group.setTitle("No Patient ID Provided")

    # Remove methods related to the list widget and search (load_patient_list, filter_patient_list, on_patient_selected)
    # Add a closeEvent handler if needed, e.g., to emit a signal
    def closeEvent(self, event):
        print(f"Closing PatientViewEditWindow for patient ID: {self.current_patient_id_to_load}")
        # Add any cleanup if necessary
        super().closeEvent(event)

# Note: Removed the if __name__ == '__main__': block as this is intended to be imported.