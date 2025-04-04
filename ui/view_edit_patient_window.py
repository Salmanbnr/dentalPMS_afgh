# dental_clinic/ui/view_edit_patient_window.py
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QSpinBox, QTextEdit, QPushButton, QMessageBox,
                             QApplication, QFormLayout, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta
from pathlib import Path

from database.data_manager import get_all_patients

# Adjust import path
try:
    from database.data_manager import get_patient_by_id, update_patient
except ImportError:
    print("Warning: Running view_edit_patient_window.py directly. Assuming 'database' directory is sibling.")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from database.data_manager import get_patient_by_id, update_patient
    except ImportError:
        print("Error: Cannot find data_manager. Please run from the project root directory.")
        sys.exit(1)

class ViewEditPatientWindow(QMainWindow):
    """Window for viewing and editing patient details."""
    patient_updated = pyqtSignal() # Signal emitted when patient is updated
    closed_signal = pyqtSignal()   # Signal emitted when this window is closed

    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.patient_data = None # Store loaded patient data

        self.setWindowTitle("View/Edit Patient Details")
        self.setGeometry(150, 150, 500, 550) # Slightly larger window

        # --- Central Widget and Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # --- Toolbar (for Back button) ---
        toolbar = self.addToolBar("Main Toolbar")
        back_action = toolbar.addAction(qta.icon('fa5s.arrow-left'), "Back")
        back_action.triggered.connect(self.close) # Close this window to go back [cite: 166]

        # --- Scroll Area for Form ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setContentsMargins(10, 10, 10, 10) # Add margins
        self.form_layout.setSpacing(10) # Add spacing
        self.scroll_area.setWidget(self.form_widget)

        # --- Widgets (inside the form layout) ---
        self.patient_id_label = QLabel(f"Patient ID: {self.patient_id}")
        self.name_input = QLineEdit()
        self.fname_input = QLineEdit()
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Male", "Female", "Other"])
        self.age_input = QSpinBox()
        self.age_input.setRange(0, 150)
        self.phone_input = QLineEdit()
        self.address_input = QTextEdit()
        self.address_input.setFixedHeight(80) # Slightly taller
        self.history_input = QTextEdit()
        self.history_input.setFixedHeight(100) # Slightly taller
        self.first_visit_label = QLabel("First Visit: N/A")
        self.last_updated_label = QLabel("Last Updated: N/A")

        # Add widgets to form layout
        self.form_layout.addRow(self.patient_id_label) # Display ID, not editable
        self.form_layout.addRow(QLabel("Name:"), self.name_input)
        self.form_layout.addRow(QLabel("Father's Name:"), self.fname_input)
        self.form_layout.addRow(QLabel("Gender:"), self.gender_input)
        self.form_layout.addRow(QLabel("Age:"), self.age_input)
        self.form_layout.addRow(QLabel("Phone Number:"), self.phone_input)
        self.form_layout.addRow(QLabel("Address:"), self.address_input)
        self.form_layout.addRow(QLabel("Medical History:"), self.history_input)
        self.form_layout.addRow(self.first_visit_label) # Read-only info
        self.form_layout.addRow(self.last_updated_label) # Read-only info


        # --- Save Button ---
        self.save_button = QPushButton(qta.icon('fa5s.save'), "Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        self.main_layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter) # Add button below scroll area

        # --- Load Data ---
        self.load_patient_data()

    def load_patient_data(self):
        """Load patient data from the database."""
        self.patient_data = get_patient_by_id(self.patient_id) # [cite: 100, 165]

        if self.patient_data:
            self.name_input.setText(self.patient_data.get('name', ''))
            self.fname_input.setText(self.patient_data.get('father_name', ''))
            self.gender_input.setCurrentText(self.patient_data.get('gender', 'Male')) # Default if missing
            self.age_input.setValue(self.patient_data.get('age', 0))
            self.phone_input.setText(self.patient_data.get('phone_number', ''))
            self.address_input.setPlainText(self.patient_data.get('address', ''))
            self.history_input.setPlainText(self.patient_data.get('medical_history', ''))

            # Display read-only info
            first_visit = self.patient_data.get('first_visit_date', 'N/A')
            last_updated = self.patient_data.get('last_updated', 'N/A')
            self.first_visit_label.setText(f"First Visit: {first_visit}")
            self.last_updated_label.setText(f"Last Updated: {last_updated}")

        else:
            QMessageBox.critical(self, "Error", f"Could not load data for patient ID: {self.patient_id}. This window will close.")
            self.close() # Close if data loading fails


    def save_changes(self):
        """Validate and save updated patient data."""
        if not self.patient_data: # Should not happen if load was successful
            QMessageBox.critical(self, "Error", "No patient data loaded.")
            return

        name = self.name_input.text().strip()
        fname = self.fname_input.text().strip()
        gender = self.gender_input.currentText()
        age = self.age_input.value()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()
        history = self.history_input.toPlainText().strip()

        # Basic Validation
        if not name:
            QMessageBox.warning(self, "Input Error", "Patient name cannot be empty.")
            return
        if not phone:
             QMessageBox.warning(self, "Input Error", "Phone number cannot be empty.")
             return

        # --- Call Data Manager to Update ---
        success = update_patient( # [cite: 101]
            self.patient_id, name, fname, gender, age, address, phone, history
        )

        if success is True:
            QMessageBox.information(self, "Success", f"Patient '{name}' (ID: {self.patient_id}) updated successfully.")
            self.patient_updated.emit() # Emit signal
            self.load_patient_data() # Reload data to show confirmation (like last_updated timestamp)
            # Optionally close after save: self.close()
        elif success is False: # e.g. Integrity error if phone became non-unique somehow (though constraint removed)
             QMessageBox.critical(self, "Database Error", "Could not update patient. There might be a conflict.")
        else: # General failure (None)
             QMessageBox.critical(self, "Database Error", "An error occurred while updating the patient.")

    def closeEvent(self, event):
        """Emit a signal when the window is closed."""
        self.closed_signal.emit()
        super().closeEvent(event)

# --- Testing Block --- [cite: 166]
if __name__ == '__main__':
    # Need a patient ID to test. Let's try adding one first if possible.
    TEST_PATIENT_ID = None
    print("Attempting to initialize database for ViewEditPatientWindow test...")
    try:
        from database.schema import initialize_database
        from database.data_manager import add_patient # Need this too
        if not initialize_database():
             print("Database initialization failed. Test may not work correctly.")
        else:
            print("Database initialized/verified successfully.")
            # Add a test patient if none exists or find an existing one
            all_patients = get_all_patients()
            if all_patients:
                TEST_PATIENT_ID = all_patients[0]['patient_id']
                print(f"Using existing patient ID: {TEST_PATIENT_ID}")
            else:
                print("Adding a temporary test patient...")
                temp_id = add_patient("Test", "Tester", "Other", 40, "1 Test St", "555-TEST", "Testing")
                if temp_id:
                    TEST_PATIENT_ID = temp_id
                    print(f"Added temporary patient with ID: {TEST_PATIENT_ID}")
                else:
                    print("Failed to add temporary patient.")

    except ImportError as e:
        print(f"Could not import database modules for test setup: {e}")

    if TEST_PATIENT_ID is None:
        print("Cannot proceed with test: No patient ID available.")
        sys.exit(1)


    app = QApplication(sys.argv)
    # Pass the test patient ID
    window = ViewEditPatientWindow(patient_id=TEST_PATIENT_ID)

    # Example of connecting signals for testing
    def on_patient_updated():
        print("Test: patient_updated signal received!")
    def on_window_closed():
        print("Test: View/Edit window closed_signal received!")

    window.patient_updated.connect(on_patient_updated)
    window.closed_signal.connect(on_window_closed)
    window.closed_signal.connect(app.quit) # Quit app when window closes for test

    window.show()
    sys.exit(app.exec())