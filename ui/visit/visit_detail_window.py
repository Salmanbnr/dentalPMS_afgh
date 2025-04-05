import sys
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QFormLayout, QDialogButtonBox, QGroupBox,
                             QPushButton, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QLineEdit, QAbstractItemView)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta

from database.data_manager import (get_patient_by_id, get_service_by_id, get_visit_by_id, get_services_for_visit, 
                                  get_prescriptions_for_visit, update_visit_details, 
                                  update_visit_payment, add_service_to_visit, remove_service_from_visit, 
                                  add_prescription_to_visit, remove_prescription_from_visit)
from model.visit_manager import load_visit_data, get_all_services, get_all_medications

class VisitDetailWindow(QDialog):
    """Dialog to display and edit the details of a specific visit."""

    def __init__(self, visit_id, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id
        self.visit_data = None
        self.patient_data = None
        self.services = []
        self.prescriptions = []
        self.is_editing = False

        self.setWindowTitle(f"Visit Details (ID: {self.visit_id})")
        self.setMinimumWidth(750)
        self.setMinimumHeight(650)
        self.setModal(True)

        # --- Layouts ---
        self.main_layout = QVBoxLayout(self)

        # --- Load Data ---
        if not self.load_data():
            QMessageBox.critical(self, "Error", f"Could not load data for visit ID: {self.visit_id}. Cannot open details.")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.reject)
            return

        # --- Widgets ---
        # Patient Info Group (Read-only)
        patient_group = QGroupBox("Patient Information")
        patient_layout = QFormLayout(patient_group)
        self.patient_name_label = QLabel(self.patient_data.get('name', 'N/A'))
        self.patient_id_label = QLabel(str(self.patient_data.get('patient_id', 'N/A')))
        patient_layout.addRow("Patient Name:", self.patient_name_label)
        patient_layout.addRow("Patient ID:", self.patient_id_label)
        self.main_layout.addWidget(patient_group)

        # Visit Info Group
        visit_group = QGroupBox("Visit Information")
        visit_form_layout = QFormLayout(visit_group)
        self.visit_date_input = QDateEdit(QDate.currentDate())
        self.visit_date_input.setCalendarPopup(True)
        self.visit_date_input.setReadOnly(True)
        self.visit_notes_input = QTextEdit()
        self.visit_notes_input.setReadOnly(True)
        self.visit_notes_input.setFixedHeight(60)
        self.lab_results_input = QTextEdit()
        self.lab_results_input.setReadOnly(True)
        self.lab_results_input.setFixedHeight(60)

        visit_date = QDate.fromString(self.visit_data.get('visit_date', ''), "yyyy-MM-dd")
        self.visit_date_input.setDate(visit_date if visit_date.isValid() else QDate.currentDate())
        self.visit_notes_input.setPlainText(self.visit_data.get('notes', ''))
        self.lab_results_input.setPlainText(self.visit_data.get('lab_results', ''))

        visit_form_layout.addRow("Visit Details:", QLabel(f"Visit #{self.visit_data.get('visit_number', 'N/A')} on {self.visit_data.get('visit_date', 'N/A')}"))
        visit_form_layout.addRow("Visit Date:", self.visit_date_input)
        visit_form_layout.addRow("Notes:", self.visit_notes_input)
        visit_form_layout.addRow("Lab Results:", self.lab_results_input)
        self.main_layout.addWidget(visit_group)

        # Services Section
        services_group = QGroupBox("Services Performed")
        services_layout = QVBoxLayout(services_group)
        # Add Service Controls wrapped in a QWidget
        self.add_service_widget = QWidget()
        self.add_service_layout = QHBoxLayout(self.add_service_widget)
        self.service_combo = QComboBox()
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
        self.add_service_layout.addWidget(QLabel("Service:"))
        self.add_service_layout.addWidget(self.service_combo, 2)
        self.add_service_layout.addWidget(self.service_tooth_input, 0)
        self.add_service_layout.addWidget(QLabel("Price:"))
        self.add_service_layout.addWidget(self.service_price_input, 0)
        self.add_service_layout.addWidget(self.service_notes_input, 1)
        self.add_service_layout.addWidget(self.add_service_button, 0)
        services_layout.addWidget(self.add_service_widget)
        self.add_service_widget.setVisible(False)  # Hidden until edit mode
        # Services Table
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels(["ID", "Service", "Tooth #", "Price", "Notes", ""])
        self.services_table.setColumnHidden(0, True)
        self.services_table.setColumnHidden(5, True)
        self.services_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.services_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.populate_services_table()
        services_layout.addWidget(self.services_table)
        self.main_layout.addWidget(services_group)

        # Prescriptions Section
        prescriptions_group = QGroupBox("Prescriptions Issued")
        prescriptions_layout = QVBoxLayout(prescriptions_group)
        # Add Prescription Controls wrapped in a QWidget
        self.add_prescription_widget = QWidget()
        self.add_prescription_layout = QHBoxLayout(self.add_prescription_widget)
        self.med_combo = QComboBox()
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
        self.add_prescription_layout.addWidget(QLabel("Med:"))
        self.add_prescription_layout.addWidget(self.med_combo, 2)
        self.add_prescription_layout.addWidget(QLabel("Qty:"))
        self.add_prescription_layout.addWidget(self.med_qty_input, 0)
        self.add_prescription_layout.addWidget(QLabel("Price:"))
        self.add_prescription_layout.addWidget(self.med_price_input, 0)
        self.add_prescription_layout.addWidget(self.med_instr_input, 1)
        self.add_prescription_layout.addWidget(self.add_med_button, 0)
        prescriptions_layout.addWidget(self.add_prescription_widget)
        self.add_prescription_widget.setVisible(False)  # Hidden until edit mode
        # Prescriptions Table
        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setColumnCount(6)
        self.prescriptions_table.setHorizontalHeaderLabels(["ID", "Medication", "Qty", "Price", "Instructions", ""])
        self.prescriptions_table.setColumnHidden(0, True)
        self.prescriptions_table.setColumnHidden(5, True)
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.prescriptions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.populate_prescriptions_table()
        prescriptions_layout.addWidget(self.prescriptions_table)
        self.main_layout.addWidget(prescriptions_group)

        # Financial Summary Group
        finance_group = QGroupBox("Financial Summary")
        finance_layout = QFormLayout(finance_group)
        self.total_amount_label = QLabel(f"{self.visit_data.get('total_amount', 0.0):.2f}")
        self.paid_amount_input = QDoubleSpinBox()
        self.paid_amount_input.setRange(0.0, 99999.99)
        self.paid_amount_input.setDecimals(2)
        self.paid_amount_input.setValue(self.visit_data.get('paid_amount', 0.0))
        self.paid_amount_input.setReadOnly(True)
        self.due_amount_label = QLabel(f"{self.visit_data.get('due_amount', 0.0):.2f}")
        finance_layout.addRow("Total Amount:", self.total_amount_label)
        finance_layout.addRow("Amount Paid:", self.paid_amount_input)
        finance_layout.addRow("Amount Due:", self.due_amount_label)
        self.main_layout.addWidget(finance_group)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.edit_button = QPushButton(qta.icon('fa5s.edit'), "Edit")
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        self.button_box.addButton(self.edit_button, QDialogButtonBox.ButtonRole.ActionRole)
        self.button_box.accepted.connect(self.accept)
        self.main_layout.addWidget(self.button_box)

        # Load available services and medications for editing
        services = get_all_services(active_only=True) or []
        self.available_services = {s['name']: {'id': s['service_id'], 'price': s['default_price']} 
                                for s in services}
        medications = get_all_medications(active_only=True) or []
        self.available_medications = {m['name']: {'id': m['medication_id'], 'price': m.get('default_price', 0.0)} 
                                   for m in medications}
        self.service_combo.addItems(sorted(self.available_services.keys()))
        self.med_combo.addItems(sorted(self.available_medications.keys()))

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
            self.services_table.setItem(row, 0, QTableWidgetItem(str(service.get('visit_service_id', service.get('service_id', '')))))
            self.services_table.setItem(row, 1, QTableWidgetItem(service.get('service_name', 'N/A')))
            self.services_table.setItem(row, 2, QTableWidgetItem(str(service.get('tooth_number', ''))))
            self.services_table.setItem(row, 3, QTableWidgetItem(f"{service.get('price_charged', 0.0):.2f}"))
            self.services_table.setItem(row, 4, QTableWidgetItem(service.get('notes', '')))
            self.services_table.setItem(row, 5, QTableWidgetItem('existing'))
            remove_button = QPushButton(qta.icon('fa5s.trash-alt'), "")
            remove_button.setToolTip("Remove this service")
            remove_button.setProperty("row", row)
            remove_button.setProperty("is_service", True)
            remove_button.clicked.connect(self.remove_item)
            self.services_table.setCellWidget(row, 6, remove_button)
        self.services_table.resizeColumnsToContents()
        self.services_table.resizeRowsToContents()

    def populate_prescriptions_table(self):
        """Fills the prescriptions table with data."""
        self.prescriptions_table.setRowCount(len(self.prescriptions))
        for row, prescription in enumerate(self.prescriptions):
            self.prescriptions_table.setItem(row, 0, QTableWidgetItem(str(prescription.get('visit_prescription_id', prescription.get('medication_id', '')))))
            self.prescriptions_table.setItem(row, 1, QTableWidgetItem(prescription.get('medication_name', 'N/A')))
            self.prescriptions_table.setItem(row, 2, QTableWidgetItem(str(prescription.get('quantity', ''))))
            self.prescriptions_table.setItem(row, 3, QTableWidgetItem(f"{prescription.get('price_charged', 0.0):.2f}"))
            self.prescriptions_table.setItem(row, 4, QTableWidgetItem(prescription.get('instructions', '')))
            self.prescriptions_table.setItem(row, 5, QTableWidgetItem('existing'))
            remove_button = QPushButton(qta.icon('fa5s.trash-alt'), "")
            remove_button.setToolTip("Remove this prescription")
            remove_button.setProperty("row", row)
            remove_button.setProperty("is_service", False)
            remove_button.clicked.connect(self.remove_item)
            self.prescriptions_table.setCellWidget(row, 6, remove_button)
        self.prescriptions_table.resizeColumnsToContents()
        self.prescriptions_table.resizeRowsToContents()

    def toggle_edit_mode(self):
        """Toggle between view and edit modes."""
        self.is_editing = not self.is_editing
        if self.is_editing:
            # Enable editing
            self.visit_date_input.setReadOnly(False)
            self.visit_notes_input.setReadOnly(False)
            self.lab_results_input.setReadOnly(False)
            self.paid_amount_input.setReadOnly(False)
            self.add_service_widget.setVisible(True)
            self.add_prescription_widget.setVisible(True)
            self.edit_button.setText("Cancel Edit")
            self.button_box.removeButton(self.edit_button)
            self.button_box.clear()
            save_button = self.button_box.addButton("Save", QDialogButtonBox.ButtonRole.AcceptRole)
            cancel_button = self.button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
            save_button.clicked.connect(self.save_changes)
            cancel_button.clicked.connect(self.cancel_edit)
            self.button_box.accepted.disconnect()
            self.button_box.rejected.connect(self.reject)
        else:
            # Revert to view mode
            self.visit_date_input.setReadOnly(True)
            self.visit_notes_input.setReadOnly(True)
            self.lab_results_input.setReadOnly(True)
            self.paid_amount_input.setReadOnly(True)
            self.add_service_widget.setVisible(False)
            self.add_prescription_widget.setVisible(False)
            self.edit_button.setText("Edit")
            self.button_box.clear()
            self.button_box.addButton(self.edit_button, QDialogButtonBox.ButtonRole.ActionRole)
            self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.disconnect()
            self.load_data()  # Reload data to revert changes
            self.populate_services_table()
            self.populate_prescriptions_table()
            self.update_financial_summary()

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

        item_data = {'service_id': service_id, 'service_name': service_name,
                     'tooth_number': tooth_number, 'price_charged': price, 'notes': notes}
        self._add_row_to_table(self.services_table, item_data, True, True)
        self.update_financial_summary()

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

        item_data = {'medication_id': med_id, 'medication_name': med_name,
                     'quantity': quantity, 'price_charged': price, 'instructions': instructions}
        self._add_row_to_table(self.prescriptions_table, item_data, False, True)
        self.update_financial_summary()

    def _add_row_to_table(self, table, item_data, is_service, is_new):
        """Helper to add a row to either table."""
        row_position = table.rowCount()
        table.insertRow(row_position)

        item_id = item_data.get('visit_service_id', item_data.get('service_id', 
                     item_data.get('visit_prescription_id', item_data.get('medication_id', ''))))
        name = item_data.get('service_name', item_data.get('medication_name', 'N/A'))
        col2_val = str(item_data.get('tooth_number', item_data.get('quantity', '')))
        price = item_data.get('price_charged', 0.0)
        notes = item_data.get('notes', item_data.get('instructions', ''))

        table.setItem(row_position, 0, QTableWidgetItem(str(item_id)))
        table.setItem(row_position, 5, QTableWidgetItem('new' if is_new else 'existing'))

        if is_service:
            table.setItem(row_position, 1, QTableWidgetItem(name))
            table.setItem(row_position, 2, QTableWidgetItem(col2_val))
            table.setItem(row_position, 3, QTableWidgetItem(f"{price:.2f}"))
            table.setItem(row_position, 4, QTableWidgetItem(notes))
        else:
            table.setItem(row_position, 1, QTableWidgetItem(name))
            table.setItem(row_position, 2, QTableWidgetItem(col2_val))
            table.setItem(row_position, 3, QTableWidgetItem(f"{price:.2f}"))
            table.setItem(row_position, 4, QTableWidgetItem(notes))

        remove_button = QPushButton(qta.icon('fa5s.trash-alt'), "")
        remove_button.setToolTip(f"Remove this {'service' if is_service else 'prescription'}")
        remove_button.setProperty("row", row_position)
        remove_button.setProperty("is_service", is_service)
        remove_button.clicked.connect(self.remove_item)
        table.setCellWidget(row_position, 6, remove_button)

        table.resizeColumnsToContents()

    def remove_item(self, button):
        """Removes an item (service or prescription) from the table."""
        row_to_remove = button.property("row")
        is_service = button.property("is_service")

        if row_to_remove is None:
            return

        table = self.services_table if is_service else self.prescriptions_table
        item_id = int(table.item(row_to_remove, 0).text())
        item_type = table.item(row_to_remove, 5).text()

        confirm = QMessageBox.question(self, "Confirm Removal",
                                      "Are you sure you want to remove this item?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            if item_type == 'existing':
                if is_service:
                    success = remove_service_from_visit(item_id)
                else:
                    success = remove_prescription_from_visit(item_id)
                if success is not True:
                    QMessageBox.critical(self, "Database Error", "Failed to remove item from database.")
                    return
            table.removeRow(row_to_remove)
            self.update_row_properties(table, row_to_remove)
            self.update_financial_summary()

    def update_row_properties(self, table, removed_row_index):
        """Adjust the 'row' property of buttons in subsequent rows after a removal."""
        for row in range(removed_row_index, table.rowCount()):
            button = table.cellWidget(row, 6)
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

    def save_changes(self):
        """Save the edited visit details and items."""
        visit_date = self.visit_date_input.date().toString("yyyy-MM-dd")
        notes = self.visit_notes_input.toPlainText().strip()
        lab_results = self.lab_results_input.toPlainText().strip()
        paid_amount = self.paid_amount_input.value()

        success = update_visit_details(self.visit_id, visit_date, notes, lab_results)
        if not success:
            QMessageBox.critical(self, "Error", "Failed to update visit details.")
            return

        # Handle new services
        for row in range(self.services_table.rowCount()):
            item_id = int(self.services_table.item(row, 0).text())
            item_type = self.services_table.item(row, 5).text()
            if item_type == 'new':
                service_name = self.services_table.item(row, 1).text()
                tooth_str = self.services_table.item(row, 2).text()
                tooth_number = int(tooth_str) if tooth_str.isdigit() else None
                price = float(self.services_table.item(row, 3).text())
                notes = self.services_table.item(row, 4).text()
                service_id = self.available_services.get(service_name, {}).get('id')
                if service_id:
                    add_service_to_visit(self.visit_id, service_id, tooth_number, price, notes)

        # Handle new prescriptions
        for row in range(self.prescriptions_table.rowCount()):
            item_id = int(self.prescriptions_table.item(row, 0).text())
            item_type = self.prescriptions_table.item(row, 5).text()
            if item_type == 'new':
                med_name = self.prescriptions_table.item(row, 1).text()
                qty = int(self.prescriptions_table.item(row, 2).text())
                price = float(self.prescriptions_table.item(row, 3).text())
                instructions = self.prescriptions_table.item(row, 4).text()
                med_id = self.available_medications.get(med_name, {}).get('id')
                if med_id:
                    add_prescription_to_visit(self.visit_id, med_id, qty, price, instructions)

        success_payment = update_visit_payment(self.visit_id, paid_amount)
        if not success_payment:
            QMessageBox.critical(self, "Error", "Failed to update payment details.")
            return

        QMessageBox.information(self, "Success", f"Visit ID {self.visit_id} updated successfully.")
        self.toggle_edit_mode()  # Return to view mode

    def cancel_edit(self):
        """Cancel editing and revert to view mode."""
        self.toggle_edit_mode()

# --- Testing Block ---
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    try:
        from database.schema import initialize_database
        from database.data_manager import add_patient, add_visit, add_service, add_medication, add_service_to_visit, add_prescription_to_visit
        initialize_database()
        if not get_patient_by_id(4):
            add_patient("Test VisitDetail", "Tester", "Other", 31, "1 Detail St", "555-DETAIL", "Needs details")
        if not get_visit_by_id(9):
            visit_id_test = add_visit(4, "2023-04-05", "tffhfh", "tffhfh")
            if visit_id_test == 9:
                if not get_service_by_id(1):
                    add_service("cleaning", "Teeth Cleaning", 50.0)
                add_service_to_visit(9, 1, None, 50.0, "")
    except Exception as e:
        print(f"Error setting up DB for test: {e}")
        sys.exit(1)

    TEST_VISIT_ID = 9
    app = QApplication(sys.argv)
    window = VisitDetailWindow(visit_id=TEST_VISIT_ID)
    window.exec()