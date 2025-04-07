import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QFormLayout, QGroupBox, QPushButton,
                             QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QLineEdit, QAbstractItemView, QScrollArea, QApplication, QGridLayout, QAbstractSpinBox,
                             QSizePolicy,QSpacerItem)
from PyQt6.QtCore import pyqtSignal, Qt, QDate
from PyQt6.QtGui import QDoubleValidator, QPalette, QColor
import qtawesome as qta
from pathlib import Path

from database.data_manager import add_service_to_visit, get_medication_by_id, get_services_for_visit, get_visit_by_id
from model.visit_detail_window_model import DATABASE_AVAILABLE, VisitDetailModel, get_patient_by_id, get_service_by_id

class NoScrollSpinBox(QSpinBox):
    """A QSpinBox that ignores wheel events."""
    def wheelEvent(self, event):
        event.ignore()  # Prevent changing value with mouse wheel

class NoScrollDoubleSpinBox(QDoubleSpinBox):
    """A QDoubleSpinBox that ignores wheel events."""
    def wheelEvent(self, event):
        event.ignore()  # Prevent changing value with mouse wheel

class VisitDetailWindow(QWidget):
    """Widget to display and edit visit details with a modern UI/UX."""
    visit_updated = pyqtSignal(int)  # Signal (patient_id) when visit is updated
    closed = pyqtSignal()            # Signal to return to patient details

    def __init__(self, visit_id, patient_id=None, parent=None):
        super().__init__(parent)
        self.visit_id = visit_id  # Store the visit_id as an attribute
        self.model = VisitDetailModel(visit_id, patient_id)
        self.is_editing = False
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._update_view_mode()  # Set initial state (view mode)
        # Set minimum size and window title
        self.setWindowTitle(f"Visit Details - ID: {visit_id}")
        self.setMinimumSize(950, 750)  # Slightly larger for better spacing

    def _setup_ui(self):
        """Initialize the main UI structure and widgets."""
        # Main layout wrapped in a scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Content layout
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(20)

        # Add sections to content layout
        self._setup_patient_info()
        self._setup_visit_info()
        self._setup_services_section()
        self._setup_prescriptions_section()
        self._setup_financial_summary()
        self._setup_action_buttons()

        # Add content layout to main layout
        self.main_layout.addLayout(self.content_layout)
        self.main_layout.addLayout(self.action_layout)  # Add action buttons layout

        # Add a spacer to create empty space at the bottom
        self.main_layout.addSpacerItem(QSpacerItem(100, 100, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Set the widget for the scroll area
        self.scroll.setWidget(self.main_widget)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.scroll)

        # Populate initial data
        self._populate_fields()
        self._populate_services_table()
        self._populate_prescriptions_table()
        self._update_financial_summary()
    def show(self):
        """Show the window and disable the parent's scrollbar if applicable."""
        parent = self.parent()
        if isinstance(parent, QScrollArea):  # Check if parent is a scrollable widget
            parent.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        super().show()

    def _setup_patient_info(self):
        """Create the patient information group box."""
        patient_group = QGroupBox("Patient Information")
        patient_layout = QFormLayout(patient_group)
        patient_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        patient_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        patient_layout.setSpacing(10)

        self.patient_name_label = QLabel(self.model.patient_data.get('name', 'N/A'))
        self.patient_id_label = QLabel(str(self.model.patient_data.get('patient_id', 'N/A')))

        patient_layout.addRow(QLabel("<b>Patient Name:</b>"), self.patient_name_label)
        patient_layout.addRow(QLabel("<b>Patient ID:</b>"), self.patient_id_label)
        self.content_layout.addWidget(patient_group)

    def _setup_visit_info(self):
        """Create the visit information group box."""
        visit_group = QGroupBox("Visit Information")
        visit_form_layout = QFormLayout(visit_group)
        visit_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        visit_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignTop)  # Align labels top for QTextEdit
        visit_form_layout.setSpacing(10)

        self.visit_details_label = QLabel()  # Will be populated later
        self.visit_date_input = QDateEdit()
        self.visit_date_input.setCalendarPopup(True)
        self.visit_date_input.setDisplayFormat("yyyy-MM-dd")

        self.visit_notes_input = QTextEdit()
        self.visit_notes_input.setMinimumHeight(100)
        self.visit_notes_input.setPlaceholderText("General notes about the visit...")

        self.lab_results_input = QTextEdit()
        self.lab_results_input.setMinimumHeight(100)
        self.lab_results_input.setPlaceholderText("Lab results or references...")

        visit_form_layout.addRow(QLabel("<b>Visit Details:</b>"), self.visit_details_label)
        visit_form_layout.addRow(QLabel("<b>Visit Date:</b>"), self.visit_date_input)
        visit_form_layout.addRow(QLabel("<b>Notes:</b>"), self.visit_notes_input)
        visit_form_layout.addRow(QLabel("<b>Lab Results:</b>"), self.lab_results_input)
        self.content_layout.addWidget(visit_group)

    def _setup_services_section(self):
        """Create the services group box, table, and add controls."""
        services_group = QGroupBox("Services Performed")
        services_layout = QVBoxLayout(services_group)
        services_layout.setSpacing(15)

        # Add Service Controls (initially hidden)
        self.add_service_widget = QWidget()
        add_service_layout = QGridLayout(self.add_service_widget)  # Use GridLayout for better alignment
        add_service_layout.setSpacing(10)

        self.service_combo = QComboBox()
        self.service_combo.setPlaceholderText("Select Service...")
        self.service_combo.addItems([""] + sorted(self.model.available_services.keys()))  # Add blank item
        self.service_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.service_tooth_input = QLineEdit()
        self.service_tooth_input.setPlaceholderText("Tooth #")
        self.service_tooth_input.setFixedWidth(80)

        self.service_price_input = NoScrollDoubleSpinBox()  # Use custom spinbox
        self.service_price_input.setRange(0.0, 99999.99)
        self.service_price_input.setDecimals(2)
        self.service_price_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)  # Hide up/down arrows
        self.service_price_input.setFixedWidth(100)
        self.service_price_input.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.service_notes_input = QLineEdit()  # Changed to QLineEdit for brevity unless long notes are common
        self.service_notes_input.setPlaceholderText("Service notes (optional)")
        self.service_notes_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.add_service_button = QPushButton(qta.icon('fa5s.plus-circle', color='white'), " Add Service")
        self.add_service_button.setObjectName("AddButton")  # For specific styling
        self.add_service_button.setFixedHeight(35)  # Consistent height

        add_service_layout.addWidget(QLabel("Service:"), 0, 0)
        add_service_layout.addWidget(self.service_combo, 0, 1)
        add_service_layout.addWidget(QLabel("Tooth:"), 0, 2)
        add_service_layout.addWidget(self.service_tooth_input, 0, 3)
        add_service_layout.addWidget(QLabel("Price:"), 0, 4)
        add_service_layout.addWidget(self.service_price_input, 0, 5)
        add_service_layout.addWidget(QLabel("Notes:"), 1, 0)
        add_service_layout.addWidget(self.service_notes_input, 1, 1, 1, 5)  # Span notes across
        add_service_layout.addWidget(self.add_service_button, 0, 6, 2, 1, alignment=Qt.AlignmentFlag.AlignVCenter)  # Span button vertically

        services_layout.addWidget(self.add_service_widget)
        self.add_service_widget.setVisible(False)  # Start hidden

        # Services Table
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)  # ID (hidden), Service, Tooth #, Price, Notes, Action
        self.services_table.setHorizontalHeaderLabels(["ID", "Service", "Tooth #", "Price", "Notes", "Action"])
        self._configure_table(self.services_table, [0])  # Hide ID column
        services_layout.addWidget(self.services_table)
        self.content_layout.addWidget(services_group)

    def _setup_prescriptions_section(self):
        """Create the prescriptions group box, table, and add controls."""
        prescriptions_group = QGroupBox("Prescriptions Issued")
        prescriptions_layout = QVBoxLayout(prescriptions_group)
        prescriptions_layout.setSpacing(15)

        # Add Prescription Controls (initially hidden)
        self.add_prescription_widget = QWidget()
        add_med_layout = QGridLayout(self.add_prescription_widget)  # Use GridLayout
        add_med_layout.setSpacing(10)

        self.med_combo = QComboBox()
        self.med_combo.setPlaceholderText("Select Medication...")
        self.med_combo.addItems([""] + sorted(self.model.available_medications.keys()))  # Add blank item
        self.med_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.med_qty_input = NoScrollSpinBox()  # Use custom spinbox
        self.med_qty_input.setRange(1, 999)
        self.med_qty_input.setValue(1)
        self.med_qty_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)  # Hide arrows
        self.med_qty_input.setFixedWidth(70)
        self.med_qty_input.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.med_price_input = NoScrollDoubleSpinBox()  # Use custom spinbox
        self.med_price_input.setRange(0.0, 9999.99)
        self.med_price_input.setDecimals(2)
        self.med_price_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)  # Hide arrows
        self.med_price_input.setFixedWidth(100)
        self.med_price_input.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.med_instr_input = QLineEdit()  # Changed to QLineEdit
        self.med_instr_input.setPlaceholderText("Instructions (optional)")
        self.med_instr_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.add_med_button = QPushButton(qta.icon('fa5s.pills', color='white'), " Add Med")  # Changed icon
        self.add_med_button.setObjectName("AddButton")  # For styling
        self.add_med_button.setFixedHeight(35)

        add_med_layout.addWidget(QLabel("Medication:"), 0, 0)
        add_med_layout.addWidget(self.med_combo, 0, 1)
        add_med_layout.addWidget(QLabel("Qty:"), 0, 2)
        add_med_layout.addWidget(self.med_qty_input, 0, 3)
        add_med_layout.addWidget(QLabel("Price:"), 0, 4)
        add_med_layout.addWidget(self.med_price_input, 0, 5)
        add_med_layout.addWidget(QLabel("Instructions:"), 1, 0)
        add_med_layout.addWidget(self.med_instr_input, 1, 1, 1, 5)  # Span instructions
        add_med_layout.addWidget(self.add_med_button, 0, 6, 2, 1, alignment=Qt.AlignmentFlag.AlignVCenter)  # Span button

        prescriptions_layout.addWidget(self.add_prescription_widget)
        self.add_prescription_widget.setVisible(False)  # Start hidden

        # Prescriptions Table
        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setColumnCount(6)  # ID (hidden), Medication, Qty, Price, Instructions, Action
        self.prescriptions_table.setHorizontalHeaderLabels(["ID", "Medication", "Qty", "Price", "Instructions", "Action"])
        self._configure_table(self.prescriptions_table, [0])  # Hide ID column
        prescriptions_layout.addWidget(self.prescriptions_table)
        self.content_layout.addWidget(prescriptions_group)

    def _configure_table(self, table, hidden_columns):
        """Apply common configuration to QTableWidget."""
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(180)  # Adjust as needed
        table.verticalHeader().setVisible(False)  # Hide row numbers

        header = table.horizontalHeader()
        # Configure resize modes for other columns first
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Default or specific columns
        # Stretch the ones that need it
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name column
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Notes/Instructions column

        # Set a fixed width for the Action column (index 5)
        action_column_index = 5
        action_column_width = 45  # Adjust this width as needed (try 40, 50, etc.)
        header.setSectionResizeMode(action_column_index, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(action_column_index, action_column_width)

        # Hide specified columns AFTER setting widths/modes
        for col_index in hidden_columns:
            table.setColumnHidden(col_index, True)

        # Set row selection color
        table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #3498db; /* Blue selection */
                color: white;
            }
            QTableWidget::item {
                padding: 8px 10px; /* More padding */
                border-bottom: 1px solid #e0e0e0; /* Row separator */
            }
        """)

    def _setup_financial_summary(self):
        """Create the financial summary group box."""
        finance_group = QGroupBox("Financial Summary")
        finance_layout = QFormLayout(finance_group)
        finance_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        finance_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        finance_layout.setSpacing(10)

        self.total_amount_label = QLabel("0.00")
        self.paid_amount_label = QLabel("0.00")
        self.due_amount_label = QLabel("0.00")
        self.pay_due_input = QLineEdit()
        self.pay_due_input.setPlaceholderText("Enter amount paying now")
        self.pay_due_input.setValidator(QDoubleValidator(0.0, 99999.99, 2))
        self.pay_due_input.setFixedWidth(180)  # Give it a fixed width
        self.pay_due_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.pay_due_input.setEnabled(False)  # Disabled in view mode

        finance_layout.addRow(QLabel("<b>Total Amount:</b>"), self.total_amount_label)
        finance_layout.addRow(QLabel("<b>Previously Paid:</b>"), self.paid_amount_label)
        finance_layout.addRow(QLabel("<b>Amount Due:</b>"), self.due_amount_label)
        finance_layout.addRow(QLabel("<b>Pay Now:</b>"), self.pay_due_input)

        # Add a label to show the *updated* amount due after Pay Now entry
        self.updated_due_label = QLabel("0.00")
        finance_layout.addRow(QLabel("<b>Remaining Due:</b>"), self.updated_due_label)

        self.content_layout.addWidget(finance_group)

    def _setup_action_buttons(self):
        """Create the main action buttons (Print, Edit, Save, Close/Cancel)."""
        # Store the layout as a class member
        self.action_layout = QHBoxLayout()
        self.action_layout.setSpacing(15)
        self.action_layout.addStretch(1)  # Push buttons to the right

        # --- Add Print Button ---
        self.print_button = QPushButton(qta.icon('fa5s.print', color='#555'), " Print Report") # Use a suitable icon color
        self.print_button.setObjectName("PrintButton") # Optional: for specific styling
        self.print_button.setToolTip("Generate and save a PDF report for this visit")
        # --- End Add Print Button ---

        # Existing Action Buttons
        self.edit_button = QPushButton(qta.icon('fa5s.edit', color='#2980b9'), " Edit Visit")
        self.save_button = QPushButton(qta.icon('fa5s.save', color='white'), " Save Changes")
        self.cancel_or_close_button = QPushButton(qta.icon('fa5s.times-circle', color='white'), " Close")

        # --- Add Print Button to layout ---
        self.action_layout.addWidget(self.print_button)
        # --- End Add Print Button ---

        self.action_layout.addWidget(self.edit_button)
        self.action_layout.addWidget(self.save_button)
        self.action_layout.addWidget(self.cancel_or_close_button)

    def _apply_styles(self):
        """Apply comprehensive CSS-like styling to the widget."""
        # Color Palette
        primary_color = "#3498db"  # Bright Blue (used for headers, edit button)
        secondary_color = "#2ecc71" # Green (used for save button)
        danger_color = "#e74c3c"   # Red (used for cancel/close button)
        info_color = "#7f8c8d"     # Gray (used for print button)
        background_color = "#ecf0f1" # Light Grayish Blue
        content_bg_color = "#ffffff"   # White
        text_color = "#2c3e50"       # Dark Gray/Blue
        label_color = "#555555"      # Medium Gray for labels
        border_color = "#bdc3c7"     # Light Gray border
        hover_primary = "#2980b9"
        hover_secondary = "#27ae60"
        hover_danger = "#c0392b"
        hover_info = "#95a5a6"

        # Font Sizes (adjust as needed)
        base_font_size = "10pt"
        large_font_size = "12pt"
        header_font_size = "14pt"

        self.setStyleSheet(f"""
            VisitDetailWindow {{
                background-color: {background_color};
                font-family: Segoe UI, Arial, sans-serif; /* Modern font stack */
                font-size: {base_font_size};
                color: {text_color};
            }}
            QGroupBox {{
                background-color: {content_bg_color};
                border: 1px solid {border_color};
                border-radius: 8px; /* Rounded corners */
                margin-top: 1em; /* Space for title */
                padding: 15px; /* Internal padding */
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background-color: {primary_color};
                color: white;
                border-radius: 5px; /* Slightly rounded title */
                font-weight: bold;
                font-size: {large_font_size};
                margin-left: 10px;
            }}
            QLabel {{
                color: {label_color};
                font-size: {base_font_size};
                padding-bottom: 2px; /* Space below labels */
            }}
            /* Style for the main Patient Name label */
            QLabel#PatientNameLabel {{
                font-weight: bold;
                font-size: {header_font_size};
                color: {primary_color};
                padding-bottom: 10px;
            }}
            /* Style for the Patient ID label (using the name from the error hint) */
            QLabel#PatientIDLabel {{
                font-weight: normal; /* Or bold if desired */
                font-size: {base_font_size}; /* Or large_font_size */
                color: {label_color}; /* Or primary_color */
                /* Add other specific styles if needed */
            }}
             QLabel#FinancialTotalLabel, QLabel#FinancialPaidLabel, QLabel#FinancialDueLabel {{
                font-weight: bold;
                font-size: {large_font_size};
                color: {text_color}; /* Darker text for financial labels */
            }}
            QLabel#FinancialValueTotal, QLabel#FinancialValuePaid {{
                 font-size: {large_font_size};
                 color: {text_color};
             }}
            QLabel#FinancialValueDue {{
                font-weight: bold;
                font-size: {large_font_size};
                color: {danger_color}; /* Red color for due amount */
            }}
            QLineEdit, QDateEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox {{
                background-color: {content_bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px;
                font-size: {base_font_size};
                color: {text_color};
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {primary_color}; /* Highlight focus */
                background-color: #fdfefe; /* Slightly different background on focus */
            }}
             QLineEdit:read-only, QTextEdit:read-only, QDateEdit:read-only,
             QSpinBox:read-only, QDoubleSpinBox:read-only {{
                 background-color: #f0f0f0; /* Gray out read-only fields slightly */
                 color: #777;
                 border: 1px solid #d0d0d0;
             }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                /* image: url(icons/down_arrow.png); */ /* Ensure you have an icon or use qta */
                width: 12px;
                height: 12px;
                padding-right: 5px;
            }}
            QTableWidget {{
                background-color: {content_bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                gridline-color: {border_color};
                font-size: {base_font_size};
                selection-background-color: {primary_color}; /* Color when cell/row selected */
                selection-color: white;
            }}
            QHeaderView::section {{
                background-color: {primary_color};
                color: white;
                padding: 5px;
                border: none; /* Remove default borders */
                border-bottom: 1px solid {border_color}; /* Add bottom border only */
                font-weight: bold;
                font-size: {base_font_size};
            }}
            QHeaderView {{
                border: none; /* Remove header frame */
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget QLineEdit, QTableWidget QComboBox, QTableWidget QSpinBox, QTableWidget QDoubleSpinBox {{
                 border-radius: 0px; /* Remove radius for table cells */
                 border: none; /* Typically remove borders inside tables unless editing */
            }}
            /* Style SpinBox buttons */
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                 subcontrol-origin: border;
                 subcontrol-position: top right;
                 width: 16px;
                 /* image: url(icons/up_arrow.png); */ /* Use icons or leave default */
                 border-left: 1px solid {border_color};
                 border-bottom: 1px solid {border_color};
                 border-top-right-radius: 4px;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                 subcontrol-origin: border;
                 subcontrol-position: bottom right;
                 width: 16px;
                 /* image: url(icons/down_arrow.png); */
                 border-left: 1px solid {border_color};
                 border-top: 1px solid {border_color};
                 border-bottom-right-radius: 4px;
            }}
             QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
             QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                 background-color: #e0e0e0;
             }}

            /* --- Action Button Styles --- */
            QPushButton {{
                padding: 8px 15px;
                border-radius: 5px;
                font-size: {base_font_size};
                font-weight: bold;
                border: none; /* Remove default border */
                min-width: 80px; /* Ensure minimum button width */
            }}
            /* Print Button */
            #PrintButton {{
                background-color: {info_color};
                color: white;
            }}
            #PrintButton:hover {{
                background-color: {hover_info};
            }}
            /* Edit Button */
            #EditButton {{ /* Assuming you give the edit button this objectName */
                 background-color: {primary_color};
                 color: white;
            }}
            #EditButton:hover {{
                 background-color: {hover_primary};
            }}
            /* Save Button */
            #SaveButton {{ /* Assuming you give the save button this objectName */
                background-color: {secondary_color};
                color: white;
            }}
            #SaveButton:hover {{
                background-color: {hover_secondary};
            }}
             /* Cancel/Close Button */
            #CancelCloseButton {{ /* Assuming you give the cancel/close button this objectName */
                background-color: {danger_color};
                color: white;
            }}
            #CancelCloseButton:hover {{
                background-color: {hover_danger};
            }}
            /* Add Item Buttons */
            #AddServiceButton, #AddMedButton {{ /* Give Add buttons these objectNames */
                background-color: #e0e0e0; /* Lighter gray for add buttons */
                color: #333;
                font-weight: normal;
                padding: 5px 10px;
                min-width: 60px;
                border: 1px solid #ccc;
            }}
            #AddServiceButton:hover, #AddMedButton:hover {{
                background-color: #d0d0d0;
            }}

             /* Disable button style */
             QPushButton:disabled {{
                 background-color: #bdc3c7; /* Gray out disabled buttons */
                 color: #7f8c8d;
             }}
             QLineEdit:disabled, QTextEdit:disabled, QDateEdit:disabled,
             QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
                 background-color: #ecf0f1; /* Similar to window background when disabled */
                 color: #95a5a6;
                 border: 1px solid #dcdcdc;
             }}

        """)
        # --- Set Object Names for Styling ---
        # Make sure you set these object names when creating the widgets
        self.patient_name_label.setObjectName("PatientNameLabel")

        # *** Correction based on Traceback ***
        # The original code had 'self.visit_id_label'. The error suggests it doesn't exist,
        # but 'self.patient_id_label' might.
        # If you have a label specifically for the VISIT ID, find its actual variable name
        # (e.g., self.the_visit_id_label) and uncomment/modify the line below.
        # self.your_actual_visit_id_label_variable.setObjectName("VisitIDLabel") # Adjust this line!

        # Setting object name for patient_id_label based on error hint
        try:
            if hasattr(self, 'patient_id_label'): # Check if it exists before setting
                 self.patient_id_label.setObjectName("PatientIDLabel")
            else:
                 print("Warning: 'patient_id_label' not found during style application.")
        except Exception as e:
            print(f"Error setting object name for patient_id_label: {e}")


        # Action Buttons
        self.print_button.setObjectName("PrintButton")
        self.edit_button.setObjectName("EditButton")
        self.save_button.setObjectName("SaveButton")
        self.cancel_or_close_button.setObjectName("CancelCloseButton")

        # Add Item Buttons
        self.add_service_button.setObjectName("AddServiceButton")
        self.add_med_button.setObjectName("AddMedButton")

        # Financial Labels (If you have separate value labels)
        # Ensure these labels exist with these names in your __init__ or _setup_ui
        try:
            self.total_label.setObjectName("FinancialTotalLabel")
            self.paid_label.setObjectName("FinancialPaidLabel")
            self.due_label.setObjectName("FinancialDueLabel")
            self.total_value_label.setObjectName("FinancialValueTotal")
            self.paid_value_label.setObjectName("FinancialValuePaid")
            self.due_value_label.setObjectName("FinancialValueDue")
        except AttributeError as e:
             print(f"Warning: Financial label not found during style application: {e}. Check widget names.")
    


    def _connect_signals(self):
        """Connect widget signals to their respective slots."""
        # --- Connect Print Button ---
        self.print_button.clicked.connect(self._generate_visit_pdf)
        # --- End Connect Print Button ---

        # Existing Action Buttons
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        self.save_button.clicked.connect(self.save_changes)
        self.cancel_or_close_button.clicked.connect(self._handle_cancel_or_close)

        # Add Item Buttons
        self.add_service_button.clicked.connect(self.add_service_item)
        self.add_med_button.clicked.connect(self.add_prescription_item)

        # Combo Box Updates
        self.service_combo.currentIndexChanged.connect(self.update_service_price)
        self.med_combo.currentIndexChanged.connect(self.update_med_price)

        # Financial Input Update
        self.pay_due_input.textChanged.connect(self._update_financial_summary)

        # Connect table row click event
        self.services_table.cellClicked.connect(self._handle_table_row_click)
        self.prescriptions_table.cellClicked.connect(self._handle_table_row_click)

    def _handle_table_row_click(self, row, column):
        """Handle table row click event to change row color."""
        table = self.sender()
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                item = table.item(r, c)
                if item:
                    if r == row:
                        item.setBackground(QColor('#3498db'))  # Blue color for selected row
                        item.setForeground(QColor('white'))
                    else:
                        item.setBackground(QColor('transparent'))  # Reset other rows
                        item.setForeground(QColor('black'))

    # --- Data Population and Update Methods ---

    def _populate_fields(self):
        """Populate the main form fields with loaded visit data."""
        if not self.model.visit_data: return

        # Visit Info
        visit_num = self.model.visit_data.get('visit_number', 'N/A')
        visit_date_str = self.model.visit_data.get('visit_date', '')
        self.visit_details_label.setText(f"Visit No. <b>{visit_num}</b>")
        visit_date = QDate.fromString(visit_date_str, "yyyy-MM-dd")
        self.visit_date_input.setDate(visit_date if visit_date.isValid() else QDate.currentDate())
        self.visit_notes_input.setPlainText(self.model.visit_data.get('notes', ''))
        self.lab_results_input.setPlainText(self.model.visit_data.get('lab_results', ''))

        # Financials (initial state before edits)
        self._update_financial_summary()

    def _populate_services_table(self):
        """Populate the services table with existing and new services."""
        self.services_table.setRowCount(0)  # Clear existing rows
        all_services = self.model.services + self.model.new_services
        for service in all_services:
            self._add_row_to_table(self.services_table, service, is_service=True)

    def _populate_prescriptions_table(self):
        """Populate the prescriptions table with existing and new prescriptions."""
        self.prescriptions_table.setRowCount(0)  # Clear existing rows
        all_prescriptions = self.model.prescriptions + self.model.new_prescriptions
        for prescription in all_prescriptions:
            self._add_row_to_table(self.prescriptions_table, prescription, is_service=False)

    def _add_row_to_table(self, table, item_data, is_service):
        """Helper to add a single row to either table."""
        row_position = table.rowCount()
        table.insertRow(row_position)

        is_new = 'new' in item_data  # Check if it's a newly added item not yet saved

        # Determine unique ID and display data based on type (service/prescription)
        if is_service:
            item_id_key = 'visit_service_id' if not is_new else 'temp_id'  # Use temp_id for new items if needed
            item_id = item_data.get(item_id_key, item_data.get('service_id'))  # Fallback to service_id
            name = item_data.get('service_name', 'N/A')
            col2_val = str(item_data.get('tooth_number', ''))
            notes = item_data.get('notes', '')
            remove_tooltip = "Remove this service"
        else:  # Prescription
            item_id_key = 'visit_prescription_id' if not is_new else 'temp_id'
            item_id = item_data.get(item_id_key, item_data.get('medication_id'))  # Fallback to medication_id
            name = item_data.get('medication_name', 'N/A')
            col2_val = str(item_data.get('quantity', ''))
            notes = item_data.get('instructions', '')
            remove_tooltip = "Remove this prescription"

        price = item_data.get('price_charged', 0.0)

        # Create items
        id_item = QTableWidgetItem(str(item_id))
        id_item.setData(Qt.ItemDataRole.UserRole, is_new)  # Store 'is_new' status in the item
        name_item = QTableWidgetItem(name)
        col2_item = QTableWidgetItem(col2_val)
        price_item = QTableWidgetItem(f"{price:.2f}")
        notes_item = QTableWidgetItem(notes)

        # Set alignment for numeric columns
        col2_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Add items to table
        table.setItem(row_position, 0, id_item)  # Hidden ID
        table.setItem(row_position, 1, name_item)  # Service/Medication Name
        table.setItem(row_position, 2, col2_item)  # Tooth # / Qty
        table.setItem(row_position, 3, price_item)  # Price
        table.setItem(row_position, 4, notes_item)  # Notes / Instructions

        # Add Remove Button
        remove_button = QPushButton(
            qta.icon('fa5s.trash-alt', color=self.style().standardPalette().color(QPalette.ColorRole.PlaceholderText)),
            ""  # Add empty text argument
        )
        remove_button.setObjectName("RemoveItemButton")
        remove_button.setToolTip(remove_tooltip)
        remove_button.setFlat(True)  # Make it look integrated
        remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_button.setProperty("row", row_position)
        remove_button.setProperty("is_service", is_service)
        remove_button.clicked.connect(lambda checked, b=remove_button: self.remove_item(b))
        remove_button.setEnabled(self.is_editing)  # Only enabled in edit mode

        # Center the button in the cell
        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.addWidget(remove_button)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        table.setCellWidget(row_position, 5, cell_widget)  # Action column

    def _update_financial_summary(self):
        """Recalculate and update the financial summary labels."""
        total_services = 0.0
        for row in range(self.services_table.rowCount()):
            price_item = self.services_table.item(row, 3)
            if price_item:
                try:
                    total_services += float(price_item.text())
                except ValueError:
                    pass  # Ignore non-numeric values

        total_prescriptions = 0.0
        for row in range(self.prescriptions_table.rowCount()):
            price_item = self.prescriptions_table.item(row, 3)
            if price_item:
                try:
                    total_prescriptions += float(price_item.text())
                except ValueError:
                    pass

        current_total = total_services + total_prescriptions
        self.total_amount_label.setText(f"<b>{current_total:.2f}</b>")

        # Use initial paid amount from loaded data, don't recalculate from label
        initial_paid = float(self.model.visit_data.get('paid_amount', 0.0)) if self.model.visit_data else 0.0
        self.paid_amount_label.setText(f"{initial_paid:.2f}")

        initial_due = max(0.0, current_total - initial_paid)
        self.due_amount_label.setText(f"<font color='red'><b>{initial_due:.2f}</b></font>")  # Show initial due in red

        # Calculate remaining due based on 'Pay Now' input
        pay_now_text = self.pay_due_input.text().strip()
        pay_now_amount = 0.0
        if self.is_editing and pay_now_text:  # Only consider Pay Now in edit mode
            try:
                pay_now_amount = float(pay_now_text)
            except ValueError:
                pass  # Invalid input, treat as 0

        remaining_due = max(0.0, initial_due - pay_now_amount)
        self.updated_due_label.setText(f"<font color='red'><b>{remaining_due:.2f}</b></font>")

    # --- Edit Mode and State Management ---

    def toggle_edit_mode(self):
        """Switch between view and edit modes."""
        self.is_editing = not self.is_editing
        self._update_view_mode()

    def _update_view_mode(self):
        """Update UI elements based on the current edit state."""
        editing = self.is_editing

        # Toggle read-only state for inputs
        self.visit_date_input.setReadOnly(not editing)
        self.visit_notes_input.setReadOnly(not editing)
        self.lab_results_input.setReadOnly(not editing)
        self.pay_due_input.setEnabled(editing)

        # Show/hide add item sections and action buttons
        self.add_service_widget.setVisible(editing)
        self.add_prescription_widget.setVisible(editing)
        self.edit_button.setVisible(not editing)
        self.save_button.setVisible(editing)

        # Update Cancel/Close button text and connection
        self.cancel_or_close_button.setText(" Cancel" if editing else " Close")
        icon_name = 'fa5s.times' if editing else 'fa5s.times-circle'
        self.cancel_or_close_button.setIcon(qta.icon(icon_name, color='white'))
        tooltip = "Discard changes and exit edit mode" if editing else "Close this visit detail view"
        self.cancel_or_close_button.setToolTip(tooltip)

        # Enable/disable remove buttons in tables
        self._set_table_buttons_enabled(self.services_table, editing)
        self._set_table_buttons_enabled(self.prescriptions_table, editing)

        # Clear "Pay Now" field when exiting edit mode (either save or cancel)
        if not editing:
            self.pay_due_input.clear()

        # Refresh financials display
        self._update_financial_summary()

        # Set focus appropriately
        if editing:
            self.visit_date_input.setFocus()
        else:
            self.edit_button.setFocus()

    def _set_table_buttons_enabled(self, table, enabled):
        """Enable or disable all 'Remove' buttons in a table."""
        for row in range(table.rowCount()):
            cell_widget = table.cellWidget(row, 5)  # Action column
            if cell_widget:
                # Find the button within the cell widget's layout
                button = cell_widget.layout().itemAt(0).widget()
                if isinstance(button, QPushButton):
                    button.setEnabled(enabled)

    def cancel_edit(self):
        """Cancel editing mode, discarding changes."""
        # Optional: Ask for confirmation if changes were made
        if self.model.new_services or self.model.new_prescriptions or self.pay_due_input.text():
            reply = QMessageBox.question(self, "Cancel Edit",
                                         "Discard unsaved changes and exit edit mode?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        # Reload original data to revert fields
        self.model._load_initial_data()  # Reloads original data
        self._populate_fields()  # Repopulate form fields
        self._populate_services_table()  # Repopulate tables (clears new items)
        self._populate_prescriptions_table()

        self.is_editing = False  # Set state back to viewing
        self._update_view_mode()  # Update UI to reflect viewing state

    def close_view(self):
        """Close the window, emit the closed signal, and re-enable the parent's scrollbar if applicable."""
        parent = self.parent()
        if isinstance(parent, QScrollArea):  # Check if parent is a scrollable widget
            parent.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.closed.emit()  # Emit the closed signal
        self.close()  # Close the current window

    def _handle_cancel_or_close(self):
        """Handles the action of the Cancel/Close button based on mode."""
        if self.is_editing:
            self.cancel_edit()
        else:
            self.close_view()

    # --- PDF Generation ---

    def _generate_visit_pdf(self):
        """Generates a PDF report for the current visit."""
        # Assuming your PDF generation logic is in pdf/visit_pdf.py
        # and you have a function generate_visit_pdf(visit_data, patient_data, services, prescriptions)
        try:
            from pdf.visit_pdf import generate_visit_pdf # Ensure this import works

            # Gather all necessary data
            visit_data = self.model.visit_data
            patient_data = self.model.patient_data
            # Combine existing and newly added items (if in edit mode, might want to save first or print current state)
            # For printing, typically you print the *saved* state.
            # If you want to print the current state *including unsaved items*, adjust data gathering:
            # current_services = self.model.services + self.model.new_services
            # current_prescriptions = self.model.prescriptions + self.model.new_prescriptions
            
            # Using only saved data for this example:
            services = self.model.services
            prescriptions = self.model.prescriptions

            if not visit_data or not patient_data:
                QMessageBox.warning(self, "Data Error", "Cannot generate PDF. Visit or patient data is missing.")
                return

            # Suggest a filename (optional, can be handled in generate_visit_pdf)
            suggested_filename = f"Visit_{visit_data.get('visit_id', 'N_A')}_Patient_{patient_data.get('patient_id', 'N_A')}.pdf"

            # Call the PDF generation function
            pdf_path = generate_visit_pdf(visit_data, patient_data, services, prescriptions, suggested_filename)

            if pdf_path:
                # Ask user if they want to open the PDF (optional)
                reply = QMessageBox.information(self, "PDF Generated",
                                                f"PDF report saved successfully:\n{pdf_path}\n\nDo you want to open it?",
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                                QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.Yes:
                    import os
                    import webbrowser
                    try:
                        # Use webbrowser for cross-platform opening
                        webbrowser.open(f"file:///{os.path.abspath(pdf_path)}")
                    except Exception as e:
                        QMessageBox.critical(self, "Open Error", f"Could not open PDF file.\nError: {e}")
            # Error handling within generate_visit_pdf should show messages

        except ImportError:
             QMessageBox.critical(self, "Error", "Could not find the PDF generation module (pdf/visit_pdf.py).")
        except Exception as e:
            QMessageBox.critical(self, "PDF Generation Failed", f"An unexpected error occurred during PDF generation:\n{e}")

    # --- Item Adding/Removing Logic ---

    def update_service_price(self):
        """Update the price input when a service is selected."""
        service_name = self.service_combo.currentText()
        if service_name and service_name in self.model.available_services:
            self.service_price_input.setValue(self.model.available_services[service_name]['price'])
        elif not service_name:  # Clear price if blank option selected
            self.service_price_input.setValue(0.0)

    def update_med_price(self):
        """Update the price input when a medication is selected."""
        med_name = self.med_combo.currentText()
        if med_name and med_name in self.model.available_medications:
            self.med_price_input.setValue(self.model.available_medications[med_name]['price'])
        elif not med_name:  # Clear price if blank option selected
            self.med_price_input.setValue(0.0)

    def add_service_item(self):
        """Add a new service item to the temporary list and table."""
        service_name = self.service_combo.currentText()
        if not service_name:
            QMessageBox.warning(self, "Selection Error", "Please select a service.")
            return

        service_id = self.model.available_services[service_name]['id']
        tooth_str = self.service_tooth_input.text().strip()
        # Allow non-numeric tooth "numbers" (e.g., "ULQ", "Mandible") if needed
        tooth_info = tooth_str if tooth_str else None
        price = self.service_price_input.value()
        notes = self.service_notes_input.text().strip()  # Using QLineEdit now

        # Basic validation (e.g., price > 0?)
        if price <= 0:
            reply = QMessageBox.question(self, "Confirm Price", "The service price is zero. Add anyway?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No: return

        item_data = {
            'service_id': service_id,  # Needed for saving
            'service_name': service_name,
            'tooth_number': tooth_info,  # Renamed for clarity
            'price_charged': price,
            'notes': notes,
            'new': True,  # Mark as unsaved
            'temp_id': f"new_s_{len(self.model.new_services)}"  # Temporary unique ID for removal before saving
        }
        self.model.new_services.append(item_data)
        self._add_row_to_table(self.services_table, item_data, is_service=True)
        self._update_financial_summary()

        # Clear input fields for next entry
        self.service_combo.setCurrentIndex(0)  # Reset combo to blank
        self.service_tooth_input.clear()
        self.service_notes_input.clear()
        self.service_price_input.setValue(0.0)
        self.service_combo.setFocus()  # Focus back on the first input

    def add_prescription_item(self):
        """Add a new prescription item to the temporary list and table."""
        med_name = self.med_combo.currentText()
        if not med_name:
            QMessageBox.warning(self, "Selection Error", "Please select a medication.")
            return

        med_id = self.model.available_medications[med_name]['id']
        quantity = self.med_qty_input.value()
        price = self.med_price_input.value()  # Price per unit or total? Assume total here. Adjust if needed.
        instructions = self.med_instr_input.text().strip()  # Using QLineEdit now

        # Basic validation
        if quantity <= 0:
            QMessageBox.warning(self, "Input Error", "Quantity must be greater than zero.")
            return
        if price < 0:
            QMessageBox.warning(self, "Input Error", "Price cannot be negative.")
            return

        item_data = {
            'medication_id': med_id,  # Needed for saving
            'medication_name': med_name,
            'quantity': quantity,
            'price_charged': price,  # Total price for the quantity
            'instructions': instructions,
            'new': True,  # Mark as unsaved
            'temp_id': f"new_p_{len(self.model.new_prescriptions)}"  # Temporary unique ID
        }
        self.model.new_prescriptions.append(item_data)
        self._add_row_to_table(self.prescriptions_table, item_data, is_service=False)
        self._update_financial_summary()

        # Clear input fields
        self.med_combo.setCurrentIndex(0)  # Reset combo to blank
        self.med_qty_input.setValue(1)
        self.med_instr_input.clear()
        self.med_price_input.setValue(0.0)
        self.med_combo.setFocus()

    def remove_item(self, button):
        """Remove an item (service or prescription) from the table and list."""
        row_to_remove = button.property("row")
        is_service = button.property("is_service")
        if row_to_remove is None: return  # Safety check

        table = self.services_table if is_service else self.prescriptions_table
        id_item = table.item(row_to_remove, 0)  # ID is in column 0
        if not id_item: return  # Safety check

        item_id_str = id_item.text()
        is_new = id_item.data(Qt.ItemDataRole.UserRole)  # Retrieve 'is_new' status

        item_name = table.item(row_to_remove, 1).text()  # Get name for confirmation

        confirm_msg = f"Remove '{item_name}'?"
        reply = QMessageBox.question(self, "Confirm Removal", confirm_msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if is_new:
                # Remove from the temporary 'new' list based on temp_id or unique data
                if is_service:
                    self.model.new_services = [s for s in self.model.new_services if s.get('temp_id') != item_id_str]
                else:
                    self.model.new_prescriptions = [p for p in self.model.new_prescriptions if p.get('temp_id') != item_id_str]
                # No database action needed yet
                table.removeRow(row_to_remove)  # Remove directly
                self._update_row_properties(table, row_to_remove)
                self._update_financial_summary()

            else:  # Item exists in the database
                # Call database function to remove
                try:
                    item_id = int(item_id_str)
                    success = False
                    if is_service:
                        # Find the original service in self.services to mark for removal or remove directly?
                        # Current approach: Remove immediately via DB call.
                        success = self.model.remove_service_from_visit(item_id)
                        if success:  # Also remove from the local 'original' list
                            self.model.services = [s for s in self.model.services if s.get('visit_service_id') != item_id]
                    else:
                        success = self.model.remove_prescription_from_visit(item_id)
                        if success:  # Also remove from the local 'original' list
                            self.model.prescriptions = [p for p in self.model.prescriptions if p.get('visit_prescription_id') != item_id]

                    if success:
                        table.removeRow(row_to_remove)
                        self._update_row_properties(table, row_to_remove)
                        self._update_financial_summary()
                        # No need to emit visit_updated here, only on full save
                    else:
                        QMessageBox.critical(self, "Database Error", f"Failed to remove the item (ID: {item_id}) from the database.")
                except ValueError:
                    QMessageBox.critical(self, "Error", f"Invalid item ID found: {item_id_str}")
                except Exception as e:
                    QMessageBox.critical(self, "Database Error", f"An error occurred during removal:\n{e}")

    def _update_row_properties(self, table, removed_row_index):
        """Update the 'row' property of buttons in subsequent rows after a removal."""
        for row in range(removed_row_index, table.rowCount()):
            cell_widget = table.cellWidget(row, 5)  # Action column
            if cell_widget:
                # Find the button within the cell widget's layout
                button = cell_widget.layout().itemAt(0).widget()
                if isinstance(button, QPushButton):
                    button.setProperty("row", row)  # Update the row index stored in the button

    # --- Saving Logic ---

    def save_changes(self):
        """Validate and save all changes to the database."""
        # 1. Validate Inputs (Example: Ensure date is valid, etc.)
        visit_date = self.visit_date_input.date()
        if not visit_date.isValid():
            QMessageBox.warning(self, "Validation Error", "Please enter a valid visit date.")
            self.visit_date_input.setFocus()
            return

        # 2. Prepare Data
        visit_date_str = visit_date.toString("yyyy-MM-dd")
        notes = self.visit_notes_input.toPlainText().strip()
        lab_results = self.lab_results_input.toPlainText().strip()

        # Calculate final paid amount
        initial_paid = float(self.model.visit_data.get('paid_amount', 0.0))
        pay_now_text = self.pay_due_input.text().strip()
        pay_now_amount = 0.0
        if pay_now_text:
            try:
                pay_now_amount = float(pay_now_text)
                if pay_now_amount < 0: raise ValueError("Payment cannot be negative")
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", f"Invalid amount entered in 'Pay Now':\n{e}")
                self.pay_due_input.setFocus()
                return

        final_paid_amount = initial_paid + pay_now_amount

        # --- Database Operations ---
        db_errors = []

        # Update Visit Details (Date, Notes, Lab Results)
        try:
            if not self.model.update_visit_details(visit_date_str, notes, lab_results):
                db_errors.append("Failed to update visit details.")
        except Exception as e:
            db_errors.append(f"Error updating visit details: {e}")

        # Add New Services
        added_service_ids = []
        for service in self.model.new_services:
            try:
                # Make sure all necessary keys exist
                sid = service['service_id']
                tooth = service.get('tooth_number')  # Use .get for optional fields
                price = service['price_charged']
                s_notes = service.get('notes', '')

                new_visit_service_id = self.model.add_service_to_visit(sid, tooth, price, s_notes)
                if new_visit_service_id:
                    service['visit_service_id'] = new_visit_service_id  # Store the real ID
                    service.pop('new', None)  # Remove 'new' marker
                    service.pop('temp_id', None)
                    added_service_ids.append(service)  # Keep track of successfully added ones
                else:
                    db_errors.append(f"Failed to add service: {service.get('service_name', 'Unknown')}")
            except Exception as e:
                db_errors.append(f"Error adding service {service.get('service_name', 'Unknown')}: {e}")

        # Add New Prescriptions
        added_prescription_ids = []
        for prescription in self.model.new_prescriptions:
            try:
                mid = prescription['medication_id']
                qty = prescription['quantity']
                price = prescription['price_charged']
                instr = prescription.get('instructions', '')

                new_visit_presc_id = self.model.add_prescription_to_visit(mid, qty, price, instr)
                if new_visit_presc_id:
                    prescription['visit_prescription_id'] = new_visit_presc_id
                    prescription.pop('new', None)
                    prescription.pop('temp_id', None)
                    added_prescription_ids.append(prescription)
                else:
                    db_errors.append(f"Failed to add prescription: {prescription.get('medication_name', 'Unknown')}")
            except Exception as e:
                db_errors.append(f"Error adding prescription {prescription.get('medication_name', 'Unknown')}: {e}")

        # Update Payment (only if payment was made or details changed)
        try:
            if not self.model.update_visit_payment(final_paid_amount):
                db_errors.append("Failed to update visit payment information.")
            else:
                # Update local data if payment update was successful
                if self.model.visit_data: self.model.visit_data['paid_amount'] = final_paid_amount

        except Exception as e:
            db_errors.append(f"Error updating payment: {e}")

        # --- Post-Save Actions ---
        if not db_errors:
            # Success: Merge new items into main lists, clear new lists
            self.model.services.extend(added_service_ids)
            self.model.prescriptions.extend(added_prescription_ids)
            self.model.new_services.clear()
            self.model.new_prescriptions.clear()

            QMessageBox.information(self, "Success", f"Visit ID {self.model.visit_id} updated successfully.")
            self.visit_updated.emit(self.model.patient_id)  # Notify parent/main window
            self.is_editing = False
            # Reload data to ensure consistency, especially calculated fields like due_amount
            self.model._load_initial_data()
            self._populate_fields()
            self._populate_services_table()
            self._populate_prescriptions_table()
            self._update_view_mode()  # Switch back to view mode
        else:
            # Handle Errors: Show accumulated errors
            # Rollback? Complex. For now, just report errors. User might need to fix and save again.
            # Keep items in new_services/new_prescriptions lists if they failed to add.
            # Remove successfully added items from the 'new' lists
            self.model.new_services = [s for s in self.model.new_services if 'visit_service_id' not in s]
            self.model.new_prescriptions = [p for p in self.model.new_prescriptions if 'visit_prescription_id' not in p]
            # Refresh tables to reflect partial success/failures
            self._populate_services_table()
            self._populate_prescriptions_table()
            # Update summary based on potentially partial changes
            self._update_financial_summary()

            error_message = "Errors occurred during saving:\n\n" + "\n".join(f"- {e}" for e in db_errors)
            QMessageBox.critical(self, "Save Error", error_message)
            # Stay in edit mode for user to correct

# --- Main Execution / Test ---
if __name__ == '__main__':

    # --- Test Data Setup (Only if DB modules not found) ---
    if not DATABASE_AVAILABLE:
        print("Running with Mock Data Setup...")
        # No explicit setup needed here as mock functions provide data on demand

    elif DATABASE_AVAILABLE:
        print("Attempting Real Database Setup for Test...")
        try:
            from database.schema import initialize_database
            from database.data_manager import add_patient, add_visit, add_service, add_medication  # Keep specific adds
            initialize_database()
            # Add minimal test data if it doesn't exist
            if not get_patient_by_id(4):
                print("Adding test patient 4...")
                add_patient("Test VisitDetail", "Tester", "Other", 31, "1 Detail St", "555-DETAIL", "Needs details")
            if not get_service_by_id(1):
                print("Adding test service 1...")
                add_service("Cleaning", "Teeth Cleaning", 50.0)
            if not get_service_by_id(2):
                print("Adding test service 2...")
                add_service("Filling", "Composite Filling", 120.0)
            # Add medication if function exists and medication not present
            try:
                if not get_medication_by_id(101):  # Assuming get_medication_by_id exists
                    print("Adding test medication 101...")
                    add_medication("Painkiller A", "Generic Pain Relief", 5.0)
            except NameError: pass  # Ignore if get_medication_by_id doesn't exist
            except Exception as e_med: print(f"Error checking/adding medication: {e_med}")

            if not get_visit_by_id(9):
                print("Adding test visit 9...")
                visit_id_test = add_visit(4, "2024-04-01", "Initial consultation", "X-rays taken")
                if visit_id_test:
                    print(f"Test visit created with ID: {visit_id_test}")
                    # Add a service to the newly created visit
                    add_service_to_visit(visit_id_test, 1, None, 50.0, "Standard cleaning")
                    TEST_VISIT_ID = visit_id_test
                else:
                    print("Failed to add test visit.")
                    sys.exit(1)
            else:
                TEST_VISIT_ID = 9  # Use existing visit 9
                # Ensure visit 9 has at least one service for testing display
                if not get_services_for_visit(9):
                    add_service_to_visit(9, 1, None, 50.0, "Standard cleaning - Added for test")

        except ImportError:
            print("Database schema/manager not fully available for test setup.")
            sys.exit(1)
        except Exception as e:
            print(f"Error setting up DB for test: {e}")
            # Don't exit if DB exists but setup fails, maybe data is already there
            if 'TEST_VISIT_ID' not in locals(): TEST_VISIT_ID = 9  # Fallback

    else:  # Should not happen based on initial check, but as fallback
        TEST_VISIT_ID = 9

    # --- Run Application ---
    app = QApplication(sys.argv)
    # app.setStyle('Fusion')  # Fusion style is clean, but stylesheet overrides most

    # Ensure a patient ID is available for the test visit
    test_patient_id = 4  # Assuming visit 9 belongs to patient 4

    print(f"Attempting to load VisitDetailWindow for Visit ID: {TEST_VISIT_ID}, Patient ID: {test_patient_id}")
    window = VisitDetailWindow(visit_id=TEST_VISIT_ID, patient_id=test_patient_id)

    # If window failed to initialize (e.g., data load error), exit
    if not window.isEnabled():
        print("Window initialization failed (likely data loading error). Exiting.")
        sys.exit(1)

    window.show()
    sys.exit(app.exec())
