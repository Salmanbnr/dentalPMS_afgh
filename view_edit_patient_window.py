# dental_clinic/ui/main_window.py
from email.mime import application
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                             QMessageBox, QSplitter, QFrame, QApplication)
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta
from pathlib import Path

# Use absolute imports assuming running from project root
try:
    from database.data_manager import get_all_patients, add_patient # Need add_patient for Add button
    from ui.patient.patient_detail_widget import PatientDetailWidget
    # Import add patient window if creating one (simple example here)
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from database.data_manager import get_all_patients, add_patient
    from ui.patient.patient_detail_widget import PatientDetailWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dental Clinic Management")
        self.setGeometry(50, 50, 900, 700) # Adjusted size
        self.setWindowIcon(qta.icon('fa5s.tooth'))

        # --- Central Widget and Main Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget) # Main layout is horizontal

        # --- Left Panel: Patient List and Search ---
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(5, 5, 5, 5)
        self.left_layout.setSpacing(5)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Patients (Name, Phone, ID)...")
        self.search_input.textChanged.connect(self.filter_patient_list)
        self.add_patient_button = QPushButton(qta.icon('fa5s.user-plus'), "") # Add Patient
        self.add_patient_button.setToolTip("Add New Patient")
        self.add_patient_button.clicked.connect(self.add_new_patient) # Simple add for now
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.add_patient_button)
        self.left_layout.addLayout(search_layout)

        self.patient_list_widget = QListWidget()
        self.patient_list_widget.currentItemChanged.connect(self.on_patient_selected)
        self.left_layout.addWidget(self.patient_list_widget)

        # --- Right Panel: Patient Details ---
        # This is where PatientDetailWidget will go
        self.detail_area = PatientDetailWidget() # Instantiate the detail widget

        # --- Splitter to make panels resizable ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.detail_area)
        self.splitter.setSizes([250, 650]) # Initial size ratio

        self.main_layout.addWidget(self.splitter)

        # --- Load Initial Data ---
        self.load_patient_list()


    def load_patient_list(self, search_term=""):
        """Loads patients into the list widget, optionally filtered."""
        self.patient_list_widget.clear()
        patients = get_all_patients(search_term)
        if patients is None:
            QMessageBox.critical(self, "Database Error", "Failed to load patient list.")
            self.patient_list_widget.addItem("Error loading patients.")
            return
        elif not patients:
             self.patient_list_widget.addItem("No patients found.")
             return

        for patient in patients:
             patient_id = patient.get('patient_id')
             name = patient.get('name', 'N/A')
             phone = patient.get('phone_number', 'N/A')
             item_text = f"{name} (ID: {patient_id}) - {phone}"
             list_item = QListWidgetItem(item_text)
             list_item.setData(Qt.ItemDataRole.UserRole, patient_id) # Store ID
             self.patient_list_widget.addItem(list_item)


    def filter_patient_list(self):
        """Filters the patient list based on the search input."""
        search_term = self.search_input.text().strip()
        self.load_patient_list(search_term)

    def on_patient_selected(self, current_item, previous_item):
        """Called when a patient is selected in the list."""
        if current_item:
            patient_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.detail_area.load_patient(patient_id)
        else:
            self.detail_area.clear_details()

    def add_new_patient(self):
        """Placeholder for adding a new patient. Opens a simple dialog or dedicated window."""
        # In a real app, open a dedicated AddPatientWindow similar to PatientEditWindow
        # For simplicity here, let's just add a default patient and reload
        name, ok = self.get_text_input("New Patient Name", "Enter the patient's full name:")
        if ok and name:
             fname, ok = self.get_text_input("Father's Name", "Enter father's name (optional):")
             # Get other fields similarly... (age, gender, phone etc.)
             # Using defaults for brevity in this example:
             new_id = add_patient(name, fname if ok else "", "Other", 30, "Default Address", "555-NEW", "New patient history")
             if new_id:
                 QMessageBox.information(self, "Success", f"Patient '{name}' added with ID: {new_id}")
                 self.load_patient_list() # Reload list
                 # Optionally select the new patient
                 items = self.patient_list_widget.findItems(str(new_id), Qt.MatchFlag.MatchContains)
                 if items: self.patient_list_widget.setCurrentItem(items[0])
             else:
                 QMessageBox.critical(self, "Error", "Failed to add the new patient.")


    def get_text_input(self, title, label):
        """Helper to get simple text input (replace with proper dialog)."""
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, label)
        return text, ok


# --- Entry Point ---
if __name__ == '__main__':
    # Ensure DB exists and is initialized
    try:
        from database.schema import initialize_database
        initialize_database()
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Decide if the app should exit or continue without a working DB
        # sys.exit(1) # Exit if DB is crucial

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())