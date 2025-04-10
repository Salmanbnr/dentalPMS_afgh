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

# Use the same colors as PatientListPage
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

ADD_PATIENT_DIALOG_STYLESHEET = f"""
    #AddPatientDialog {{
        background-color: {COLOR_SECONDARY};
        border-radius: 8px;
        padding: 15px;
    }}

    #AddPatientDialog QLabel {{
        font-size: 10pt;
        color: {COLOR_TEXT_DARK};
        padding: 5px 0;
    }}

    #AddPatientDialog QLineEdit, #AddPatientDialog QSpinBox, #AddPatientDialog QComboBox {{
        padding: 8px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        font-size: 10pt;
        background-color: white;
    }}

    #AddPatientDialog QTextEdit {{
        padding: 8px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        font-size: 10pt;
        background-color: white;
        min-height: 60px;
    }}

    #AddPatientDialog QDialogButtonBox QPushButton {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border: none;
        padding: 8px 15px;
        border-radius: 4px;
        font-size: 10pt;
        min-width: 80px;
    }}

    #AddPatientDialog QDialogButtonBox QPushButton:hover {{
        background-color: {COLOR_HOVER};
    }}

    #AddPatientDialog QDialogButtonBox QPushButton:pressed {{
        background-color: {COLOR_PRIMARY};
    }}
"""

class AddPatientDialog(QDialog):
    """Dialog for adding a new patient."""
    patient_added = pyqtSignal()  # Signal emitted when a patient is successfully added

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Patient")
        self.setMinimumWidth(450)
        self.setModal(True)  # Make it a modal dialog
        self.setObjectName("AddPatientDialog")  # For QSS styling
        self.setStyleSheet(ADD_PATIENT_DIALOG_STYLESHEET)  # Apply styles

        # --- Widgets ---
        self.name_input = QLineEdit()
        self.fname_input = QLineEdit()
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Male", "Female", "Other"])
        self.age_input = QSpinBox()
        self.age_input.setRange(0, 150)
        self.phone_input = QLineEdit()
        self.address_input = QTextEdit()
        self.address_input.setFixedHeight(80)  # Adjusted for better visibility
        self.history_input = QTextEdit()
        self.history_input.setFixedHeight(100)  # Adjusted for better visibility

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Add form fields with icons for a modern touch
        form_layout.addRow(QLabel("Name:"), self.name_input)
        form_layout.addRow(QLabel("Father's / Husband:"), self.fname_input)
        form_layout.addRow(QLabel("Gender:"), self.gender_input)
        form_layout.addRow(QLabel("Age:"), self.age_input)
        form_layout.addRow(QLabel("Phone Number:"), self.phone_input)
        form_layout.addRow(QLabel("Address:"), self.address_input)
        form_layout.addRow(QLabel("Medical History:"), self.history_input)

        layout.addLayout(form_layout)

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        save_icon = qta.icon('fa5s.save', color=COLOR_TEXT_LIGHT)
        cancel_icon = qta.icon('fa5s.times', color=COLOR_TEXT_LIGHT)

        save_button.setIcon(save_icon)
        cancel_button.setIcon(cancel_icon)

        self.button_box.accepted.connect(self.accept_data)
        self.button_box.rejected.connect(self.reject)  # QDialog's reject slot

        layout.addWidget(self.button_box)

        # Set window icon (optional, for a polished look)
        self.setWindowIcon(qta.icon('fa5s.user-plus', color=COLOR_ACCENT))

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
        if not phone:  # Example: require phone number
            QMessageBox.warning(self, "Input Error", "Phone number cannot be empty.")
            return

        # --- Call Data Manager ---
        patient_id = add_patient(name, fname, gender, age, address, phone, history)

        if patient_id is not None:
            QMessageBox.information(self, "Success", f"Patient '{name}' added successfully with ID: {patient_id}.")
            self.patient_added.emit()  # Emit signal
            self.accept()  # Close dialog successfully
        elif patient_id is False:  # Specific case like IntegrityError
            QMessageBox.critical(self, "Database Error", "Could not add patient. A patient with similar unique details might already exist.")
        else:  # General failure (None)
            QMessageBox.critical(self, "Database Error", "An error occurred while adding the patient.")

# --- Testing Block ---
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

    app = QApplication(sys.argv)
    dialog = AddPatientDialog()

    def on_patient_added():
        print("Test: patient_added signal received!")

    dialog.patient_added.connect(on_patient_added)

    # Show the dialog modally
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Dialog accepted (patient likely added).")
    else:
        print("Dialog cancelled or closed.")