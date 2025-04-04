import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QPushButton, QMessageBox, QFormLayout, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QSpinBox,
                             QDoubleSpinBox, QDateEdit, QAbstractItemView, QLineEdit, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QDate
import qtawesome as qta
from pathlib import Path

from database.data_manager import (add_prescription_to_visit, add_service_to_visit, get_medication_by_id, 
                                  get_patient_by_id, get_prescriptions_for_visit, get_service_by_id, 
                                  get_services_for_visit, remove_prescription_from_visit, 
                                  remove_service_from_visit, get_visit_by_id)
from model.visit_manager import load_initial_data, save_visit_details, add_new_visit

class AddEditVisitWindow(QWidget):
    """Widget for adding a new visit or editing an existing one with enhanced UI/UX."""

    visit_saved = pyqtSignal(int)
    cancelled = pyqtSignal()

    def __init__(self, patient_id, visit_id=None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.visit_id = visit_id
        self.is_editing = visit_id is not None

        self.patient_data = None
        self.visit_data = None
        self.available_services = {}
        self.available_medications = {}

        # Load initial data first
        if not self.load_initial_data():
            QMessageBox.critical(self, "Error", "Could not load necessary data.")
            return

        # Set up modern styling
        self.setStyleSheet("""
            QWidget {
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                background-color: #f5f6fa;
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
                left: 10px;
                padding: 0 5px 0 5px;
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QTextEdit, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                gridline-color: #eee;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QLabel {
                padding: 5px;
                font-weight: bold;
                color: #2c3e50;
            }
            QScrollArea {
                border: none;
                background-color: #f5f6fa;
            }
        """)

        # Main layout with scroll area
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Scrollable content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)

        # Scroll area setup
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

        # Patient Info
        patient_info_layout = QHBoxLayout()
        patient_info_layout.addWidget(QLabel(f"<b>Patient:</b> {self.patient_data.get('name', 'Unknown')} (ID: {self.patient_id})"))
        patient_info_layout.addStretch()
        self.content_layout.addLayout(patient_info_layout)

        # Visit Details
        visit_details_group = QGroupBox("Visit Details")
        visit_form_layout = QFormLayout(visit_details_group)
        visit_form_layout.setSpacing(15)

        self.visit_date_input = QDateEdit(QDate.currentDate())
        self.visit_date_input.setCalendarPopup(True)
        self.visit_notes_input = QTextEdit()
        self.visit_notes_input.setPlaceholderText("Enter general notes about the visit...")
        self.visit_notes_input.setMinimumHeight(120)
        self.lab_results_input = QTextEdit()
        self.lab_results_input.setPlaceholderText("Enter lab results or references...")
        self.lab_results_input.setMinimumHeight(120)

        visit_form_layout.addRow("Visit Date:", self.visit_date_input)
        visit_form_layout.addRow("Notes:", self.visit_notes_input)
        visit_form_layout.addRow("Lab Results:", self.lab_results_input)
        self.content_layout.addWidget(visit_details_group)

        # Services
        services_group = QGroupBox("Services Performed")
        services_layout = QVBoxLayout(services_group)

        add_service_layout = QHBoxLayout()
        add_service_layout.setSpacing(10)

        self.service_combo = QComboBox()
        self.service_combo.addItems(sorted(self.available_services.keys()))
        self.service_combo.currentIndexChanged.connect(self.update_service_price)

        self.service_tooth_input = QLineEdit()
        self.service_tooth_input.setPlaceholderText("Tooth # (optional)")
        self.service_tooth_input.setFixedWidth(100)

        self.service_price_input = QDoubleSpinBox()
        self.service_price_input.setRange(0.0, 99999.99)
        self.service_price_input.setDecimals(2)
        self.service_price_input.setFixedWidth(120)

        self.service_notes_input = QTextEdit()  # Changed to QTextEdit for larger field
        self.service_notes_input.setPlaceholderText("Enter service notes (optional)...")
        self.service_notes_input.setMinimumHeight(80)

        self.add_service_button = QPushButton(qta.icon('fa5s.plus-circle', color='white'), "Add Service")
        self.add_service_button.clicked.connect(self.add_service_item)

        add_service_layout.addWidget(QLabel("Service:"))
        add_service_layout.addWidget(self.service_combo, 2)
        add_service_layout.addWidget(QLabel("Tooth #:"))
        add_service_layout.addWidget(self.service_tooth_input)
        add_service_layout.addWidget(QLabel("Price:"))
        add_service_layout.addWidget(self.service_price_input)
        add_service_layout.addWidget(QLabel("Notes:"))
        add_service_layout.addWidget(self.service_notes_input)
        add_service_layout.addWidget(self.add_service_button)

        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels(["ID", "Service", "Tooth #", "Price", "Notes", "Action"])
        self.services_table.setColumnHidden(0, True)
        self.services_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.services_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.services_table.setMinimumHeight(200)  # Vertically larger table
        # Alternative dynamic resizing (uncomment to use instead of fixed height):
        # self.services_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.services_table.resizeRowsToContents()

        services_layout.addLayout(add_service_layout)
        services_layout.addWidget(self.services_table)
        self.content_layout.addWidget(services_group)

        # Prescriptions
        prescriptions_group = QGroupBox("Prescriptions Issued")
        prescriptions_layout = QVBoxLayout(prescriptions_group)

        add_prescription_layout = QHBoxLayout()
        add_prescription_layout.setSpacing(10)

        self.med_combo = QComboBox()
        self.med_combo.addItems(sorted(self.available_medications.keys()))
        self.med_combo.currentIndexChanged.connect(self.update_med_price)

        self.med_qty_input = QSpinBox()
        self.med_qty_input.setRange(1, 999)
        self.med_qty_input.setValue(1)
        self.med_qty_input.setFixedWidth(80)

        self.med_price_input = QDoubleSpinBox()
        self.med_price_input.setRange(0.0, 9999.99)
        self.med_price_input.setDecimals(2)
        self.med_price_input.setFixedWidth(120)

        self.med_instr_input = QTextEdit()
        self.med_instr_input.setPlaceholderText("Enter instructions (optional)...")
        self.med_instr_input.setMinimumHeight(80)

        self.add_med_button = QPushButton(qta.icon('fa5s.plus-circle', color='white'), "Add Medication")
        self.add_med_button.clicked.connect(self.add_prescription_item)

        add_prescription_layout.addWidget(QLabel("Medication:"))
        add_prescription_layout.addWidget(self.med_combo, 2)
        add_prescription_layout.addWidget(QLabel("Qty:"))
        add_prescription_layout.addWidget(self.med_qty_input)
        add_prescription_layout.addWidget(QLabel("Price:"))
        add_prescription_layout.addWidget(self.med_price_input)
        add_prescription_layout.addWidget(QLabel("Instructions:"))
        add_prescription_layout.addWidget(self.med_instr_input)
        add_prescription_layout.addWidget(self.add_med_button)

        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setColumnCount(6)
        self.prescriptions_table.setHorizontalHeaderLabels(["ID", "Medication", "Qty", "Price", "Instructions", "Action"])
        self.prescriptions_table.setColumnHidden(0, True)
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.prescriptions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.prescriptions_table.setMinimumHeight(200)  # Vertically larger table
        # Alternative dynamic resizing (uncomment to use instead of fixed height):
        # self.prescriptions_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.prescriptions_table.resizeRowsToContents()

        prescriptions_layout.addLayout(add_prescription_layout)
        prescriptions_layout.addWidget(self.prescriptions_table)
        self.content_layout.addWidget(prescriptions_group)

        # Payment
        payment_group = QGroupBox("Payment Summary")
        payment_layout = QFormLayout(payment_group)
        payment_layout.setSpacing(15)

        self.total_amount_label = QLabel("0.00")
        self.paid_amount_input = QDoubleSpinBox()
        self.paid_amount_input.setRange(0.0, 99999.99)
        self.paid_amount_input.setDecimals(2)
        self.paid_amount_input.setValue(0.0)
        self.due_amount_label = QLabel("0.00")

        payment_layout.addRow("Total Amount:", self.total_amount_label)
        payment_layout.addRow("Amount Paid:", self.paid_amount_input)
        payment_layout.addRow("Amount Due:", self.due_amount_label)
        self.paid_amount_input.valueChanged.connect(self.update_due_amount_display)
        self.content_layout.addWidget(payment_group)

        # Action Buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(15)
        action_layout.addStretch()

        self.save_button = QPushButton(qta.icon('fa5s.save', color='white'), "Save Visit")
        self.save_button.clicked.connect(self.save_visit)

        self.cancel_button = QPushButton(qta.icon('fa5s.times-circle', color='white'), "Cancel")
        self.cancel_button.clicked.connect(self.cancel)

        action_layout.addWidget(self.save_button)
        action_layout.addWidget(self.cancel_button)
        self.content_layout.addLayout(action_layout)

        # Ensure initial population if editing
        if self.is_editing:
            self.populate_fields_for_edit()

        self.update_service_price()
        self.update_med_price()
        self.update_financial_summary()

    def load_initial_data(self):
        data = load_initial_data(self.patient_id, self.is_editing, self.visit_id)
        if not data:
            return False
        self.patient_data, self.visit_data, self.available_services, self.available_medications = data
        return True

    def populate_fields_for_edit(self):
        if not self.visit_data:
            return

        visit_date = QDate.fromString(self.visit_data.get('visit_date', ''), "yyyy-MM-dd")
        self.visit_date_input.setDate(visit_date if visit_date.isValid() else QDate.currentDate())
        self.visit_notes_input.setPlainText(self.visit_data.get('notes', ''))
        self.lab_results_input.setPlainText(self.visit_data.get('lab_results', ''))

        self.paid_amount_input.setValue(self.visit_data.get('paid_amount', 0.0))

        visit_services = get_services_for_visit(self.visit_id)
        self.services_table.setRowCount(0)
        if visit_services:
            for service in visit_services:
                self._add_row_to_table(self.services_table, service, True)

        visit_prescriptions = get_prescriptions_for_visit(self.visit_id)
        self.prescriptions_table.setRowCount(0)
        if visit_prescriptions:
            for prescription in visit_prescriptions:
                self._add_row_to_table(self.prescriptions_table, prescription, False)

        self.update_financial_summary()

    def update_service_price(self):
        service_name = self.service_combo.currentText()
        if service_name in self.available_services:
            self.service_price_input.setValue(self.available_services[service_name]['price'])

    def update_med_price(self):
        med_name = self.med_combo.currentText()
        if med_name in self.available_medications:
            self.med_price_input.setValue(self.available_medications[med_name]['price'])

    def add_service_item(self):
        service_name = self.service_combo.currentText()
        if not service_name or service_name not in self.available_services:
            QMessageBox.warning(self, "Selection Error", "Please select a valid service.")
            return

        service_id = self.available_services[service_name]['id']
        tooth_str = self.service_tooth_input.text().strip()
        tooth_number = int(tooth_str) if tooth_str.isdigit() else None
        price = self.service_price_input.value()
        notes = self.service_notes_input.toPlainText().strip()

        if self.is_editing:
            visit_service_id = add_service_to_visit(self.visit_id, service_id, tooth_number, price, notes)
            if visit_service_id:
                item_data = {'visit_service_id': visit_service_id, 'service_name': service_name, 'tooth_number': tooth_number, 'price_charged': price, 'notes': notes}
                self._add_row_to_table(self.services_table, item_data, True)
                self.update_financial_summary()
            else:
                QMessageBox.critical(self, "Database Error", "Failed to add service.")
        else:
            item_data = {'service_id': service_id, 'service_name': service_name, 'tooth_number': tooth_number, 'price_charged': price, 'notes': notes}
            self._add_row_to_table(self.services_table, item_data, True)
            self.update_financial_summary()

    def add_prescription_item(self):
        med_name = self.med_combo.currentText()
        if not med_name or med_name not in self.available_medications:
            QMessageBox.warning(self, "Selection Error", "Please select a valid medication.")
            return

        med_id = self.available_medications[med_name]['id']
        quantity = self.med_qty_input.value()
        price = self.med_price_input.value()
        instructions = self.med_instr_input.toPlainText().strip()

        if self.is_editing:
            visit_prescription_id = add_prescription_to_visit(self.visit_id, med_id, quantity, price, instructions)
            if visit_prescription_id:
                item_data = {'visit_prescription_id': visit_prescription_id, 'medication_name': med_name, 'quantity': quantity, 'price_charged': price, 'instructions': instructions}
                self._add_row_to_table(self.prescriptions_table, item_data, False)
                self.update_financial_summary()
            else:
                QMessageBox.critical(self, "Database Error", "Failed to add prescription.")
        else:
            item_data = {'medication_id': med_id, 'medication_name': med_name, 'quantity': quantity, 'price_charged': price, 'instructions': instructions}
            self._add_row_to_table(self.prescriptions_table, item_data, False)
            self.update_financial_summary()

    def _add_row_to_table(self, table, item_data, is_service):
        row = table.rowCount()
        table.insertRow(row)

        remove_button = QPushButton(qta.icon('fa5s.trash-alt', color='red'), "")
        remove_button.setToolTip(f"Remove this {'service' if is_service else 'prescription'}")
        remove_button.setProperty("row", row)
        remove_button.setStyleSheet("QPushButton { background: transparent; border: none; }")

        if is_service:
            item_id = item_data.get('visit_service_id') or item_data.get('service_id')
            name = item_data.get('service_name', 'N/A')
            tooth = str(item_data.get('tooth_number', ''))
            price = item_data.get('price_charged', 0.0)
            notes = item_data.get('notes', '')

            remove_button.setProperty("item_id", item_data.get('visit_service_id'))
            remove_button.clicked.connect(lambda checked, b=remove_button: self.remove_service_item(b))

            table.setItem(row, 0, QTableWidgetItem(str(item_id)))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 2, QTableWidgetItem(tooth))
            table.setItem(row, 3, QTableWidgetItem(f"AFN {price:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(notes))
            table.setCellWidget(row, 5, remove_button)
        else:
            item_id = item_data.get('visit_prescription_id') or item_data.get('medication_id')
            name = item_data.get('medication_name', 'N/A')
            qty = str(item_data.get('quantity', ''))
            price = item_data.get('price_charged', 0.0)
            instructions = item_data.get('instructions', '')

            remove_button.setProperty("item_id", item_data.get('visit_prescription_id'))
            remove_button.clicked.connect(lambda checked, b=remove_button: self.remove_prescription_item(b))

            table.setItem(row, 0, QTableWidgetItem(str(item_id)))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 2, QTableWidgetItem(qty))
            table.setItem(row, 3, QTableWidgetItem(f"AFN {price:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(instructions))
            table.setCellWidget(row, 5, remove_button)

        table.resizeColumnsToContents()
        # Uncomment for dynamic resizing:
        # table.resizeRowsToContents()
        # table.setFixedHeight(table.verticalHeader().length() + table.horizontalHeader().height())

    def remove_service_item(self, button):
        row = button.property("row")
        visit_service_id = button.property("item_id")

        if row is None:
            return

        if QMessageBox.question(self, "Confirm", "Remove this service?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.is_editing and visit_service_id:
                if remove_service_from_visit(visit_service_id):
                    self.services_table.removeRow(row)
                    self.update_row_properties(self.services_table, row)
                    self.update_financial_summary()
                else:
                    QMessageBox.critical(self, "Error", "Failed to remove service.")
            else:
                self.services_table.removeRow(row)
                self.update_row_properties(self.services_table, row)
                self.update_financial_summary()

    def remove_prescription_item(self, button):
        row = button.property("row")
        visit_prescription_id = button.property("item_id")

        if row is None:
            return

        if QMessageBox.question(self, "Confirm", "Remove this prescription?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.is_editing and visit_prescription_id:
                if remove_prescription_from_visit(visit_prescription_id):
                    self.prescriptions_table.removeRow(row)
                    self.update_row_properties(self.prescriptions_table, row)
                    self.update_financial_summary()
                else:
                    QMessageBox.critical(self, "Error", "Failed to remove prescription.")
            else:
                self.prescriptions_table.removeRow(row)
                self.update_row_properties(self.prescriptions_table, row)
                self.update_financial_summary()

    def update_row_properties(self, table, removed_row):
        for row in range(removed_row, table.rowCount()):
            button = table.cellWidget(row, 5)
            if button:
                button.setProperty("row", row)

    def update_financial_summary(self):
        total = sum(float(self.services_table.item(row, 3).text().replace('AFN', '')) for row in range(self.services_table.rowCount()) if self.services_table.item(row, 3)) + \
                sum(float(self.prescriptions_table.item(row, 3).text().replace('AFN', '')) for row in range(self.prescriptions_table.rowCount()) if self.prescriptions_table.item(row, 3))

        self.total_amount_label.setText(f"AFN {total:.2f}")
        due = max(0.0, total - self.paid_amount_input.value())
        self.due_amount_label.setText(f"AFN {due:.2f}")

    def update_due_amount_display(self):
        total = float(self.total_amount_label.text().replace('AFN', ''))
        paid = self.paid_amount_input.value()
        due = max(0.0, total - paid)
        self.due_amount_label.setText(f"AFN {due:.2f}")

    def save_visit(self):
        visit_date = self.visit_date_input.date().toString("yyyy-MM-dd")
        notes = self.visit_notes_input.toPlainText().strip()
        lab_results = self.lab_results_input.toPlainText().strip()
        paid_amount = self.paid_amount_input.value()

        if self.is_editing:
            if save_visit_details(self.visit_id, visit_date, notes, lab_results, paid_amount):
                QMessageBox.information(self, "Success", "Visit updated successfully.")
                self.visit_saved.emit(self.patient_id)
                self.clear_form()
            else:
                QMessageBox.critical(self, "Error", "Failed to update visit.")
        else:
            new_visit_id = add_new_visit(self.patient_id, visit_date, notes, lab_results, self.services_table, self.prescriptions_table, paid_amount)
            if new_visit_id:
                QMessageBox.information(self, "Success", "New visit added successfully.")
                self.visit_saved.emit(self.patient_id)
                self.clear_form()
            else:
                QMessageBox.warning(self, "Partial Success", "New visit created, but some items may have failed.")

    def cancel(self):
        self.cancelled.emit()

    def clear_form(self):
        self.visit_date_input.setDate(QDate.currentDate())
        self.visit_notes_input.clear()
        self.lab_results_input.clear()
        self.paid_amount_input.setValue(0.0)
        self.service_tooth_input.clear()
        self.service_notes_input.clear()
        self.med_instr_input.clear()
        self.services_table.setRowCount(0)
        self.prescriptions_table.setRowCount(0)
        self.update_financial_summary()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    try:
        from database.schema import initialize_database
        from database.data_manager import add_patient, add_service, add_medication
        initialize_database()
        if not get_patient_by_id(4):
            add_patient("Test AddVisit", "Tester", "Female", 40, "1 Add St", "555-ADD", "Needs visit")
        if not get_service_by_id(1):
            add_service("cleaning", "Teeth Cleaning", 50.0)
        if not get_medication_by_id(1):
            add_medication("abc", "Antibiotic", 20.0)
    except Exception as e:
        print(f"Error setting up DB: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = AddEditVisitWindow(patient_id=4)
    window.setMinimumSize(900, 700)  # Ensure window is large enough to show content
    window.show()

    sys.exit(app.exec())