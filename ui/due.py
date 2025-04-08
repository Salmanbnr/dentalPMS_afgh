# ui/due.py

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QLabel,
    QHeaderView, QApplication, QMessageBox
)
# Import QTimer for live search debouncing
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
import qtawesome as qta

# Use absolute/relative imports based on your project structure
try:
    # Assumes 'ui' and 'model' are siblings in the project root
    from model import due_model
except ImportError:
    # Fallback if the structure is different or running directly
    # This might require adjusting sys.path if run standalone
    from pathlib import Path
    # Add project root to path - Adjust level as needed (../..)
    project_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(project_root))
    from model import due_model

class DuePatientsWidget(QWidget):
    """
    A widget to display patients with outstanding due amounts,
    including the count of visits contributing to the debt,
    and featuring live search functionality.
    """
    data_loaded = pyqtSignal()

    # Define debounce delay in milliseconds
    SEARCH_DEBOUNCE_MS = 350

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patients with Due Amounts")
        self.setGeometry(200, 200, 1000, 550) # Adjusted size slightly

        # Timer for live search debouncing
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(self.SEARCH_DEBOUNCE_MS)

        self._setup_ui()
        self._connect_signals()
        self.load_due_patients() # Load data initially

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Search Bar ---
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Live search by Patient ID, Name, or Phone...") # Updated placeholder
        self.search_input.setFixedHeight(30)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border-color: #5dade2;
            }
        """)

        # Search button kept for explicit action/accessibility, though live search is primary
        self.search_button = QPushButton()
        self.search_button.setIcon(qta.icon('fa5s.search', color='#3498db'))
        self.search_button.setToolTip("Search Patients Now")
        self.search_button.setFixedSize(30, 30)
        self.search_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)

        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(qta.icon('fa5s.sync-alt', color='#2ecc71'))
        self.refresh_button.setToolTip("Refresh List (Clear Search)")
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.setStyleSheet(self.search_button.styleSheet())

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button) # Keep button
        search_layout.addWidget(self.refresh_button)

        # --- Table ---
        self.due_table = QTableWidget()
        # *** Increased column count to 7 ***
        self.due_table.setColumnCount(7)
        self.due_table.setHorizontalHeaderLabels([
            "Patient ID", "Name", "Father's Name", "Phone Number",
            "Address", "Due Visits", "Total Due (PKR)" # Added "Due Visits"
        ])
        self.due_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.due_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.due_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.due_table.setAlternatingRowColors(True)
        self.due_table.verticalHeader().setVisible(False)
        self.due_table.setSortingEnabled(True)

        self.due_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdcdc;
                gridline-color: #e0e0e0;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #5dade2;
                color: white;
                padding: 5px;
                border: 1px solid #5dade2;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #aed6f1;
                color: black;
            }
            QTableWidget::item:focus {
                 border: 1px solid #aed6f1;
            }
            QTableView QTableCornerButton::section {
                 background-color: #5dade2;
                 border: 1px solid #5dade2;
            }
        """)

        # Adjust column widths - Added column 5 (Due Visits)
        header = self.due_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Patient ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)        # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)        # Father's Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Phone
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)        # Address
        # *** Set resize mode for new column 5 (Due Visits) ***
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Due Visits
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Total Due (was 5)

        # --- Status Bar ---
        self.status_label = QLabel("Loading data...")
        self.status_label.setFixedHeight(20)
        self.status_label.setStyleSheet("font-style: italic; color: #555;")

        # --- Assemble Layout ---
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.due_table)
        main_layout.addWidget(self.status_label)

    def _connect_signals(self):
        # *** Live search: Trigger timer on text changed ***
        self.search_input.textChanged.connect(self.search_timer.start)
        # *** When timer finishes, perform the actual search ***
        self.search_timer.timeout.connect(self._perform_search)

        # Keep explicit search button functional
        self.search_button.clicked.connect(self._perform_search)
        # Refresh button clears search and reloads
        self.refresh_button.clicked.connect(self.refresh_list)
        # No longer need returnPressed connection as textChanged handles it via timer
        # self.search_input.returnPressed.connect(self._perform_search)


    def _perform_search(self):
        """
        Called by the timer timeout or search button click.
        Reads the search input and triggers data loading.
        """
        search_term = self.search_input.text().strip()
        self.load_due_patients(search_term)

    def refresh_list(self):
        """Clears search input and reloads the full list."""
        self.search_input.clear() # This will trigger textChanged -> timer -> _perform_search
        # Optionally, call _perform_search directly if clearing shouldn't have a delay:
        # self._perform_search()

    def load_due_patients(self, search_term=""):
        """Fetches data from the model and populates the table."""
        self.status_label.setText(f"Searching..." if search_term else "Loading data...")
        QApplication.processEvents()

        patients_data = due_model.get_due_patients_details(search_term)

        self.due_table.setSortingEnabled(False)
        self.due_table.setRowCount(0)

        if patients_data is None:
            QMessageBox.critical(self, "Database Error", "Could not retrieve patient debt information. Please check logs.")
            self.status_label.setText("Error loading data.")
            return
        elif not patients_data:
            search_message_part = f' matching "{search_term}"' if search_term else ""
            self.status_label.setText(f"No patients found with due amounts{search_message_part}.")
        else:
            self.due_table.setRowCount(len(patients_data))
            total_overall_due = 0.0
            for row, patient in enumerate(patients_data):
                # --- Existing Columns ---
                patient_id_num = patient.get('patient_id')
                if patient_id_num is not None:
                    id_item = QTableWidgetItem()
                    id_item.setData(Qt.ItemDataRole.DisplayRole, str(patient_id_num))
                    id_item.setData(Qt.ItemDataRole.UserRole, int(patient_id_num))
                    self.due_table.setItem(row, 0, id_item)
                else:
                     self.due_table.setItem(row, 0, QTableWidgetItem("N/A"))

                name = QTableWidgetItem(str(patient.get('name', 'N/A')))
                father_name = QTableWidgetItem(str(patient.get('father_name', '')))
                phone = QTableWidgetItem(str(patient.get('phone_number', 'N/A')))
                address = QTableWidgetItem(str(patient.get('address', '')))

                # --- New Column: Due Visits Count ---
                due_visits_count_val = patient.get('due_visits_count', 0)
                due_visits_item = QTableWidgetItem()
                due_visits_item.setData(Qt.ItemDataRole.DisplayRole, str(due_visits_count_val))
                due_visits_item.setData(Qt.ItemDataRole.UserRole, int(due_visits_count_val)) # Store as int for sorting
                due_visits_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Center align count

                # --- Existing Column: Total Due ---
                total_due = patient.get('total_due', 0.0)
                total_overall_due += total_due
                due_item = QTableWidgetItem() # Format as currency
                due_item.setData(Qt.ItemDataRole.DisplayRole, f"{total_due:,.2f}")
                due_item.setData(Qt.ItemDataRole.UserRole, total_due) # Store float for sorting
                due_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                # --- Set Items (adjust column indices) ---
                self.due_table.setItem(row, 1, name)
                self.due_table.setItem(row, 2, father_name)
                self.due_table.setItem(row, 3, phone)
                self.due_table.setItem(row, 4, address)
                self.due_table.setItem(row, 5, due_visits_item) # New column at index 5
                self.due_table.setItem(row, 6, due_item)        # Old due column now at index 6

            self.status_label.setText(f"Found {len(patients_data)} patient(s) with a total due amount of PKR {total_overall_due:,.2f}.")

        self.due_table.setSortingEnabled(True)
        self.data_loaded.emit()


# --- Main execution block for testing ---
if __name__ == '__main__':
    # IMPORTANT: Ensure database setup and potentially add dummy data
    # as mentioned in the previous response.

    app = QApplication(sys.argv)
    try:
        app.setStyle("Fusion")
    except Exception as e:
        print(f"Could not set Fusion style: {e}")

    main_window = DuePatientsWidget()
    main_window.show()
    sys.exit(app.exec())