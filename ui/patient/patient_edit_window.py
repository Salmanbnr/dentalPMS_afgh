# dental_clinic/ui/patient/patient_edit_window.py
import sys
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QComboBox, QSpinBox, QTextEdit, QPushButton, QMessageBox,
                             QFormLayout, QDialogButtonBox)
from PyQt6.QtCore import pyqtSignal, Qt, QDate
import qtawesome as qta
from pathlib import Path

# Use absolute imports assuming running from project root
try:
    from database.data_manager import get_patient_by_id, update_patient
except ImportError:
    # Add project root to path for standalone testing
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from database.data_manager import get_patient_by_id, update_patient


class PatientEditWindow(QDialog):
    """Dialog for editing existing patient details."""
    patient_updated = pyqtSignal(int) # Emit patient ID on successful update

    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.patient_data = None

        self.setWindowTitle(f"Edit Patient (ID: {self.patient_id})")
        self.setMinimumWidth(450)
        # self.setGeometry(200, 200, 450, 400) # Optional fixed geometry
        self.setModal(True) # Make it a modal dialog

        # --- Layout ---
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(10, 10, 10, 10)
        self.form_layout.setSpacing(10)
        self.main_layout.addLayout(self.form_layout)

        # --- Widgets ---
        self.name_input = QLineEdit()
        self.fname_input = QLineEdit()
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Male", "Female", "Other"])
        self.age_input = QSpinBox()
        self.age_input.setRange(0, 150)
        self.phone_input = QLineEdit() # Add validation later if needed
        self.address_input = QTextEdit()
        self.address_input.setFixedHeight(60)
        self.history_input = QTextEdit()
        self.history_input.setFixedHeight(80)

        # Add widgets to form layout
        self.form_layout.addRow(QLabel("Name:"), self.name_input)
        self.form_layout.addRow(QLabel("Father's / Husband:"), self.fname_input)
        self.form_layout.addRow(QLabel("Gender:"), self.gender_input)
        self.form_layout.addRow(QLabel("Age:"), self.age_input)
        self.form_layout.addRow(QLabel("Phone Number:"), self.phone_input)
        self.form_layout.addRow(QLabel("Address:"), self.address_input)
        self.form_layout.addRow(QLabel("Medical History:"), self.history_input)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept) # Triggers save_changes
        self.button_box.rejected.connect(self.reject) # Closes the dialog
        self.main_layout.addWidget(self.button_box)

        # --- Load Data ---
        if not self.load_patient_data():
             # Handle error during init if data load fails immediately
             QMessageBox.critical(self, "Error", f"Could not load data for patient ID: {self.patient_id}. Cannot open editor.")
             # We need to reject the dialog *after* the constructor finishes
             # Use a QTimer to call reject shortly after showing
             from PyQt6.QtCore import QTimer
             QTimer.singleShot(0, self.reject)


    def load_patient_data(self):
        """Load patient data from the database. Returns True if successful."""
        self.patient_data = get_patient_by_id(self.patient_id)
        if self.patient_data:
            self.name_input.setText(self.patient_data.get('name', ''))
            self.fname_input.setText(self.patient_data.get('father_name', ''))
            self.gender_input.setCurrentText(self.patient_data.get('gender', 'Male'))
            self.age_input.setValue(self.patient_data.get('age', 0))
            self.phone_input.setText(self.patient_data.get('phone_number', ''))
            self.address_input.setPlainText(self.patient_data.get('address', ''))
            self.history_input.setPlainText(self.patient_data.get('medical_history', ''))
            return True
        else:
            print(f"Error: Could not find patient data for ID: {self.patient_id}")
            return False

    def accept(self):
        """Overrides QDialog.accept() to perform validation and saving."""
        if self.save_changes():
            super().accept() # Close dialog with Accepted state if save is successful
        # Else: stay open, message box already shown by save_changes

    def save_changes(self):
        """Validate and save updated patient data. Returns True on success, False otherwise."""
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
            self.name_input.setFocus()
            return False
        # Add more validation as needed (e.g., phone format)

        # --- Call Data Manager to Update ---
        success = update_patient(
            self.patient_id, name, fname, gender, age, address, phone, history
        )

        if success is True:
            QMessageBox.information(self, "Success", f"Patient '{name}' (ID: {self.patient_id}) updated successfully.")
            self.patient_updated.emit(self.patient_id) # Emit signal with ID
            return True
        elif success is False:
            # Typically constraint error (e.g., if UNIQUE was added back to phone)
             QMessageBox.critical(self, "Database Error", "Could not update patient. Check for potential conflicts (e.g., unique constraints).")
             return False
        else: # General failure (None)
             QMessageBox.critical(self, "Database Error", "An unexpected error occurred while updating the patient.")
             return False

# --- Testing Block ---
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    # Make sure DB is initialized and has a patient (e.g., ID 1)
    try:
        from database.schema import initialize_database
        initialize_database()
        # Optional: Add a test patient if needed
        # from database.data_manager import add_patient
        # if not get_patient_by_id(1):
        #     add_patient("Test Edit", "Tester", "Other", 30, "1 Edit St", "555-EDIT", "Needs editing")
    except Exception as e:
        print(f"Error setting up DB for test: {e}")
        sys.exit(1)

    TEST_PATIENT_ID = 1 # Or get first patient ID dynamically

    app = QApplication(sys.argv)
    patient_data = get_patient_by_id(TEST_PATIENT_ID)

    if not patient_data:
        print(f"Cannot run test: Patient with ID {TEST_PATIENT_ID} not found.")
        sys.exit(1)

    print(f"Attempting to edit Patient ID: {TEST_PATIENT_ID}")
    window = PatientEditWindow(patient_id=TEST_PATIENT_ID)

    def on_patient_updated_test(updated_id):
        print(f"Test: patient_updated signal received for ID: {updated_id}!")
        reloaded_data = get_patient_by_id(updated_id)
        print(f"Reloaded data: {reloaded_data}")

    window.patient_updated.connect(on_patient_updated_test)

    result = window.exec() # Show the modal dialog

    if result == QDialog.DialogCode.Accepted:
        print("Edit window accepted (Save successful).")
    else:
        print("Edit window rejected (Cancel pressed or error).")

    # sys.exit(app.exec()) # Not needed for modal dialog test