# dental_clinic/ui/add_patient_dialog.py
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QSpinBox, QTextEdit, QPushButton, QMessageBox,
                             QApplication, QDialogButtonBox, QFormLayout)
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta
from pathlib import Path

# Adjust import path - Assuming this runs from the root via main.py
try:
    from database.data_manager import add_patient
except ImportError:
    # Simple fallback for direct execution (testing) - requires database dir to be sibling
    print("Warning: Running add_patient_dialog.py directly. Assuming 'database' directory is sibling.")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from database.data_manager import add_patient
    except ImportError:
        print("Error: Cannot find data_manager. Please run from the project root directory.")
        sys.exit(1)

class AddPatientDialog(QDialog):
    """Dialog for adding a new patient."""
    patient_added = pyqtSignal() # Signal emitted when a patient is successfully added

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Patient")
        self.setMinimumWidth(400)
        self.setModal(True) # Make it a modal dialog

        # --- Widgets ---
        self.name_input = QLineEdit()
        self.fname_input = QLineEdit()
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Male", "Female", "Other"])
        self.age_input = QSpinBox()
        self.age_input.setRange(0, 150)
        self.phone_input = QLineEdit()
        self.address_input = QTextEdit()
        self.address_input.setFixedHeight(60) # Smaller height for address
        self.history_input = QTextEdit()
        self.history_input.setFixedHeight(80) # Slightly larger for history

        # --- Layout ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow(QLabel("Name:"), self.name_input)
        form_layout.addRow(QLabel("Father's Name:"), self.fname_input)
        form_layout.addRow(QLabel("Gender:"), self.gender_input)
        form_layout.addRow(QLabel("Age:"), self.age_input)
        form_layout.addRow(QLabel("Phone Number:"), self.phone_input)
        form_layout.addRow(QLabel("Address:"), self.address_input)
        form_layout.addRow(QLabel("Medical History:"), self.history_input)

        layout.addLayout(form_layout)

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept_data)
        self.button_box.rejected.connect(self.reject) # QDialog's reject slot

        layout.addWidget(self.button_box)

    def accept_data(self):
        """Validate and save patient data."""
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
        if not phone: # Example: require phone number
             QMessageBox.warning(self, "Input Error", "Phone number cannot be empty.")
             return

        # --- Call Data Manager ---
        patient_id = add_patient(name, fname, gender, age, address, phone, history) # [cite: 99, 163]

        if patient_id is not None:
            QMessageBox.information(self, "Success", f"Patient '{name}' added successfully with ID: {patient_id}.")
            self.patient_added.emit() # Emit signal
            self.accept() # Close dialog successfully
        elif patient_id is False: # Specific case like IntegrityError
             QMessageBox.critical(self, "Database Error", "Could not add patient. A patient with similar unique details might already exist.")
        else: # General failure (None)
            QMessageBox.critical(self, "Database Error", "An error occurred while adding the patient.")
            # Optionally keep the dialog open for correction, or close:
            # self.reject()


# --- Testing Block --- [cite: 166]
if __name__ == '__main__':
    # Ensure the database exists for testing this dialog standalone
    print("Attempting to initialize database for AddPatientDialog test...")
    try:
        from database.schema import initialize_database
        if not initialize_database():
             print("Database initialization failed. Dialog test may not work correctly.")
        else:
            print("Database initialized/verified successfully.")
    except ImportError:
        print("Could not import initialize_database. Ensure schema.py is accessible.")
        # Decide if you want to proceed without DB init or exit
        # sys.exit(1)


    app = QApplication(sys.argv)
    dialog = AddPatientDialog()

    # Example of connecting the signal if needed for testing interaction
    def on_patient_added():
        print("Test: patient_added signal received!")

    dialog.patient_added.connect(on_patient_added)

    # Show the dialog modally
    if dialog.exec() == QDialog.DialogCode.Accepted:
         print("Dialog accepted (patient likely added).")
    else:
         print("Dialog cancelled or closed.")

    # No sys.exit(app.exec()) needed here as dialog.exec() blocks