# dental_clinic/ui/main_window.py
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem, QAbstractItemView,
                             QLineEdit, QMessageBox, QApplication, QStackedLayout)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta
from pathlib import Path

# Adjust import path
try:
    from database.data_manager import get_all_patients, delete_patient
    from .add_patient_dialog import AddPatientDialog
    from .view_edit_patient_window import ViewEditPatientWindow
except ImportError as e:
     print(f"Error importing UI/DB modules in main_window.py: {e}")
     print("Ensure you are running from the project root directory (dental_clinic).")
     sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
     try:
        from database.data_manager import get_all_patients, delete_patient
        from ui.add_patient_dialog import AddPatientDialog
        from ui.view_edit_patient_window import ViewEditPatientWindow
     except ImportError:
        print("Failed to import necessary modules even after path adjustment.")
        sys.exit(1)

class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dental Clinic Management")
        self.setGeometry(100, 100, 800, 600)

        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QStackedLayout(central_widget)

        # --- Main Layout ---
        main_layout_widget = QWidget()
        main_layout = QVBoxLayout(main_layout_widget)

        # --- Toolbar / Header Area ---
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Search Patient (Name/Phone):"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter name or phone...")
        self.search_input.textChanged.connect(self.filter_patients)
        header_layout.addWidget(self.search_input)

        # Add Patient Button
        self.add_button = QPushButton(qta.icon('fa5s.user-plus'), " Add Patient")
        self.add_button.clicked.connect(self.open_add_patient_dialog)
        header_layout.addWidget(self.add_button)

        # View/Edit Patient Button
        self.view_edit_button = QPushButton(qta.icon('fa5s.user-edit'), " View/Edit Patient")
        self.view_edit_button.clicked.connect(self.open_view_edit_patient_window)
        self.view_edit_button.setEnabled(False) # Disabled until a patient is selected
        header_layout.addWidget(self.view_edit_button)

        # Delete Patient Button
        self.delete_button = QPushButton(qta.icon('fa5s.user-minus'), " Delete Patient")
        self.delete_button.clicked.connect(self.delete_selected_patient)
        self.delete_button.setEnabled(False) # Disabled until a patient is selected
        header_layout.addWidget(self.delete_button)

        main_layout.addLayout(header_layout)

        # --- Patient Table ---
        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(5) # ID, Name, Father's Name, Phone, Address
        self.patient_table.setHorizontalHeaderLabels(["ID", "Name", "Father's Name", "Phone Number", "Address"])
        self.patient_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Read-only table
        self.patient_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # Select whole row
        self.patient_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Only one selection
        self.patient_table.verticalHeader().setVisible(False) # Hide row numbers
        self.patient_table.horizontalHeader().setStretchLastSection(True) # Make last column stretch
        # Adjust column widths (example)
        self.patient_table.setColumnWidth(0, 50)  # ID
        self.patient_table.setColumnWidth(1, 150) # Name
        self.patient_table.setColumnWidth(2, 150) # Father's Name
        self.patient_table.setColumnWidth(3, 120) # Phone
        # Address will stretch

        self.patient_table.itemSelectionChanged.connect(self.update_button_states)

        main_layout.addWidget(self.patient_table)

        # Add main layout widget to stacked layout
        self.main_layout.addWidget(main_layout_widget)
        self.main_layout.setCurrentWidget(main_layout_widget)

        # --- Load Initial Data ---
        self.load_patients()

    def load_patients(self, search_term=""):
        """Load patients from DB and populate the table."""
        self.patient_table.setRowCount(0) # Clear table
        patients = get_all_patients(search_term)

        if patients is None:
            QMessageBox.critical(self, "Database Error", "Could not retrieve patient list.")
            return

        self.patient_table.setRowCount(len(patients))
        for row, patient in enumerate(patients):
            patient_id = patient.get('patient_id', '')
            name = patient.get('name', '')
            fname = patient.get('father_name', '')
            phone = patient.get('phone_number', '')
            address = patient.get('address', '')

            # Store patient_id in the first column's item data
            id_item = QTableWidgetItem(str(patient_id))
            id_item.setData(Qt.ItemDataRole.UserRole, patient_id) # Store ID for later retrieval

            self.patient_table.setItem(row, 0, id_item)
            self.patient_table.setItem(row, 1, QTableWidgetItem(name))
            self.patient_table.setItem(row, 2, QTableWidgetItem(fname))
            self.patient_table.setItem(row, 3, QTableWidgetItem(phone))
            self.patient_table.setItem(row, 4, QTableWidgetItem(address))

        self.update_button_states() # Update buttons after loading

    def filter_patients(self):
        """Filter patient list based on search input."""
        search_term = self.search_input.text().strip()
        self.load_patients(search_term)

    def update_button_states(self):
        """Enable/disable buttons based on table selection."""
        selected_items = self.patient_table.selectedItems()
        is_patient_selected = bool(selected_items)
        self.view_edit_button.setEnabled(is_patient_selected)
        self.delete_button.setEnabled(is_patient_selected)

    def get_selected_patient_id(self):
        """Helper to get the ID of the currently selected patient."""
        selected_rows = self.patient_table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            id_item = self.patient_table.item(selected_row, 0) # ID is in column 0
            if id_item:
                return id_item.data(Qt.ItemDataRole.UserRole) # Retrieve stored ID
        return None

    def open_add_patient_dialog(self):
        """Open the dialog to add a new patient."""
        dialog = AddPatientDialog(self)
        dialog.patient_added.connect(self.load_patients) # Refresh table on success
        dialog.exec() # Show modally

    def open_view_edit_patient_window(self):
        """Open the window to view/edit the selected patient."""
        patient_id = self.get_selected_patient_id()
        if patient_id is None:
            QMessageBox.warning(self, "Selection Error", "Please select a patient from the table.")
            return

        # Create the view/edit widget
        self.view_edit_widget = ViewEditPatientWindow(patient_id, self)
        self.view_edit_widget.patient_updated.connect(self.load_patients) # Refresh list on update
        self.view_edit_widget.closed_signal.connect(self.on_view_edit_closed) # Track when closed

        # Add the view/edit widget to the stacked layout
        self.main_layout.addWidget(self.view_edit_widget)
        self.main_layout.setCurrentWidget(self.view_edit_widget)

    def on_view_edit_closed(self):
        """Callback when the view/edit window is closed."""
        # Remove the view/edit widget from the stacked layout
        self.main_layout.removeWidget(self.view_edit_widget)
        self.view_edit_widget.deleteLater()
        self.view_edit_widget = None

        # Show the main layout again
        self.main_layout.setCurrentIndex(0)

    def delete_selected_patient(self):
        """Delete the patient selected in the table."""
        patient_id = self.get_selected_patient_id()
        if patient_id is None:
            QMessageBox.warning(self, "Selection Error", "Please select a patient to delete.")
            return

        # Get patient name for confirmation message
        selected_row = self.patient_table.selectionModel().selectedRows()[0].row()
        name_item = self.patient_table.item(selected_row, 1)
        patient_name = name_item.text() if name_item else f"ID: {patient_id}"

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete patient '{patient_name}'?\n"
                                     "This will also delete all associated visits.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success = delete_patient(patient_id)
            if success is True:
                QMessageBox.information(self, "Success", f"Patient '{patient_name}' deleted successfully.")
                self.load_patients(self.search_input.text().strip()) # Refresh table
            elif success is False: # Integrity error or other known failure
                 QMessageBox.critical(self, "Deletion Failed", f"Could not delete patient '{patient_name}'. There might be related records preventing deletion (check service/medication usage if CASCADE wasn't fully effective or applicable).")
            else: # None - general error
                QMessageBox.critical(self, "Database Error", f"An error occurred while deleting patient '{patient_name}'.")

# --- Testing Block ---
if __name__ == '__main__':
    print("Attempting to initialize database for MainWindow test...")
    try:
        # Need schema to initialize db if it doesn't exist
        from database.schema import initialize_database
        if not initialize_database():
             print("Database initialization failed. Main window test may not function correctly.")
        else:
            print("Database initialized/verified successfully.")
    except ImportError as e:
        print(f"Could not import initialize_database: {e}")
        # Decide whether to proceed or exit

    app = QApplication(sys.argv)
    # Set fusion style for a modern look (optional)
    # app.setStyle("Fusion")
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())