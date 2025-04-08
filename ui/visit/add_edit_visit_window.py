import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox,
    QFormLayout, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDateEdit, QAbstractItemView, QLineEdit, QScrollArea, QApplication, QSpacerItem, QSizePolicy,QGridLayout,QCompleter
)
from PyQt6.QtCore import pyqtSignal, Qt, QDate,QSize
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta

from database.data_manager import (
    add_prescription_to_visit, add_service_to_visit, get_medication_by_id,
    get_patient_by_id, get_prescriptions_for_visit, get_service_by_id,
    get_services_for_visit, remove_prescription_from_visit,
    remove_service_from_visit, get_visit_by_id
)
from model.visit_manager import load_initial_data, save_visit_details, add_new_visit

class AddEditVisitWindow(QWidget):
    """
    Widget for adding a new visit or editing an existing one.
    Enhanced UI/UX with modern clean design, clear typography and responsive layout.
    """
    visit_saved = pyqtSignal(int)
    cancelled = pyqtSignal()

    def __init__(self, patient_id, visit_id=None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.visit_id = visit_id
        self.is_editing = visit_id is not None

        # Data holders for patient, visit, services and medications.
        self.patient_data = None
        self.visit_data = None
        self.available_services = {}
        self.available_medications = {}

        if not self.load_initial_data():
            QMessageBox.critical(self, "Error", "Could not load necessary data.")
            return

        self.setWindowTitle("Add/Edit Visit")
        self.setStyleSheet(self.get_stylesheet())
        self.setMinimumSize(900, 700)

        # Main layout with a scroll area for improved responsiveness.
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

        self.create_patient_info_header()
        self.create_visit_details_section()
        self.create_services_section()
        self.create_prescriptions_section()
        self.create_payment_summary_section()
        self.create_action_buttons()

        # Spacer to ensure proper scrolling.
        self.content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Populate fields if in editing mode.
        if self.is_editing:
            self.populate_fields_for_edit()

        self.update_service_price()
        self.update_med_price()
        self.update_financial_summary()

    def get_stylesheet(self):
        # Modern, clean stylesheet with subtle shadows and rounded corners.
        return """
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
            background-color: #ecf0f1;
            color: #2c3e50;
        }
        QGroupBox {
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            margin-top: 1ex;
            padding: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 15px;
            padding: 5px 10px;
            background-color: #3498db;
            color: white;
            font-weight: bold;
            font-size: 11pt;
            border-radius: 4px;
        }
        QLabel {
            padding: 2px;
            font-weight: normal;
            color: #34495e;
        }
        QLineEdit, QTextEdit, QComboBox, QDateEdit {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 6px 8px;
            background-color: #ffffff;
            min-height: 28px;
        }
        QPushButton {
            border-radius: 4px;
            padding: 8px 18px;
            font-size: 10pt;
            font-weight: bold;
            border: none;
            min-height: 28px;
            color: white;
        }
        QPushButton:hover {
            opacity: 0.9;
        }
        QPushButton:pressed {
            opacity: 0.7;
        }
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
        #SaveButton {
            background-color: #3498db;  /* Blue color for save button */
        }
        #SaveButton:hover {
            background-color: #2980b9;  /* Darker blue on hover */
        }
        #CancelButton {
            background-color: #e74c3c;  /* Red color for cancel button */
        }
        #CancelButton:hover {
            background-color: #c0392b;  /* Darker red on hover */
        }
        #AddButton {
            background-color: #2ecc71;  /* Green color for add buttons */
        }
        #AddButton:hover {
            background-color: #27ae60;  /* Darker green on hover */
        }
        QTableWidget {
            border: 1px solid #bdc3c7;
            border-radius: 6px;
            background-color: #ffffff;
            gridline-color: #e0e0e0;
            selection-background-color: #3498db;
            selection-color: white;
        }
        QTableWidget::item {
            padding: 8px 10px;
            border-bottom: 1px solid #e0e0e0;
        }
        QTableWidget::item:selected {
            background-color: #2980b9;
            color: white;
        }
        QHeaderView::section {
            background-color: #eaeaed;
            color: #34495e;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #bdc3c7;
            font-weight: bold;
            font-size: 10pt;
        }
        QScrollArea {
            border: none;
            background-color: #ecf0f1;
        }
        QScrollBar:vertical {
            border: 1px solid #bdc3c7;
            background: #ffffff;
            width: 12px;
            margin: 0px 0px 0px 0px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #bdc3c7;
            min-height: 25px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background: #95a5a6;
        }
        """
    
    def load_initial_data(self):
        """Load patient, visit, available services and medications data."""
        data = load_initial_data(self.patient_id, self.is_editing, self.visit_id)
        if not data:
            return False
        self.patient_data, self.visit_data, self.available_services, self.available_medications = data
        return True

    def create_patient_info_header(self):
        """Header showing patient information."""
        header_layout = QHBoxLayout()
        patient_label = QLabel(f"<b>Patient:</b> {self.patient_data.get('name', 'Unknown')} (ID: {self.patient_id})")
        patient_label.setFont(QFont("Segoe UI", 12))
        header_layout.addWidget(patient_label)
        header_layout.addStretch()
        self.content_layout.addLayout(header_layout)

    def create_visit_details_section(self):
        """Section for visit details such as date, notes and lab results."""
        visit_details_group = QGroupBox("Visit Details")
        form_layout = QFormLayout(visit_details_group)
        form_layout.setSpacing(15)

        self.visit_date_input = QDateEdit(QDate.currentDate())
        self.visit_date_input.setCalendarPopup(True)
        self.visit_notes_input = QTextEdit()
        self.visit_notes_input.setPlaceholderText("Enter general notes about the visit...")
        self.visit_notes_input.setMinimumHeight(100)
        self.lab_results_input = QTextEdit()
        self.lab_results_input.setPlaceholderText("Enter lab results or references...")
        self.lab_results_input.setMinimumHeight(100)

        form_layout.addRow("Visit Date:", self.visit_date_input)
        form_layout.addRow("Notes:", self.visit_notes_input)
        form_layout.addRow("Lab Results:", self.lab_results_input)
        self.content_layout.addWidget(visit_details_group)

    def create_services_section(self):
        """Section for adding and displaying performed services."""
        services_group = QGroupBox("Services Performed")
        layout = QVBoxLayout(services_group)

        # Layout for adding a new service.
        add_layout = QGridLayout()
        add_layout.setSpacing(10)

        self.service_combo = QComboBox()
        self.service_combo.setEditable(True)  # Make the combo box editable
        self.service_combo.addItems(sorted(self.available_services.keys()))
        self.service_combo.setCurrentIndex(-1)  # No initial selection

        # Set up completer for search functionality
        completer = QCompleter(sorted(self.available_services.keys()))
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.service_combo.setCompleter(completer)

        self.service_combo.currentIndexChanged.connect(self.update_service_price)

        self.service_tooth_input = QLineEdit()
        self.service_tooth_input.setPlaceholderText("Tooth # (optional)")
        self.service_tooth_input.setFixedWidth(80)

        self.service_price_input = QLineEdit()
        self.service_price_input.setPlaceholderText("Enter price")
        self.service_price_input.setFixedWidth(100)
        self.service_price_input.textChanged.connect(self.update_financial_summary)

        self.service_notes_input = QLineEdit()
        self.service_notes_input.setPlaceholderText("Enter service notes (optional)...")

        self.add_service_button = QPushButton(qta.icon('fa5s.plus-circle', color='white'), "Add Service")
        self.add_service_button.setObjectName("AddButton")
        self.add_service_button.clicked.connect(self.add_service_item)

        add_layout.addWidget(QLabel("Service:"), 0, 0)
        add_layout.addWidget(self.service_combo, 0, 1)
        add_layout.addWidget(QLabel("Tooth #:"), 0, 2)
        add_layout.addWidget(self.service_tooth_input, 0, 3)
        add_layout.addWidget(QLabel("Price:"), 0, 4)
        add_layout.addWidget(self.service_price_input, 0, 5)
        add_layout.addWidget(QLabel("Notes:"), 1, 0)
        add_layout.addWidget(self.service_notes_input, 1, 1, 1, 5)
        add_layout.addWidget(self.add_service_button, 0, 6, 2, 1, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Table to display added services.
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels(["ID", "Service", "Tooth #", "Price", "Notes", "Action"])
        self.services_table.setColumnHidden(0, True)
        self.services_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.services_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.services_table.setMinimumHeight(180)

        layout.addLayout(add_layout)
        layout.addWidget(self.services_table)
        self.content_layout.addWidget(services_group)

    def create_prescriptions_section(self):
        """Section for adding and displaying issued prescriptions."""
        prescriptions_group = QGroupBox("Prescriptions Issued")
        layout = QVBoxLayout(prescriptions_group)

        # Layout for adding a new prescription.
        add_layout = QGridLayout()
        add_layout.setSpacing(10)

        self.med_combo = QComboBox()
        self.med_combo.setEditable(True)  # Make the combo box editable
        self.med_combo.addItems(sorted(self.available_medications.keys()))
        self.med_combo.setCurrentIndex(-1)  # No initial selection

        # Set up completer for search functionality
        completer = QCompleter(sorted(self.available_medications.keys()))
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.med_combo.setCompleter(completer)

        self.med_combo.currentIndexChanged.connect(self.update_med_price)

        self.med_qty_input = QLineEdit()
        self.med_qty_input.setPlaceholderText("Quantity")
        self.med_qty_input.setFixedWidth(80)
        self.med_qty_input.textChanged.connect(self.update_med_price)

        self.med_price_input = QLineEdit()
        self.med_price_input.setPlaceholderText("Total price")
        self.med_price_input.setFixedWidth(100)
        self.med_price_input.textChanged.connect(self.update_financial_summary)

        self.med_instr_input = QLineEdit()
        self.med_instr_input.setPlaceholderText("Enter instructions (optional)...")

        self.add_med_button = QPushButton(qta.icon('fa5s.plus-circle', color='white'), "Add Medication")
        self.add_med_button.setObjectName("AddButton")
        self.add_med_button.clicked.connect(self.add_prescription_item)

        add_layout.addWidget(QLabel("Medication:"), 0, 0)
        add_layout.addWidget(self.med_combo, 0, 1)
        add_layout.addWidget(QLabel("Qty:"), 0, 2)
        add_layout.addWidget(self.med_qty_input, 0, 3)
        add_layout.addWidget(QLabel("Price:"), 0, 4)
        add_layout.addWidget(self.med_price_input, 0, 5)
        add_layout.addWidget(QLabel("Instructions:"), 1, 0)
        add_layout.addWidget(self.med_instr_input, 1, 1, 1, 5)
        add_layout.addWidget(self.add_med_button, 0, 6, 2, 1, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Table to display added prescriptions.
        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setColumnCount(6)
        self.prescriptions_table.setHorizontalHeaderLabels(["ID", "Medication", "Qty", "Price", "Instructions", "Action"])
        self.prescriptions_table.setColumnHidden(0, True)
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.prescriptions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.prescriptions_table.setMinimumHeight(180)

        layout.addLayout(add_layout)
        layout.addWidget(self.prescriptions_table)
        self.content_layout.addWidget(prescriptions_group)

    def create_payment_summary_section(self):
        """Section for displaying the financial summary including total, paid and due amounts."""
        payment_group = QGroupBox("Payment Summary")
        layout = QFormLayout(payment_group)
        layout.setSpacing(15)

        self.total_amount_label = QLabel("0.00")
        self.paid_amount_input = QLineEdit()
        self.paid_amount_input.setPlaceholderText("Amount Paid")
        self.paid_amount_input.setFixedWidth(120)
        self.paid_amount_input.textChanged.connect(self.update_financial_summary)
        self.due_amount_label = QLabel("0.00")

        layout.addRow("Total Amount:", self.total_amount_label)
        layout.addRow("Amount Paid:", self.paid_amount_input)
        layout.addRow("Amount Due:", self.due_amount_label)
        self.content_layout.addWidget(payment_group)

    def create_action_buttons(self):
        """Bottom action buttons for saving or cancelling the visit."""
        action_layout = QHBoxLayout()
        action_layout.setSpacing(15)
        action_layout.addStretch()

        self.save_button = QPushButton(qta.icon('fa5s.save', color='white'), "Save Visit")
        self.save_button.setObjectName("SaveButton")
        self.save_button.clicked.connect(self.save_visit)

        self.cancel_button = QPushButton(qta.icon('fa5s.times-circle', color='white'), "Cancel")
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.clicked.connect(self.cancel)

        action_layout.addWidget(self.save_button)
        action_layout.addWidget(self.cancel_button)
        self.content_layout.addLayout(action_layout)

    def populate_fields_for_edit(self):
        """Populate form fields with visit data when editing an existing visit."""
        if not self.visit_data:
            return

        visit_date = QDate.fromString(self.visit_data.get('visit_date', ''), "yyyy-MM-dd")
        self.visit_date_input.setDate(visit_date if visit_date.isValid() else QDate.currentDate())
        self.visit_notes_input.setPlainText(self.visit_data.get('notes', ''))
        self.lab_results_input.setPlainText(self.visit_data.get('lab_results', ''))
        self.paid_amount_input.setText(str(self.visit_data.get('paid_amount', 0.0)))

        # Populate services table.
        visit_services = get_services_for_visit(self.visit_id)
        self.services_table.setRowCount(0)
        if visit_services:
            for service in visit_services:
                self._add_row_to_table(self.services_table, service, is_service=True)

        # Populate prescriptions table.
        visit_prescriptions = get_prescriptions_for_visit(self.visit_id)
        self.prescriptions_table.setRowCount(0)
        if visit_prescriptions:
            for prescription in visit_prescriptions:
                self._add_row_to_table(self.prescriptions_table, prescription, is_service=False)

        self.update_financial_summary()

    def update_service_price(self):
        """Update service price based on selected service."""
        service_name = self.service_combo.currentText()
        if service_name in self.available_services:
            self.service_price_input.setText(f"{self.available_services[service_name]['price']:.2f}")

    def update_med_price(self):
        """Update medication price based on selected medication and quantity."""
        med_name = self.med_combo.currentText()
        if med_name in self.available_medications:
            unit_price = self.available_medications[med_name]['price']
            try:
                qty = int(self.med_qty_input.text())
            except ValueError:
                qty = 1
            total_price = unit_price * max(qty, 1)
            self.med_price_input.setText(f"{total_price:.2f}")

    def add_service_item(self):
        """Add a service item to the services table and database if editing."""
        service_name = self.service_combo.currentText()
        if not service_name or service_name not in self.available_services:
            QMessageBox.warning(self, "Selection Error", "Please select a valid service.")
            return

        service_id = self.available_services[service_name]['id']
        tooth_str = self.service_tooth_input.text().strip()
        tooth_number = int(tooth_str) if tooth_str.isdigit() else None
        try:
            price = float(self.service_price_input.text() or 0)
        except ValueError:
            price = 0.0
        notes = self.service_notes_input.text().strip()

        if self.is_editing:
            visit_service_id = add_service_to_visit(self.visit_id, service_id, tooth_number, price, notes)
            if visit_service_id:
                item_data = {
                    'visit_service_id': visit_service_id,
                    'service_name': service_name,
                    'tooth_number': tooth_number,
                    'price_charged': price,
                    'notes': notes
                }
                self._add_row_to_table(self.services_table, item_data, is_service=True)
                self.update_financial_summary()
            else:
                QMessageBox.critical(self, "Database Error", "Failed to add service.")
        else:
            item_data = {
                'service_id': service_id,
                'service_name': service_name,
                'tooth_number': tooth_number,
                'price_charged': price,
                'notes': notes
            }
            self._add_row_to_table(self.services_table, item_data, is_service=True)
            self.update_financial_summary()

    def add_prescription_item(self):
        """Add a prescription item to the prescriptions table and database if editing."""
        med_name = self.med_combo.currentText()
        if not med_name or med_name not in self.available_medications:
            QMessageBox.warning(self, "Selection Error", "Please select a valid medication.")
            return

        med_id = self.available_medications[med_name]['id']
        try:
            quantity = int(self.med_qty_input.text() or 1)
        except ValueError:
            quantity = 1
        try:
            price = float(self.med_price_input.text() or 0)
        except ValueError:
            price = 0.0
        instructions = self.med_instr_input.text().strip()

        if self.is_editing:
            visit_prescription_id = add_prescription_to_visit(self.visit_id, med_id, quantity, price, instructions)
            if visit_prescription_id:
                item_data = {
                    'visit_prescription_id': visit_prescription_id,
                    'medication_name': med_name,
                    'quantity': quantity,
                    'price_charged': price,
                    'instructions': instructions
                }
                self._add_row_to_table(self.prescriptions_table, item_data, is_service=False)
                self.update_financial_summary()
            else:
                QMessageBox.critical(self, "Database Error", "Failed to add prescription.")
        else:
            item_data = {
                'medication_id': med_id,
                'medication_name': med_name,
                'quantity': quantity,
                'price_charged': price,
                'instructions': instructions
            }
            self._add_row_to_table(self.prescriptions_table, item_data, is_service=False)
            self.update_financial_summary()

    def _add_row_to_table(self, table: QTableWidget, item_data: dict, is_service: bool):
        """Helper method to add a row to the given table with a remove button."""
        row = table.rowCount()
        table.insertRow(row)

        # Create a QWidget to hold the remove button
        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cell_layout.setContentsMargins(0, 0, 0, 0)

        # Create remove button with trash icon
        remove_button = QPushButton()
        remove_button.setIcon(qta.icon('fa5s.trash-alt', color='#e74c3c'))  # Set explicit color
        remove_button.setToolTip(f"Remove this {'service' if is_service else 'prescription'}")
        remove_button.setProperty("row", row)
        remove_button.setIconSize(QSize(15, 15))  # Increase icon size for better visibility
        remove_button.setFixedSize(15, 15)  # Set fixed size for the button
        remove_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: -10px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-radius: -2px;
            }
        """)

        # Fill table row with data and attach remove button
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
            table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(notes))
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
            table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(instructions))

        # Add the remove button to the last column
        cell_layout.addWidget(remove_button)
        table.setCellWidget(row, 5, cell_widget)
        
    def remove_service_item(self, button):
        """Remove a service row from the table and database if editing."""
        row = button.property("row")
        visit_service_id = button.property("item_id")

        if row is None:
            return

        confirm = self.show_confirmation_dialog("Confirm", "Remove this service?")
        if confirm == QMessageBox.StandardButton.Yes:
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
        """Remove a prescription row from the table and database if editing."""
        row = button.property("row")
        visit_prescription_id = button.property("item_id")

        if row is None:
            return

        confirm = self.show_confirmation_dialog("Confirm", "Remove this prescription?")
        if confirm == QMessageBox.StandardButton.Yes:
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
    def show_confirmation_dialog(self, title, message):
        """Show a confirmation dialog with custom styled Yes and No buttons."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        # Style the Yes and No buttons
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        no_button = msg_box.button(QMessageBox.StandardButton.No)

        button_style = """
            QPushButton {
                background-color: #3498db;  /* Blue color for Yes button */
                color: white;
                border-radius: 4px;
                padding: 8px 18px;
                font-size: 10pt;
                font-weight: bold;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #2980b9;  /* Darker blue on hover */
            }
            QPushButton:pressed {
                background-color: #2471a3;  /* Even darker blue on press */
            }
        """

        yes_button.setStyleSheet(button_style)
        no_button.setStyleSheet(button_style.replace("#3498db", "#e74c3c").replace("#2980b9", "#c0392b").replace("#2471a3", "#a93226"))

        return msg_box.exec()
    def update_row_properties(self, table, removed_row):
        """Update the row property for buttons after a removal so that the row numbers are consistent."""
        for row in range(removed_row, table.rowCount()):
            button = table.cellWidget(row, 5)
            if button:
                button.setProperty("row", row)

    def update_financial_summary(self):
        """Calculate and update the total, paid and due amounts."""
        total_services = sum(
            float(self.services_table.item(row, 3).text().strip())
            for row in range(self.services_table.rowCount()) if self.services_table.item(row, 3)
        )
        total_prescriptions = sum(
            float(self.prescriptions_table.item(row, 3).text().strip())
            for row in range(self.prescriptions_table.rowCount()) if self.prescriptions_table.item(row, 3)
        )
        total = total_services + total_prescriptions

        self.total_amount_label.setText(f"{total:.2f}")
        try:
            paid = float(self.paid_amount_input.text() or 0)
        except ValueError:
            paid = 0.0
        due = max(0.0, total - paid)
        self.due_amount_label.setText(f"{due:.2f}")

    def save_visit(self):
        """Save the visit details and notify via signals."""
        visit_date = self.visit_date_input.date().toString("yyyy-MM-dd")
        notes = self.visit_notes_input.toPlainText().strip()
        lab_results = self.lab_results_input.toPlainText().strip()
        try:
            paid_amount = float(self.paid_amount_input.text() or 0)
        except ValueError:
            paid_amount = 0.0

        if self.is_editing:
            if save_visit_details(self.visit_id, visit_date, notes, lab_results, paid_amount):
                self.show_message("Success", "Visit updated successfully.")
                self.visit_saved.emit(self.patient_id)
                self.clear_form()
            else:
                QMessageBox.critical(self, "Error", "Failed to update visit.")
        else:
            new_visit_id = add_new_visit(self.patient_id, visit_date, notes, lab_results, self.services_table, self.prescriptions_table, paid_amount)
            if new_visit_id:
                self.show_message("Success", "New visit added successfully.")
                self.visit_saved.emit(self.patient_id)
                self.clear_form()
            else:
                QMessageBox.warning(self, "Partial Success", "New visit created, but some items may have failed.")

    def show_message(self, title, message):
        """Show a message box with custom styled OK button."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Style the OK button
        ok_button = msg_box.button(QMessageBox.StandardButton.Ok)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;  /* Green color for OK button */
                color: white;
                border-radius: 4px;
                padding: 8px 18px;
                font-size: 10pt;
                font-weight: bold;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #27ae60;  /* Darker green on hover */
            }
            QPushButton:pressed {
                background-color: #239b56;  /* Even darker green on press */
            }
        """)

        msg_box.exec()
    def cancel(self):
        """Emit cancelled signal on cancel."""
        self.cancelled.emit()

    def clear_form(self):
        """Reset the form fields after saving or cancelling."""
        self.visit_date_input.setDate(QDate.currentDate())
        self.visit_notes_input.clear()
        self.lab_results_input.clear()
        self.paid_amount_input.clear()
        self.service_tooth_input.clear()
        self.service_notes_input.clear()
        self.med_instr_input.clear()
        self.services_table.setRowCount(0)
        self.prescriptions_table.setRowCount(0)
        self.update_financial_summary()

if __name__ == '__main__':
    try:
        from database.schema import initialize_database
        from database.data_manager import add_patient, add_service, add_medication
        initialize_database()
        # Setup sample patient, service, and medication data if they don't exist.
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
    window.show()

    sys.exit(app.exec())
