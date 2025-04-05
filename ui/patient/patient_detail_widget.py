import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QMessageBox, QFormLayout, QGroupBox, QScrollArea,
                             QListWidget, QListWidgetItem, QSizePolicy, QStackedLayout)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
import qtawesome as qta
from pathlib import Path

# Use absolute imports assuming running from project root
try:
    from database.data_manager import get_patient_by_id, get_patient_visits
    from ui.patient.patient_edit_window import PatientEditWindow
    from ui.visit.add_edit_visit_window import AddEditVisitWindow
    from ui.visit.visit_detail_window import VisitDetailWindow
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from database.data_manager import get_patient_by_id, get_patient_visits
    from ui.patient.patient_edit_window import PatientEditWindow
    from ui.visit.add_edit_visit_window import AddEditVisitWindow
    from ui.visit.visit_detail_window import VisitDetailWindow

class PatientDetailWidget(QWidget):
    """Widget to display patient details and manage their visits."""
    # Define signals if needed, e.g., to notify main window of changes
    # patient_updated = pyqtSignal()
    # visit_added_or_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_patient_id = None
        self.patient_data = None
        self.visit_list_data = []  # Store basic visit info for the list
        self.add_visit_widget = None  # Will be created when patient is loaded

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Use spacing from parent layouts

        # Create a stacked layout to switch between patient details and add visit form
        self.stacked_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # --- First Page: Patient Info and Visits ---
        self.patient_and_visits_widget = QWidget()
        self.patient_and_visits_layout = QVBoxLayout(self.patient_and_visits_widget)

        # --- Top Section: Patient Info ---
        self.patient_info_group = QGroupBox("Patient Information")
        self.patient_info_layout = QVBoxLayout(self.patient_info_group)

        top_row_layout = QHBoxLayout()  # Layout for labels + edit button
        self.patient_details_layout = QFormLayout()  # Use form layout for alignment
        self.name_label = QLabel("N/A")
        self.fname_label = QLabel("N/A")
        self.age_label = QLabel("N/A")
        self.phone_label = QLabel("N/A")
        self.address_label = QLabel("N/A")
        self.address_label.setWordWrap(True)  # Allow address to wrap
        self.patient_details_layout.addRow("<b>Name:</b>", self.name_label)
        self.patient_details_layout.addRow("<b>Father's Name:</b>", self.fname_label)
        self.patient_details_layout.addRow("<b>Age:</b>", self.age_label)
        self.patient_details_layout.addRow("<b>Phone:</b>", self.phone_label)
        self.patient_details_layout.addRow("<b>Address:</b>", self.address_label)

        self.edit_patient_button = QPushButton(qta.icon('fa5s.edit'), "Edit Patient")
        self.edit_patient_button.setToolTip("Edit this patient's details")
        self.edit_patient_button.clicked.connect(self.open_edit_patient_window)
        self.edit_patient_button.setEnabled(False)  # Disabled until patient loaded
        self.edit_patient_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        top_row_layout.addLayout(self.patient_details_layout, 1)  # Form layout takes expanding space
        top_row_layout.addWidget(self.edit_patient_button, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)  # Button top-right

        self.patient_info_layout.addLayout(top_row_layout)
        self.patient_and_visits_layout.addWidget(self.patient_info_group)

        # --- Bottom Section: Visits ---
        self.visits_group = QGroupBox("Patient Visits")
        self.visits_layout = QVBoxLayout(self.visits_group)

        self.visits_list_widget = QListWidget()
        self.visits_list_widget.setAlternatingRowColors(True)
        self.visits_list_widget.itemDoubleClicked.connect(self.open_visit_detail_window)
        self.visits_layout.addWidget(self.visits_list_widget)

        self.add_visit_button = QPushButton(qta.icon('fa5s.plus-circle'), "Add New Visit")
        self.add_visit_button.setToolTip("Add a new visit record for this patient")
        self.add_visit_button.clicked.connect(self.show_add_visit_form)
        self.add_visit_button.setEnabled(False)  # Disabled until patient loaded
        self.visits_layout.addWidget(self.add_visit_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.patient_and_visits_layout.addWidget(self.visits_group)
        self.patient_and_visits_layout.addStretch()  # Push content upwards

        # Add the patient and visits widget to the stacked layout initially
        self.stacked_layout.addWidget(self.patient_and_visits_widget)

        self.clear_details()

    def load_patient(self, patient_id):
        """Loads and displays details for the given patient ID."""
        if patient_id is None:
            self.clear_details()
            return

        self.patient_data = get_patient_by_id(patient_id)

        if self.patient_data:
            self.current_patient_id = patient_id
            self.name_label.setText(self.patient_data.get('name', 'N/A'))
            self.fname_label.setText(self.patient_data.get('father_name', 'N/A'))
            self.age_label.setText(str(self.patient_data.get('age', 'N/A')))
            self.phone_label.setText(self.patient_data.get('phone_number', 'N/A'))
            self.address_label.setText(self.patient_data.get('address', 'N/A'))

            self.patient_info_group.setVisible(True)
            self.visits_group.setVisible(True)
            self.edit_patient_button.setEnabled(True)
            self.add_visit_button.setEnabled(True)

            # Create or update the add visit widget with the current patient_id
            if self.add_visit_widget is None:
                self.add_visit_widget = AddEditVisitWindow(patient_id=self.current_patient_id, parent=self)
                self.add_visit_widget.visit_saved.connect(self.handle_visit_saved)
                self.add_visit_widget.cancelled.connect(self.hide_add_visit_form)
                self.stacked_layout.addWidget(self.add_visit_widget)

            self.load_visits()  # Load visits after patient details are set
        else:
            self.clear_details()
            QMessageBox.warning(self, "Load Error", f"Could not find patient data for ID: {patient_id}")

    def clear_details(self):
        """Clears the displayed patient and visit information."""
        self.current_patient_id = None
        self.patient_data = None
        self.visit_list_data = []

        self.name_label.setText("N/A")
        self.fname_label.setText("N/A")
        self.age_label.setText("N/A")
        self.phone_label.setText("N/A")
        self.address_label.setText("N/A")

        self.visits_list_widget.clear()
        self.visits_list_widget.addItem("No patient selected.")

        self.edit_patient_button.setEnabled(False)
        self.add_visit_button.setEnabled(False)

        # Remove add_visit_widget if it exists to free resources
        if self.add_visit_widget is not None:
            self.stacked_layout.removeWidget(self.add_visit_widget)
            self.add_visit_widget.deleteLater()
            self.add_visit_widget = None

    def load_visits(self):
        """Loads the visit list for the current patient."""
        self.visits_list_widget.clear()
        if not self.current_patient_id:
            self.visits_list_widget.addItem("No patient selected.")
            return

        self.visit_list_data = get_patient_visits(self.current_patient_id)

        if self.visit_list_data is None:  # DB error
            self.visits_list_widget.addItem("Error loading visits.")
            QMessageBox.critical(self, "Database Error", "Failed to retrieve patient visits.")
        elif not self.visit_list_data:
            self.visits_list_widget.addItem("No visits found for this patient.")
        else:
            for visit in self.visit_list_data:
                # Format: Visit #ID on DATE - Total: X, Due: Y
                visit_id = visit.get('visit_id')
                visit_date = visit.get('visit_date', 'N/A')
                total = visit.get('total_amount', 0.0)
                due = visit.get('due_amount', 0.0)
                visit_number = visit.get('visit_number', 'N/A')
                item_text = f"Visit #{visit_number} on {visit_date}   (Total: {total:.2f}, Due: {due:.2f})"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, visit_id)  # Store visit_id in item data
                self.visits_list_widget.addItem(list_item)

    def open_edit_patient_window(self):
        """Opens the modal dialog to edit the current patient."""
        if not self.current_patient_id:
            QMessageBox.warning(self, "No Patient", "Please select a patient first.")
            return

        dialog = PatientEditWindow(patient_id=self.current_patient_id, parent=self)
        dialog.patient_updated.connect(self.handle_patient_updated)  # Connect signal
        dialog.exec()

    def handle_patient_updated(self, updated_patient_id):
        """Called when the edit dialog signals success. Reloads patient data."""
        if updated_patient_id == self.current_patient_id:
            print(f"PatientDetailWidget reloading data for patient ID: {updated_patient_id}")
            self.load_patient(self.current_patient_id)  # Reload displayed data

    def show_add_visit_form(self):
        """Shows the add visit form in the stacked layout."""
        if not self.current_patient_id:
            QMessageBox.warning(self, "No Patient", "Please select a patient first.")
            return

        if self.add_visit_widget is None:
            # This should not happen if load_patient was called, but handle it just in case
            self.add_visit_widget = AddEditVisitWindow(patient_id=self.current_patient_id, parent=self)
            self.add_visit_widget.visit_saved.connect(self.handle_visit_saved)
            self.add_visit_widget.cancelled.connect(self.hide_add_visit_form)
            self.stacked_layout.addWidget(self.add_visit_widget)

        self.add_visit_widget.clear_form()  # Reset form fields
        self.stacked_layout.setCurrentIndex(1)  # Switch to add visit form

    def hide_add_visit_form(self):
        """Hides the add visit form and returns to patient details."""
        self.stacked_layout.setCurrentIndex(0)  # Switch back to patient details
        self.load_visits()  # Refresh visits list

    def open_visit_detail_window(self, item):
        """Opens the modal dialog to view details of the selected visit."""
        visit_id = item.data(Qt.ItemDataRole.UserRole)
        if visit_id:
            dialog = VisitDetailWindow(visit_id=visit_id, parent=self)
            dialog.exec()
        else:
            print("Error: Could not get visit ID from list item.")

    def handle_visit_saved(self, patient_id_from_signal):
        """Called when AddEditVisitWindow signals success. Reloads visit list."""
        if patient_id_from_signal == self.current_patient_id:
            print(f"PatientDetailWidget reloading visits for patient ID: {patient_id_from_signal}")
            self.hide_add_visit_form()  # Return to patient details and refresh

# --- Testing Block ---
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    # Ensure DB setup
    try:
        from database.schema import initialize_database
        from database.data_manager import add_patient, add_visit  # Import necessary functions
        initialize_database()
        if not get_patient_by_id(1):
            add_patient("Test DetailWidget", "Tester", "Male", 50, "1 Detail St", "555-WIDGET", "Needs displaying")
        # Optionally add a visit for patient 1
        # if not get_patient_visits(1):
        #    add_visit(1, "2023-01-15", "Test visit for detail widget")
    except Exception as e:
        print(f"Error setting up DB for test: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)

    # Create a dummy main window to host the widget
    main_win = QMainWindow()
    main_win.setWindowTitle("Patient Detail Widget Test")
    main_win.setGeometry(100, 100, 500, 600)

    detail_widget = PatientDetailWidget()

    # Add a button to load a test patient
    test_load_button = QPushButton("Load Patient 1")
    def load_test_patient():
        detail_widget.load_patient(1)  # Load patient with ID 1
    test_load_button.clicked.connect(load_test_patient)

    central_container = QWidget()
    container_layout = QVBoxLayout(central_container)
    container_layout.addWidget(test_load_button)
    container_layout.addWidget(detail_widget)

    main_win.setCentralWidget(central_container)
    main_win.show()

    sys.exit(app.exec())