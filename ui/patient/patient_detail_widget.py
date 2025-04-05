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
    """Widget to display patient details and manage their visits with a modern UI/UX."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_patient_id = None
        self.patient_data = None
        self.visit_list_data = []
        self.add_visit_widget = None
        self.visit_detail_widget = None  # Added for VisitDetailWindow

        self.setStyleSheet("""
            QWidget {
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                background-color: #f5f6fa;
                color: #333;
                border-radius: 8px;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 10px;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
            }
            QLabel {
                padding: 5px;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # Stacked layout for switching views
        self.stacked_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # Patient and Visits Widget
        self.patient_and_visits_widget = QWidget()
        self.patient_and_visits_layout = QVBoxLayout(self.patient_and_visits_widget)
        self.patient_and_visits_layout.setSpacing(15)

        # Patient Info Section
        self.patient_info_group = QGroupBox("Patient Information")
        self.patient_info_layout = QVBoxLayout(self.patient_info_group)

        top_row_layout = QHBoxLayout()
        self.patient_details_layout = QFormLayout()
        self.patient_details_layout.setSpacing(10)
        self.name_label = QLabel("N/A")
        self.fname_label = QLabel("N/A")
        self.age_label = QLabel("N/A")
        self.phone_label = QLabel("N/A")
        self.address_label = QLabel("N/A")
        self.address_label.setWordWrap(True)
        self.patient_details_layout.addRow("<b>Name:</b>", self.name_label)
        self.patient_details_layout.addRow("<b>Father's Name:</b>", self.fname_label)
        self.patient_details_layout.addRow("<b>Age:</b>", self.age_label)
        self.patient_details_layout.addRow("<b>Phone:</b>", self.phone_label)
        self.patient_details_layout.addRow("<b>Address:</b>", self.address_label)

        self.edit_patient_button = QPushButton(qta.icon('fa5s.edit', color='white'), "Edit Patient")
        self.edit_patient_button.setToolTip("Edit patient details")
        self.edit_patient_button.clicked.connect(self.open_edit_patient_window)
        self.edit_patient_button.setEnabled(False)

        top_row_layout.addLayout(self.patient_details_layout, 1)
        top_row_layout.addWidget(self.edit_patient_button, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self.patient_info_layout.addLayout(top_row_layout)
        self.patient_and_visits_layout.addWidget(self.patient_info_group)

        # Visits Section
        self.visits_group = QGroupBox("Patient Visits")
        self.visits_layout = QVBoxLayout(self.visits_group)

        self.visits_list_widget = QListWidget()
        self.visits_list_widget.setAlternatingRowColors(True)
        self.visits_list_widget.itemDoubleClicked.connect(self.open_visit_detail_window)
        self.visits_layout.addWidget(self.visits_list_widget)

        self.add_visit_button = QPushButton(qta.icon('fa5s.plus-circle', color='white'), "Add New Visit")
        self.add_visit_button.setToolTip("Add a new visit")
        self.add_visit_button.clicked.connect(self.show_add_visit_form)
        self.add_visit_button.setEnabled(False)
        self.visits_layout.addWidget(self.add_visit_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.patient_and_visits_layout.addWidget(self.visits_group)
        self.patient_and_visits_layout.addStretch()

        self.stacked_layout.addWidget(self.patient_and_visits_widget)

        self.clear_details()

    def load_patient(self, patient_id):
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

            if self.add_visit_widget is None:
                self.add_visit_widget = AddEditVisitWindow(patient_id=self.current_patient_id, parent=self)
                self.add_visit_widget.visit_saved.connect(self.handle_visit_saved)
                self.add_visit_widget.cancelled.connect(self.hide_add_visit_form)
                self.stacked_layout.addWidget(self.add_visit_widget)

            self.load_visits()
        else:
            self.clear_details()
            QMessageBox.warning(self, "Load Error", f"Could not find patient data for ID: {patient_id}")

    def clear_details(self):
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

        if self.add_visit_widget is not None:
            self.stacked_layout.removeWidget(self.add_visit_widget)
            self.add_visit_widget.deleteLater()
            self.add_visit_widget = None

        if self.visit_detail_widget is not None:
            self.stacked_layout.removeWidget(self.visit_detail_widget)
            self.visit_detail_widget.deleteLater()
            self.visit_detail_widget = None

    def load_visits(self):
        self.visits_list_widget.clear()
        if not self.current_patient_id:
            self.visits_list_widget.addItem("No patient selected.")
            return

        self.visit_list_data = get_patient_visits(self.current_patient_id)

        if self.visit_list_data is None:
            self.visits_list_widget.addItem("Error loading visits.")
            QMessageBox.critical(self, "Database Error", "Failed to retrieve patient visits.")
        elif not self.visit_list_data:
            self.visits_list_widget.addItem("No visits found for this patient.")
        else:
            for visit in self.visit_list_data:
                visit_id = visit.get('visit_id')
                visit_date = visit.get('visit_date', 'N/A')
                total = visit.get('total_amount', 0.0)
                due = visit.get('due_amount', 0.0)
                visit_number = visit.get('visit_number', 'N/A')
                item_text = f"Visit No. {visit_number} on {visit_date} - Total: {total:.2f}, Due: {due:.2f}"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, visit_id)
                self.visits_list_widget.addItem(list_item)

    def open_edit_patient_window(self):
        if not self.current_patient_id:
            QMessageBox.warning(self, "No Patient", "Please select a patient first.")
            return

        dialog = PatientEditWindow(patient_id=self.current_patient_id, parent=self)
        dialog.patient_updated.connect(self.handle_patient_updated)
        dialog.exec()

    def handle_patient_updated(self, updated_patient_id):
        if updated_patient_id == self.current_patient_id:
            self.load_patient(self.current_patient_id)

    def show_add_visit_form(self):
        if not self.current_patient_id:
            QMessageBox.warning(self, "No Patient", "Please select a patient first.")
            return

        if self.add_visit_widget is None:
            self.add_visit_widget = AddEditVisitWindow(patient_id=self.current_patient_id, parent=self)
            self.add_visit_widget.visit_saved.connect(self.handle_visit_saved)
            self.add_visit_widget.cancelled.connect(self.hide_add_visit_form)
            self.stacked_layout.addWidget(self.add_visit_widget)

        self.add_visit_widget.clear_form()
        self.stacked_layout.setCurrentIndex(1)

    def hide_add_visit_form(self):
        self.stacked_layout.setCurrentIndex(0)
        self.load_visits()

    def open_visit_detail_window(self, item):
        """Shows the visit detail view in the stacked layout."""
        visit_id = item.data(Qt.ItemDataRole.UserRole)
        if visit_id:
            # Check if visit_detail_widget exists and has a different visit_id
            if self.visit_detail_widget is None or self.visit_detail_widget.visit_id != visit_id:
                if self.visit_detail_widget is not None:  # Clean up existing widget if it exists
                    self.stacked_layout.removeWidget(self.visit_detail_widget)
                    self.visit_detail_widget.deleteLater()
                self.visit_detail_widget = VisitDetailWindow(visit_id=visit_id, patient_id=self.current_patient_id, parent=self)
                self.visit_detail_widget.visit_updated.connect(self.handle_visit_updated)
                self.visit_detail_widget.closed.connect(self.hide_visit_detail)
                self.stacked_layout.addWidget(self.visit_detail_widget)
            self.stacked_layout.setCurrentWidget(self.visit_detail_widget)
        else:
            print("Error: Could not get visit ID from list item.")

    def handle_visit_saved(self, patient_id):
        """Called when AddEditVisitWindow signals a new visit is saved."""
        if patient_id == self.current_patient_id:
            self.hide_add_visit_form()

    def handle_visit_updated(self, patient_id):
        """Called when VisitDetailWindow signals an update."""
        if patient_id == self.current_patient_id:
            self.load_visits()

    def hide_visit_detail(self):
        """Return to patient details view."""
        self.stacked_layout.setCurrentIndex(0)
        self.load_visits()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    try:
        from database.schema import initialize_database
        from database.data_manager import add_patient, add_visit
        initialize_database()
        if not get_patient_by_id(1):
            add_patient("Test DetailWidget", "Tester", "Male", 50, "1 Detail St", "555-WIDGET", "Needs displaying")
    except Exception as e:
        print(f"Error setting up DB for test: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    main_win = QMainWindow()
    main_win.setWindowTitle("Patient Detail Widget Test")
    main_win.setGeometry(100, 100, 800, 600)
    main_win.setStyleSheet("QMainWindow { background-color: #f5f6fa; }")

    detail_widget = PatientDetailWidget()

    test_load_button = QPushButton(qta.icon('fa5s.user-plus', color='white'), "Load Patient 1")
    test_load_button.clicked.connect(lambda: detail_widget.load_patient(1))

    central_container = QWidget()
    container_layout = QVBoxLayout(central_container)
    container_layout.addWidget(test_load_button)
    container_layout.addWidget(detail_widget)

    main_win.setCentralWidget(central_container)
    main_win.show()

    sys.exit(app.exec())