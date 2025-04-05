# ui/visit/visit_detail_window.py

import sys
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QFormLayout, QDialogButtonBox, QGroupBox)
from PyQt6.QtCore import Qt, QDate

from database.data_manager import get_medication_by_id, get_patient_by_id, get_service_by_id, get_visit_by_id
from model.visit_manager import load_visit_data

class VisitDetailWindow(QDialog):
    """Dialog to display the details of a specific visit."""

    def __init__(self, visit_id, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.visit_data = None
        self.patient_data = None
        self.services = []
        self.prescriptions = []

        self.setWindowTitle(f"Visit Details (ID: {self.visit_id})")
        self.setMinimumWidth(650)
        self.setMinimumHeight(500)
        self.setModal(True)

        # --- Layouts ---
        self.main_layout = QVBoxLayout(self)

        # --- Load Data ---
        if not self.load_data():
            QMessageBox.critical(self, "Error", f"Could not load data for visit ID: {self.visit_id}. Cannot open details.")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.reject)
            return # Stop further init if load fails

        # --- Widgets ---
        # Patient Info Group
        patient_group = QGroupBox("Patient Information")
        patient_layout = QFormLayout(patient_group)
        self.patient_name_label = QLabel(self.patient_data.get('name', 'N/A'))
        self.patient_id_label = QLabel(str(self.patient_data.get('patient_id', 'N/A')))
        patient_layout.addRow("Patient Name:", self.patient_name_label)
        patient_layout.addRow("Patient ID:", self.patient_id_label)

        # Visit Info Group
        visit_group = QGroupBox("Visit Information")
        visit_layout = QFormLayout(visit_group)
        self.visit_date_label = QLabel(self.visit_data.get('visit_date', 'N/A'))
        self.notes_display = QTextEdit(self.visit_data.get('notes', ''))
        self.notes_display.setReadOnly(True)
        self.notes_display.setFixedHeight(60)
        self.lab_results_display = QTextEdit(self.visit_data.get('lab_results', ''))
        self.lab_results_display.setReadOnly(True)
        self.lab_results_display.setFixedHeight(60)
        visit_layout.addRow("Visit Date:", self.visit_date_label)
        visit_layout.addRow("Notes:", self.notes_display)
        visit_layout.addRow("Lab Results:", self.lab_results_display)

        # Services Table
        services_group = QGroupBox("Services Performed")
        services_layout = QVBoxLayout(services_group)
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels(["Service", "Tooth #", "Price Charged", "Notes"])
        self.services_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.services_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
        self.populate_services_table()
        services_layout.addWidget(self.services_table)

        # Prescriptions Table
        prescriptions_group = QGroupBox("Prescriptions Issued")
        prescriptions_layout = QVBoxLayout(prescriptions_group)
        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setColumnCount(4)
        self.prescriptions_table.setHorizontalHeaderLabels(["Medication", "Qty", "Price Charged", "Instructions"])
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
        self.populate_prescriptions_table()
        prescriptions_layout.addWidget(self.prescriptions_table)

        # Financial Summary Group
        finance_group = QGroupBox("Financial Summary")
        finance_layout = QFormLayout(finance_group)
        self.total_amount_label = QLabel(f"{self.visit_data.get('total_amount', 0.0):.2f}")
        self.paid_amount_label = QLabel(f"{self.visit_data.get('paid_amount', 0.0):.2f}")
        self.due_amount_label = QLabel(f"{self.visit_data.get('due_amount', 0.0):.2f}")
        finance_layout.addRow("Total Amount:", self.total_amount_label)
        finance_layout.addRow("Amount Paid:", self.paid_amount_label)
        finance_layout.addRow("Amount Due:", self.due_amount_label)

        # --- Add Widgets to Main Layout ---
        self.main_layout.addWidget(patient_group)
        self.main_layout.addWidget(visit_group)
        self.main_layout.addWidget(services_group)
        self.main_layout.addWidget(prescriptions_group)
        self.main_layout.addWidget(finance_group)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept) # Just close the dialog
        self.main_layout.addWidget(self.button_box)

    def load_data(self):
        """Load all necessary data for the visit. Returns True if successful."""
        data = load_visit_data(self.visit_id)
        if not data:
            return False

        self.visit_data, self.patient_data, self.services, self.prescriptions = data
        return True

    def populate_services_table(self):
        """Fills the services table with data."""
        self.services_table.setRowCount(len(self.services))
        for row, service in enumerate(self.services):
            self.services_table.setItem(row, 0, QTableWidgetItem(service.get('service_name', 'N/A')))
            self.services_table.setItem(row, 1, QTableWidgetItem(str(service.get('tooth_number', ''))))
            self.services_table.setItem(row, 2, QTableWidgetItem(f"{service.get('price_charged', 0.0):.2f}"))
            self.services_table.setItem(row, 3, QTableWidgetItem(service.get('notes', '')))
        self.services_table.resizeColumnsToContents()
        self.services_table.resizeRowsToContents()

    def populate_prescriptions_table(self):
        """Fills the prescriptions table with data."""
        self.prescriptions_table.setRowCount(len(self.prescriptions))
        for row, prescription in enumerate(self.prescriptions):
            self.prescriptions_table.setItem(row, 0, QTableWidgetItem(prescription.get('medication_name', 'N/A')))
            self.prescriptions_table.setItem(row, 1, QTableWidgetItem(str(prescription.get('quantity', ''))))
            self.prescriptions_table.setItem(row, 2, QTableWidgetItem(f"{prescription.get('price_charged', 0.0):.2f}"))
            self.prescriptions_table.setItem(row, 3, QTableWidgetItem(prescription.get('instructions', '')))
        self.prescriptions_table.resizeColumnsToContents()
        self.prescriptions_table.resizeRowsToContents()

# --- Testing Block ---
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    # Make sure DB is initialized and has a patient and a visit (e.g., Visit ID 1)
    try:
        from database.schema import initialize_database
        from database.data_manager import add_patient, add_visit, add_service, add_medication, add_service_to_visit, add_prescription_to_visit
        initialize_database()
        # Ensure patient 1 exists
        if not get_patient_by_id(1):
            add_patient("Test VisitDetail", "Tester", "Other", 31, "1 Detail St", "555-DETAIL", "Needs details")
        # Ensure visit 1 exists for patient 1
        if not get_visit_by_id(1):
           visit_id_test = add_visit(1, QDate.currentDate().toString("yyyy-MM-dd"), "Initial checkup")
           if visit_id_test == 1:
                # Add dummy service/medication if they don't exist
                if not get_service_by_id(1): add_service("Checkup", "Routine Checkup", 50.0)
                if not get_medication_by_id(1): add_medication("Painkiller", "Generic", 5.0)
                # Add items to the visit
                add_service_to_visit(1, 1, None, 50.0, "Routine")
                add_prescription_to_visit(1, 1, 10, 5.0, "Take as needed")
           else:
               print("Failed to add visit 1 for testing.")

    except Exception as e:
        print(f"Error setting up DB for test: {e}")
        sys.exit(1)

    TEST_VISIT_ID = 1 # Assume visit 1 exists

    app = QApplication(sys.argv)
    visit_data_test = get_visit_by_id(TEST_VISIT_ID)

    if not visit_data_test:
        print(f"Cannot run test: Visit with ID {TEST_VISIT_ID} not found.")
        sys.exit(1)

    print(f"Attempting to view details for Visit ID: {TEST_VISIT_ID}")
    window = VisitDetailWindow(visit_id=TEST_VISIT_ID)
    window.exec()

    print("Visit Detail window closed.")
