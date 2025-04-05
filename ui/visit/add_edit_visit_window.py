import sys
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QPushButton, QMessageBox, QFormLayout, QDialogButtonBox, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QSpinBox,
                             QDoubleSpinBox, QDateEdit, QAbstractItemView, QLineEdit)
from PyQt6.QtCore import pyqtSignal, Qt, QDate
import qtawesome as qta
from pathlib import Path

from database.data_manager import (add_prescription_to_visit, add_service_to_visit, get_medication_by_id, 
                                  get_patient_by_id, get_prescriptions_for_visit, get_service_by_id, 
                                  get_services_for_visit, remove_prescription_from_visit, 
                                  remove_service_from_visit, get_visit_by_id)
from model.visit_manager import load_initial_data, save_visit_details, add_new_visit

class AddEditVisitWindow(QDialog):
    """Dialog for adding a new visit or editing an existing one."""
    visit_saved = pyqtSignal(int)  # Emit patient_id when visit is saved/updated

    def __init__(self, patient_id, visit_id=None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.visit_id = visit_id  # None for adding, existing ID for editing
        self.is_editing = visit_id is not None

        self.patient_data = None
        self.visit_data = None
        self.available_services = {}  # Store name -> id, price
        self.available_medications = {}  # Store name -> id, price

        self.setWindowTitle(f"{'Edit' if self.is_editing else 'Add'} Visit for Patient ID: {self.patient_id}")
        self.setMinimumWidth(750)
        self.setMinimumHeight(650)
        self.setModal(True)

        # --- Load initial data ---
        if not self.load_initial_data():
            QMessageBox.critical(self, "Error", "Could not load necessary data (Patient/Services/Medications). Cannot open window.")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.reject)
            return

        # --- Layouts ---
        self.main_layout = QVBoxLayout(self)

        # --- Top Section: Patient Info ---
        patient_info_layout = QHBoxLayout()
        patient_info_layout.addWidget(QLabel(f"<b>Patient:</b> {self.patient_data.get('name', 'N/A')} (ID: {self.patient_id})"))
        patient_info_layout.addStretch()
        self.main_layout.addLayout(patient_info_layout)

        # --- Visit Details Form ---
        visit_details_group = QGroupBox("Visit Details")
        visit_form_layout = QFormLayout(visit_details_group)
        self.visit_date_input = QDateEdit(QDate.currentDate())
        self.visit_date_input.setCalendarPopup(True)
        self.visit_notes_input = QTextEdit()
        self.visit_notes_input.setPlaceholderText("General notes about the visit...")
        self.visit_notes_input.setFixedHeight(60)
        self.lab_results_input = QTextEdit()
        self.lab_results_input.setPlaceholderText("Lab results or references...")
        self.lab_results_input.setFixedHeight(60)

        visit_form_layout.addRow("Visit Date:", self.visit_date_input)
        visit_form_layout.addRow("Notes:", self.visit_notes_input)
        visit_form_layout.addRow("Lab Results:", self.lab_results_input)
        self.main_layout.addWidget(visit_details_group)

        # --- Services Section ---
        services_group = QGroupBox("Services Performed")
        services_layout = QVBoxLayout(services_group)
        # Add Service Controls
        add_service_layout = QHBoxLayout()
        self.service_combo = QComboBox()
        self.service_combo.addItems(sorted(self.available_services.keys()))
        self.service_combo.currentIndexChanged.connect(self.update_service_price)
        self.service_tooth_input = QLineEdit()
        self.service_tooth_input.setPlaceholderText("Tooth # (opt)")
        self.service_tooth_input.setFixedWidth(80)
        self.service_price_input = QDoubleSpinBox()
        self.service_price_input.setRange(0.0, 99999.99)
        self.service_price_input.setDecimals(2)
        self.service_price_input.setFixedWidth(100)
        self.service_notes_input = QLineEdit()
        self.service_notes_input.setPlaceholderText("Service Notes (opt)")
        self.add_service_button = QPushButton(qta.icon('fa5s.plus'), "Add Service")
        self.add_service_button.clicked.connect(self.add_service_item)
        add_service_layout.addWidget(QLabel("Service:"))
        add_service_layout.addWidget(self.service_combo, 2)
        add_service_layout.addWidget(self.service_tooth_input, 0)
        add_service_layout.addWidget(QLabel("Price:"))
        add_service_layout.addWidget(self.service_price_input, 0)
        add_service_layout.addWidget(self.service_notes_input, 1)
        add_service_layout.addWidget(self.add_service_button, 0)
        services_layout.addLayout(add_service_layout)
        # Services Table
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)  # Added hidden ID and remove button column
        self.services_table.setHorizontalHeaderLabels(["ID", "Service", "Tooth #", "Price", "Notes", "Remove"])
        self.services_table.setColumnHidden(0, True)  # Hide visit_service_id/service_id
        self.services_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Service Name
        self.services_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Notes
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        services_layout.addWidget(self.services_table)
        self.main_layout.addWidget(services_group)

        # --- Prescriptions Section ---
        prescriptions_group = QGroupBox("Prescriptions Issued")
        prescriptions_layout = QVBoxLayout(prescriptions_group)
        # Add Prescription Controls
        add_prescription_layout = QHBoxLayout()
        self.med_combo = QComboBox()
        self.med_combo.addItems(sorted(self.available_medications.keys()))
        self.med_combo.currentIndexChanged.connect(self.update_med_price)
        self.med_qty_input = QSpinBox()
        self.med_qty_input.setRange(1, 999)
        self.med_qty_input.setValue(1)
        self.med_qty_input.setFixedWidth(60)
        self.med_price_input = QDoubleSpinBox()
        self.med_price_input.setRange(0.0, 9999.99)
        self.med_price_input.setDecimals(2)
        self.med_price_input.setFixedWidth(100)
        self.med_instr_input = QLineEdit()
        self.med_instr_input.setPlaceholderText("Instructions (opt)")
        self.add_med_button = QPushButton(qta.icon('fa5s.plus'), "Add Med")
        self.add_med_button.clicked.connect(self.add_prescription_item)
        add_prescription_layout.addWidget(QLabel("Med:"))
        add_prescription_layout.addWidget(self.med_combo, 2)
        add_prescription_layout.addWidget(QLabel("Qty:"))
        add_prescription_layout.addWidget(self.med_qty_input, 0)
        add_prescription_layout.addWidget(QLabel("Price:"))
        add_prescription_layout.addWidget(self.med_price_input, 0)
        add_prescription_layout.addWidget(self.med_instr_input, 1)
        add_prescription_layout.addWidget(self.add_med_button, 0)
        prescriptions_layout.addLayout(add_prescription_layout)
        # Prescriptions Table
        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setColumnCount(6)  # Added hidden ID and remove button column
        self.prescriptions_table.setHorizontalHeaderLabels(["ID", "Medication", "Qty", "Price", "Instructions", "Remove"])
        self.prescriptions_table.setColumnHidden(0, True)  # Hide visit_prescription_id/med_id
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Med Name
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Instructions
        self.prescriptions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.prescriptions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        prescriptions_layout.addWidget(self.prescriptions_table)
        self.main_layout.addWidget(prescriptions_group)

        # --- Payment Section ---
        payment_group = QGroupBox("Payment")
        payment_layout = QFormLayout(payment_group)
        self.total_amount_label = QLabel("0.00")  # Will be updated dynamically
        self.paid_amount_input = QDoubleSpinBox()
        self.paid_amount_input.setRange(0.0, 99999.99)
        self.paid_amount_input.setDecimals(2)
        self.paid_amount_input.setValue(0.0)
        self.due_amount_label = QLabel("0.00")  # Will be updated dynamically
        payment_layout.addRow("Total Amount:", self.total_amount_label)
        payment_layout.addRow("Amount Paid:", self.paid_amount_input)
        payment_layout.addRow("Amount Due:", self.due_amount_label)
        self.paid_amount_input.valueChanged.connect(self.update_due_amount_display)
        self.main_layout.addWidget(payment_group)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

        # --- Populate fields if editing ---
        if self.is_editing:
            self.populate_fields_for_edit()

        # Update prices based on initial combo selections
        self.update_service_price()
        self.update_med_price()
        self.update_financial_summary()  # Initial update

    def load_initial_data(self):
        """Load patient, services, meds, and existing visit data if editing."""
        data = load_initial_data(self.patient_id, self.is_editing, self.visit_id)
        if not data:
            return False

        self.patient_data, self.visit_data, self.available_services, self.available_medications = data
        return True

    def populate_fields_for_edit(self):
        """Fill form fields with data from the existing visit."""
        if not self.visit_data:
            return

        # Visit Details
        visit_date = QDate.fromString(self.visit_data.get('visit_date', ''), "yyyy-MM-dd")
        self.visit_date_input.setDate(visit_date if visit_date.isValid() else QDate.currentDate())
        self.visit_notes_input.setPlainText(self.visit_data.get('notes', ''))
        self.lab_results_input.setPlainText(self.visit_data.get('lab_results', ''))

        # Payment Details
        self.paid_amount_input.setValue(self.visit_data.get('paid_amount', 0.0))
        # Total and Due are updated dynamically

        # Populate Services Table
        visit_services = get_services_for_visit(self.visit_id)
        self.services_table.setRowCount(0)  # Clear existing
        if visit_services:
            for service in visit_services:
                self._add_row_to_table(self.services_table, service, is_service=True)

        # Populate Prescriptions Table
        visit_prescriptions = get_prescriptions_for_visit(self.visit_id)
        self.prescriptions_table.setRowCount(0)  # Clear existing
        if visit_prescriptions:
            for prescription in visit_prescriptions:
                self._add_row_to_table(self.prescriptions_table, prescription, is_service=False)

        self.update_financial_summary()  # Update totals based on loaded items

    def update_service_price(self):
        """Update price input when service selection changes."""
        service_name = self.service_combo.currentText()
        if service_name in self.available_services:
            self.service_price_input.setValue(self.available_services[service_name]['price'])

    def update_med_price(self):
        """Update price input when medication selection changes."""
        med_name = self.med_combo.currentText()
        if med_name in self.available_medications:
            self.med_price_input.setValue(self.available_medications[med_name]['price'])

    def add_service_item(self):
        """Adds the selected service to the services table."""
        service_name = self.service_combo.currentText()
        if not service_name or service_name not in self.available_services:
            QMessageBox.warning(self, "Selection Error", "Please select a valid service.")
            return

        service_id = self.available_services[service_name]['id']
        tooth_str = self.service_tooth_input.text().strip()
        tooth_number = int(tooth_str) if tooth_str.isdigit() else None
        price = self.service_price_input.value()
        notes = self.service_notes_input.text().strip()

        if self.is_editing:
            # Add directly to DB if editing
            visit_service_id = add_service_to_visit(self.visit_id, service_id, tooth_number, price, notes)
            if visit_service_id:
                item_data = {'visit_service_id': visit_service_id, 'service_name': service_name,
                             'tooth_number': tooth_number, 'price_charged': price, 'notes': notes}
                self._add_row_to_table(self.services_table, item_data, is_service=True)
                self.update_financial_summary()  # Update totals immediately
            else:
                QMessageBox.critical(self, "Database Error", "Failed to add service to the visit.")
        else:
            # Add to table only if adding a new visit
            item_data = {'service_id': service_id, 'service_name': service_name,
                         'tooth_number': tooth_number, 'price_charged': price, 'notes': notes}
            self._add_row_to_table(self.services_table, item_data, is_service=True)
            self.update_financial_summary()  # Update totals immediately

    def add_prescription_item(self):
        """Adds the selected prescription to the prescriptions table."""
        med_name = self.med_combo.currentText()
        if not med_name or med_name not in self.available_medications:
            QMessageBox.warning(self, "Selection Error", "Please select a valid medication.")
            return

        med_id = self.available_medications[med_name]['id']
        quantity = self.med_qty_input.value()
        price = self.med_price_input.value()
        instructions = self.med_instr_input.text().strip()

        if self.is_editing:
            # Add directly to DB if editing
            visit_prescription_id = add_prescription_to_visit(self.visit_id, med_id, quantity, price, instructions)
            if visit_prescription_id:
                item_data = {'visit_prescription_id': visit_prescription_id, 'medication_name': med_name,
                             'quantity': quantity, 'price_charged': price, 'instructions': instructions}
                self._add_row_to_table(self.prescriptions_table, item_data, is_service=False)
                self.update_financial_summary()  # Update totals immediately
            else:
                QMessageBox.critical(self, "Database Error", "Failed to add prescription to the visit.")
        else:
            # Add to table only if adding a new visit
            item_data = {'medication_id': med_id, 'medication_name': med_name,
                         'quantity': quantity, 'price_charged': price, 'instructions': instructions}
            self._add_row_to_table(self.prescriptions_table, item_data, is_service=False)
            self.update_financial_summary()  # Update totals immediately

    def _add_row_to_table(self, table, item_data, is_service):
        """Helper to add a row to either table."""
        row_position = table.rowCount()
        table.insertRow(row_position)

        remove_button = QPushButton(qta.icon('fa5s.trash-alt'), "Remove")
        remove_button.setToolTip(f"Remove this {'service' if is_service else 'prescription'}")
        remove_button.setProperty("row", row_position)

        if is_service:
            # Store visit_service_id if editing, or service_id if adding
            item_id = item_data.get('visit_service_id') or item_data.get('service_id')
            name = item_data.get('service_name', 'N/A')
            col2_val = str(item_data.get('tooth_number', ''))
            price = item_data.get('price_charged', 0.0)
            notes = item_data.get('notes', '')
            remove_button.setProperty("item_id", item_data.get('visit_service_id'))  # Store DB ID if exists
            remove_button.clicked.connect(lambda checked, b=remove_button: self.remove_service_item(b))
            table.setItem(row_position, 0, QTableWidgetItem(str(item_id)))  # Hidden ID
            table.setItem(row_position, 1, QTableWidgetItem(name))
            table.setItem(row_position, 2, QTableWidgetItem(col2_val))  # Tooth #
            table.setItem(row_position, 3, QTableWidgetItem(f"{price:.2f}"))
            table.setItem(row_position, 4, QTableWidgetItem(notes))  # Notes
            table.setCellWidget(row_position, 5, remove_button)  # Remove Button Col
        else:
            # Store visit_prescription_id if editing, or medication_id if adding
            item_id = item_data.get('visit_prescription_id') or item_data.get('medication_id')
            name = item_data.get('medication_name', 'N/A')
            col2_val = str(item_data.get('quantity', ''))
            price = item_data.get('price_charged', 0.0)
            notes = item_data.get('instructions', '')
            remove_button.setProperty("item_id", item_data.get('visit_prescription_id'))  # Store DB ID if exists
            remove_button.clicked.connect(lambda checked, b=remove_button: self.remove_prescription_item(b))
            table.setItem(row_position, 0, QTableWidgetItem(str(item_id)))  # Hidden ID
            table.setItem(row_position, 1, QTableWidgetItem(name))
            table.setItem(row_position, 2, QTableWidgetItem(col2_val))  # Quantity
            table.setItem(row_position, 3, QTableWidgetItem(f"{price:.2f}"))
            table.setItem(row_position, 4, QTableWidgetItem(notes))  # Instructions
            table.setCellWidget(row_position, 5, remove_button)  # Remove Button Col

        table.resizeColumnsToContents()

    def remove_service_item(self, button):
        """Removes a service item from the table and DB (if editing)."""
        row_to_remove = button.property("row")
        visit_service_id = button.property("item_id")  # This is the DB ID (None if adding new visit)

        if row_to_remove is None:
            return

        confirm = QMessageBox.question(self, "Confirm Removal",
                                       "Are you sure you want to remove this service item?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            if self.is_editing and visit_service_id:
                success = remove_service_from_visit(visit_service_id)
                if success is True:
                    self.services_table.removeRow(row_to_remove)
                    self.update_row_properties(self.services_table, row_to_remove)
                    self.update_financial_summary()
                elif success is False:
                    QMessageBox.warning(self, "Error", "Could not remove service due to a constraint.")
                else:
                    QMessageBox.critical(self, "Database Error", "Failed to remove service item from database.")
            else:
                self.services_table.removeRow(row_to_remove)
                self.update_row_properties(self.services_table, row_to_remove)
                self.update_financial_summary()

    def remove_prescription_item(self, button):
        """Removes a prescription item from the table and DB (if editing)."""
        row_to_remove = button.property("row")
        visit_prescription_id = button.property("item_id")  # DB ID (None if adding)

        if row_to_remove is None:
            return

        confirm = QMessageBox.question(self, "Confirm Removal",
                                       "Are you sure you want to remove this prescription item?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            if self.is_editing and visit_prescription_id:
                success = remove_prescription_from_visit(visit_prescription_id)
                if success is True:
                    self.prescriptions_table.removeRow(row_to_remove)
                    self.update_row_properties(self.prescriptions_table, row_to_remove)
                    self.update_financial_summary()
                elif success is False:
                    QMessageBox.warning(self, "Error", "Could not remove prescription due to a constraint.")
                else:
                    QMessageBox.critical(self, "Database Error", "Failed to remove prescription item from database.")
            else:
                self.prescriptions_table.removeRow(row_to_remove)
                self.update_row_properties(self.prescriptions_table, row_to_remove)
                self.update_financial_summary()

    def update_row_properties(self, table, removed_row_index):
        """Adjust the 'row' property of buttons in subsequent rows after a removal."""
        for row in range(removed_row_index, table.rowCount()):
            button = table.cellWidget(row, table.columnCount() - 1)  # Last column has button
            if button:
                button.setProperty("row", row)

    def update_financial_summary(self):
        """Updates the total and due amount labels based on current table data."""
        total = 0.0
        for row in range(self.services_table.rowCount()):
            price = float(self.services_table.item(row, 3).text())
            total += price
        for row in range(self.prescriptions_table.rowCount()):
            price = float(self.prescriptions_table.item(row, 3).text())
            total += price

        self.total_amount_label.setText(f"{total:.2f}")
        due = max(0.0, total - self.paid_amount_input.value())
        self.due_amount_label.setText(f"{due:.2f}")

    def update_due_amount_display(self):
        """Updates only the due amount label when 'paid' amount changes."""
        total = float(self.total_amount_label.text())
        paid = self.paid_amount_input.value()
        due = max(0.0, total - paid)
        self.due_amount_label.setText(f"{due:.2f}")

    def accept(self):
        """Save the visit details and items."""
        visit_date = self.visit_date_input.date().toString("yyyy-MM-dd")
        notes = self.visit_notes_input.toPlainText().strip()
        lab_results = self.lab_results_input.toPlainText().strip()
        paid_amount = self.paid_amount_input.value()

        if self.is_editing:
            success = save_visit_details(self.visit_id, visit_date, notes, lab_results, paid_amount)
            if success:
                QMessageBox.information(self, "Success", f"Visit ID {self.visit_id} updated successfully.")
                self.visit_saved.emit(self.patient_id)
                super().accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to update visit details.")
        else:  # Adding a new visit
            new_visit_id = add_new_visit(self.patient_id, visit_date, notes, lab_results,
                                         self.services_table, self.prescriptions_table, paid_amount)
            if new_visit_id:
                QMessageBox.information(self, "Success", f"New visit added successfully.")
                self.visit_saved.emit(self.patient_id)
                super().accept()
            else:
                QMessageBox.warning(self, "Partial Success", f"New visit created, but some items may have failed to save.")

# --- Testing Block ---
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    try:
        from database.schema import initialize_database
        from database.data_manager import add_patient, add_service, add_medication, get_visit_by_id, add_visit
        initialize_database()
        if not get_patient_by_id(4):
            add_patient("Test AddVisit", "Tester", "Female", 40, "1 Add St", "555-ADD", "Needs adding visit")
        if not get_service_by_id(1):
            add_service("cleaning", "Teeth Cleaning", 50.0)
        if not get_medication_by_id(1):
            add_medication("abc", "Antibiotic", 20.0)
    except Exception as e:
        print(f"Error setting up DB for test: {e}")
        sys.exit(1)

    TEST_PATIENT_ID = 4
    TEST_VISIT_ID_EDIT = None  # Set to None for new visit, or an existing ID for editing

    app = QApplication(sys.argv)

    if TEST_VISIT_ID_EDIT:
        print(f"\n--- Testing EDIT Visit ID: {TEST_VISIT_ID_EDIT} for Patient ID: {TEST_PATIENT_ID} ---")
        window = AddEditVisitWindow(patient_id=TEST_PATIENT_ID, visit_id=TEST_VISIT_ID_EDIT)
    else:
        print(f"\n--- Testing ADD Visit for Patient ID: {TEST_PATIENT_ID} ---")
        window = AddEditVisitWindow(patient_id=TEST_PATIENT_ID)

    def on_visit_saved_test(p_id):
        print(f"Test: visit_saved signal received for Patient ID: {p_id}!")

    window.visit_saved.connect(on_visit_saved_test)

    result = window.exec()

    if result == QDialog.DialogCode.Accepted:
        print("Add/Edit Visit window accepted (Save successful).")
    else:
        print("Add/Edit Visit window rejected (Cancel pressed or error).")