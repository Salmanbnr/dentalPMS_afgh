import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QLineEdit, QMessageBox, QApplication, QFrame, QSizePolicy, QMainWindow
)
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta
from pathlib import Path

# --- Determine Project Root (assuming main_window.py is in dental_clinic/ui/) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Adjust import paths relative to PROJECT_ROOT ---
# This allows imports like 'database.data_manager'
sys.path.insert(0, str(PROJECT_ROOT))
try:
    from database.data_manager import get_all_patients, delete_patient
    from ui.add_patient_dialog import AddPatientDialog
    from ui.view_edit_patient_window import PatientViewEditWindow
    from database.schema import initialize_database  # Keep for testing block if needed
except ImportError as e:
    print(f"Error importing UI/DB modules in main_window.py: {e}")
    print("Ensure the script is run where PROJECT_ROOT is correctly determined,")
    print("or that the necessary modules are importable.")
    # Attempt different relative import as fallback
    try:
        from ..database.data_manager import get_all_patients, delete_patient
        from .add_patient_dialog import AddPatientDialog
        from .view_edit_patient_window import PatientViewEditWindow
        from ..database.schema import initialize_database
    except ImportError:
        print("Failed to import necessary modules using relative paths.")
        sys.exit(1)

# --- Styling specific to the Patient List Page ---
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

PATIENT_PAGE_STYLESHEET = f"""
    /* Style the PatientListPage widget itself */
    #PatientListPage {{
        background-color: {COLOR_SECONDARY};
        /* Add padding if needed around the content, or let the dashboard handle it */
        /* padding: 15px; */
    }}

    /* Search bar and buttons within this page */
     #PatientListPage #HeaderFrame {{
        /* Add styling to the header frame if desired, e.g., background or border */
        /* border-bottom: 1px solid {COLOR_BORDER}; */
        /* padding-bottom: 10px; */
     }}

    #PatientListPage QLineEdit {{
        padding: 8px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        font-size: 10pt;
        background-color: white;
    }}
     #PatientListPage QPushButton {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border: none;
        padding: 8px 15px;
        border-radius: 4px;
        font-size: 10pt;
        min-width: 120px;
     }}
    #PatientListPage QPushButton:hover {{
        background-color: {COLOR_HOVER};
    }}
     #PatientListPage QPushButton:disabled {{
        background-color: #95a5a6;
        color: #ecf0f1;
     }}

    /* Table Styling */
    #PatientListPage QTableWidget {{
        border: 1px solid {COLOR_BORDER};
        gridline-color: {COLOR_BORDER};
        font-size: 10pt;
        background-color: white;
    }}
    #PatientListPage QHeaderView::section {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        padding: 6px;
        border: none;
        border-right: 1px solid {COLOR_BORDER};
        font-weight: bold;
    }}
    #PatientListPage QHeaderView::section:last {{
        border-right: none;
    }}
    #PatientListPage QTableWidget::item {{
        padding: 5px;
        color: {COLOR_TEXT_DARK};
    }}
    #PatientListPage QTableWidget::item:selected {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
    }}
     #PatientListPage QTableWidget::item:focus {{
        outline: none;
    }}
     #PatientListPage QScrollBar:vertical {{
        border: none;
        background: {COLOR_SECONDARY};
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    #PatientListPage QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}
    #PatientListPage QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        background: none;
    }}
     #PatientListPage QScrollBar:horizontal {{
        border: none;
        background: {COLOR_SECONDARY};
        height: 10px;
        margin: 0px 0px 0px 0px;
    }}
    #PatientListPage QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER};
        min-width: 20px;
        border-radius: 5px;
    }}
    #PatientListPage QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: none;
    }}
"""

class PatientListPage(QWidget):
    """Widget managing the patient list display and operations."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PatientListPage")  # For QSS styling
        self.setStyleSheet(PATIENT_PAGE_STYLESHEET)  # Apply styles to this widget

        # --- Keep track of the opened view/edit window ---
        self.view_edit_win_instance = None

        # --- Main Layout for this widget ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)  # Add padding within the page
        main_layout.setSpacing(15)

        # --- Toolbar / Header Area ---
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)  # No internal margins for layout
        header_layout.setSpacing(10)

        search_icon = qta.icon('fa5s.search', color=COLOR_TEXT_DARK)
        search_label = QLabel()
        search_label.setPixmap(search_icon.pixmap(QSize(16, 16)))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Patient (Name/Phone)...")
        self.search_input.textChanged.connect(self.filter_patients)

        # Enlarge the search bar horizontally
        self.search_input.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Horizontal policy: Expanding
            QSizePolicy.Policy.Fixed       # Vertical policy: Fixed
        )
        self.search_input.setMinimumWidth(300)  # Optional: Set a minimum width

        # Add widgets to the header layout
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 1)  # Add stretch factor to expand the search bar
        header_layout.addStretch(1)  # Push buttons to the right

        # Add Patient Button
        self.add_button = QPushButton(qta.icon('fa5s.user-plus', color=COLOR_TEXT_LIGHT), " Add Patient")
        self.add_button.clicked.connect(self.open_add_patient_dialog)
        header_layout.addWidget(self.add_button)

        # View/Edit Patient Button
        self.view_edit_button = QPushButton(qta.icon('fa5s.user-edit', color=COLOR_TEXT_LIGHT), " View/Edit")
        self.view_edit_button.clicked.connect(self.open_view_edit_patient_window)
        self.view_edit_button.setEnabled(False)
        header_layout.addWidget(self.view_edit_button)

        # Delete Patient Button
        self.delete_button = QPushButton(qta.icon('fa5s.user-minus', color=COLOR_TEXT_LIGHT), " Delete")
        self.delete_button.clicked.connect(self.delete_selected_patient)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)

        main_layout.addWidget(header_frame)  # Add the frame containing the header controls

        # --- Patient Table ---
        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(5)
        self.patient_table.setHorizontalHeaderLabels(["ID", "Name", "Father's Name", "Phone Number", "Address"])
        self.patient_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.patient_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.patient_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.patient_table.verticalHeader().setVisible(False)
        self.patient_table.horizontalHeader().setStretchLastSection(True)
        self.patient_table.setShowGrid(True)

        self.patient_table.setColumnWidth(0, 60)
        self.patient_table.setColumnWidth(1, 180)
        self.patient_table.setColumnWidth(2, 180)
        self.patient_table.setColumnWidth(3, 130)

        self.patient_table.itemSelectionChanged.connect(self.update_button_states)
        self.patient_table.itemDoubleClicked.connect(self.handle_double_click)

        main_layout.addWidget(self.patient_table)

        # --- Load Initial Data ---
        self.load_patients()

    def handle_double_click(self, item):
        if self.get_selected_patient_id() is not None:
            self.open_view_edit_patient_window()

    def load_patients(self, search_term=""):
        current_selection_id = self.get_selected_patient_id()
        self.patient_table.setRowCount(0)
        try:
            patients = get_all_patients(search_term)
        except Exception as e:
            QMessageBox.critical(self.window(), "Database Error", f"Could not retrieve patient list.\nError: {e}")
            patients = None

        if patients is None:
            return

        new_selection_row = -1
        self.patient_table.setRowCount(len(patients))
        for row, patient in enumerate(patients):
            patient_id = patient.get('patient_id', '')
            name = patient.get('name', '')
            fname = patient.get('father_name', '')
            phone = patient.get('phone_number', '')
            address = patient.get('address', '')

            id_item = QTableWidgetItem(str(patient_id))
            id_item.setData(Qt.ItemDataRole.UserRole, patient_id)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.patient_table.setItem(row, 0, id_item)
            self.patient_table.setItem(row, 1, QTableWidgetItem(name))
            self.patient_table.setItem(row, 2, QTableWidgetItem(fname))
            self.patient_table.setItem(row, 3, QTableWidgetItem(phone))
            self.patient_table.setItem(row, 4, QTableWidgetItem(address))

            if patient_id == current_selection_id:
                new_selection_row = row

        self.update_button_states()

        if new_selection_row != -1:
            self.patient_table.selectRow(new_selection_row)

    def filter_patients(self):
        search_term = self.search_input.text().strip()
        self.load_patients(search_term)

    def update_button_states(self):
        is_patient_selected = bool(self.patient_table.selectionModel().hasSelection())
        self.view_edit_button.setEnabled(is_patient_selected)
        self.delete_button.setEnabled(is_patient_selected)

    def get_selected_patient_id(self):
        selected_rows = self.patient_table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            id_item = self.patient_table.item(selected_row, 0)
            if id_item:
                return id_item.data(Qt.ItemDataRole.UserRole)
        return None

    def open_add_patient_dialog(self):
        dialog = AddPatientDialog(parent=self.window())
        dialog.patient_added.connect(lambda: self.load_patients(self.search_input.text().strip()))
        dialog.exec()

    def open_view_edit_patient_window(self):
        patient_id = self.get_selected_patient_id()
        if patient_id is None:
            QMessageBox.warning(self.window(), "Selection Error", "Please select a patient from the table.")
            return

        # Window management logic
        if self.view_edit_win_instance and self.view_edit_win_instance.isVisible():
            if self.view_edit_win_instance.current_patient_id == patient_id:
                self.view_edit_win_instance.activateWindow()
                self.view_edit_win_instance.raise_()
                return
            else:
                self.view_edit_win_instance.close()

        print(f"Opening View/Edit window for patient {patient_id}.")
        # Create as a widget within the stacked layout
        self.view_edit_win_instance = PatientViewEditWindow(patient_id=patient_id, parent=self)

        # Connect the signal after the instance is created
        self.view_edit_win_instance.back_button_clicked.connect(self.window().show_home_page)

        self.view_edit_win_instance.data_changed.connect(self.handle_data_changed)

        # Add the view/edit window to the stacked widget
        parent_main_window = self.window()
        if hasattr(parent_main_window, 'content_stack'):
            parent_main_window.content_stack.addWidget(self.view_edit_win_instance)
            parent_main_window.content_stack.setCurrentWidget(self.view_edit_win_instance)
        else:
            print("Error: Parent window does not have a content stack.")

    def handle_data_changed(self, patient_id):
        print(f"PatientListPage: Data changed signal received for patient {patient_id}. Reloading list.")
        self.load_patients(self.search_input.text().strip())

    def delete_selected_patient(self):
        patient_id = self.get_selected_patient_id()
        if patient_id is None:
            QMessageBox.warning(self.window(), "Selection Error", "Please select a patient to delete.")
            return

        selected_row = self.patient_table.selectionModel().selectedRows()[0].row()
        name_item = self.patient_table.item(selected_row, 1)
        patient_name = name_item.text() if name_item else f"ID: {patient_id}"

        reply = QMessageBox.question(self.window(), "Confirm Delete",
                                     f"Are you sure you want to delete patient '{patient_name}'?\n"
                                     "This will also delete all associated visits.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Close the detail window if it's open for the patient being deleted
            self.close_active_child_window(patient_id_to_match=patient_id)

            try:
                success = delete_patient(patient_id)
                if success is True:
                    QMessageBox.information(self.window(), "Success", f"Patient '{patient_name}' deleted successfully.")
                    self.load_patients(self.search_input.text().strip())
                elif success is False:
                    QMessageBox.critical(self.window(), "Deletion Failed", f"Could not delete patient '{patient_name}'. Related records might exist.")
                else:
                    QMessageBox.critical(self.window(), "Database Error", f"An error occurred while deleting patient '{patient_name}'.")
            except Exception as e:
                QMessageBox.critical(self.window(), "Deletion Error", f"An unexpected error occurred: {e}")

    def close_active_child_window(self, patient_id_to_match=None):
        """
        Closes the view/edit window if it's open.
        If patient_id_to_match is provided, only closes if the window's ID matches.
        """
        if self.view_edit_win_instance and self.view_edit_win_instance.isVisible():
            close_it = True
            if patient_id_to_match is not None:
                try:
                    # Check if the window instance has the expected ID
                    if (not hasattr(self.view_edit_win_instance, 'current_patient_id') or
                        self.view_edit_win_instance.current_patient_id != patient_id_to_match):
                        close_it = False
                except (AttributeError, RuntimeError):
                    self.view_edit_win_instance = None

            if close_it:
                print(f"PatientListPage: Closing active child view/edit window (Matching ID: {patient_id_to_match is not None}).")
                try:
                    self.view_edit_win_instance.close()
                except RuntimeError:
                    print("PatientListPage: Child window already deleted.")
                    self.view_edit_win_instance = None

# --- Testing Block (Optional: for testing PatientListPage in isolation) ---
if __name__ == '__main__':
    print("Attempting to initialize database for PatientListPage test...")
    if not initialize_database():
        print("Database initialization failed. Test may not function correctly.")
    else:
        print("Database initialized/verified successfully.")

    app = QApplication(sys.argv)

    test_widget = PatientListPage()
    # Since it's a QWidget, show it directly or embed in a basic QMainWindow for testing
    test_win = QMainWindow()
    test_win.setCentralWidget(test_widget)
    test_win.setWindowTitle("Patient List Page Test")
    test_win.setGeometry(100, 100, 900, 650)
    test_win.show()

    sys.exit(app.exec())
