import sys
import os
from pathlib import Path

# Add project root to path to enable imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDoubleSpinBox, QCheckBox,
    QDialog, QDialogButtonBox, QFormLayout, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPalette, QColor
import qtawesome as qta

from database.data_manager import (
    add_medication, get_all_medications, get_medication_by_id, 
    update_medication, delete_medication
)

# Color constants
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

MEDICATION_PAGE_STYLESHEET = f"""
    /* Style the MedicationsManagementWidget itself */
    #MedicationsManagementWidget {{
        background-color: {COLOR_SECONDARY};
        padding: 15px;
    }}

    /* Header frame styling */
    #MedicationsManagementWidget #HeaderFrame {{
        border-bottom: 1px solid {COLOR_BORDER};
        padding-bottom: 10px;
    }}

    /* Input fields and buttons */
    #MedicationsManagementWidget QLineEdit, #MedicationsManagementWidget QTextEdit, #MedicationsManagementWidget QDoubleSpinBox {{
        padding: 8px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        font-size: 10pt;
        background-color: white;
    }}
    #MedicationsManagementWidget QPushButton {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border: none;
        padding: 8px 15px;
        border-radius: 4px;
        font-size: 10pt;
        min-width: 120px;
    }}
    #MedicationsManagementWidget QPushButton:hover {{
        background-color: {COLOR_HOVER};
    }}
    #MedicationsManagementWidget QPushButton:disabled {{
        background-color: #95a5a6;
        color: #ecf0f1;
    }}

    /* Table Styling */
    #MedicationsManagementWidget QTableWidget {{
        border: 1px solid {COLOR_BORDER};
        gridline-color: {COLOR_BORDER};
        font-size: 10pt;
        background-color: white;
    }}
    #MedicationsManagementWidget QHeaderView::section {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        padding: 6px;
        border: none;
        border-right: 1px solid {COLOR_BORDER};
        font-weight: bold;
    }}
    #MedicationsManagementWidget QHeaderView::section:last {{
        border-right: none;
    }}
    #MedicationsManagementWidget QTableWidget::item {{
        padding: 5px;
        color: {COLOR_TEXT_DARK};
    }}
    #MedicationsManagementWidget QTableWidget::item:selected {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
    }}
    #MedicationsManagementWidget QTableWidget::item:focus {{
        outline: none;
    }}

    /* Scroll Bars */
    #MedicationsManagementWidget QScrollBar:vertical {{
        border: none;
        background: {COLOR_SECONDARY};
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    #MedicationsManagementWidget QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}
    #MedicationsManagementWidget QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        background: none;
    }}
    #MedicationsManagementWidget QScrollBar:horizontal {{
        border: none;
        background: {COLOR_SECONDARY};
        height: 10px;
        margin: 0px 0px 0px 0px;
    }}
    #MedicationsManagementWidget QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER};
        min-width: 20px;
        border-radius: 5px;
    }}
    #MedicationsManagementWidget QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: none;
    }}
"""

class MedicationDialog(QDialog):
    """Dialog for adding or editing a medication with modern styling"""
    
    def __init__(self, parent=None, medication_id=None):
        super().__init__(parent)
        self.medication_id = medication_id
        self.medication_data = None
        
        if medication_id:
            self.setWindowTitle("Edit Medication")
            self.medication_data = get_medication_by_id(medication_id)
            if not self.medication_data:
                QMessageBox.critical(self, "Error", f"Could not find medication with ID {medication_id}")
                self.reject()
                return
        else:
            self.setWindowTitle("Add New Medication")
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_SECONDARY};
                border-radius: 8px;
                padding: 20px;
            }}
            QLineEdit, QTextEdit, QDoubleSpinBox {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                background-color: {COLOR_TEXT_LIGHT};
            }}
            QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {{
                border-color: {COLOR_ACCENT};
                outline: none;
            }}
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_TEXT_LIGHT};
                border-radius: 4px;
                padding: 8px 16px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLOR_HOVER};
            }}
        """)
        
        self.setup_ui()
        
        if self.medication_data:
            self.name_edit.setText(self.medication_data.get('name', ''))
            self.description_edit.setPlainText(self.medication_data.get('description', ''))
            self.price_edit.setValue(float(self.medication_data.get('default_price', 0.0)))
            self.active_checkbox.setChecked(bool(self.medication_data.get('is_active', 1)))
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter medication name")
        layout.addRow(QLabel("Name:"), self.name_edit)
        
        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter medication description (e.g., dosage, form)")
        self.description_edit.setMaximumHeight(120)
        layout.addRow(QLabel("Description:"), self.description_edit)
        
        # Price field
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setRange(0, 100000)
        self.price_edit.setDecimals(2)
        self.price_edit.setSingleStep(10)
        
        layout.addRow(QLabel("Default Price:"), self.price_edit)
        
        # Active checkbox
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)
        layout.addRow(QLabel("Status:"), self.active_checkbox)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                        QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
        
        self.resize(500, 400)
    
    def accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Medication name cannot be empty.")
            return
        
        description = self.description_edit.toPlainText().strip()
        price = self.price_edit.value()
        is_active = self.active_checkbox.isChecked()
        
        success = False
        if self.medication_id:
            success = update_medication(self.medication_id, name, description, price, is_active)
            message = f"Medication '{name}' updated successfully!" if success else "Failed to update medication."
        else:
            new_id = add_medication(name, description, price)
            success = bool(new_id)
            message = f"Medication '{name}' added successfully!" if success else "Failed to add medication."
        
        if success:
            QMessageBox.information(self, "Success", message)
            super().accept()
        else:
            QMessageBox.critical(self, "Error", message)

class MedicationsManagementWidget(QWidget):
    """Widget for managing medications with modern UI"""
    
    medication_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MedicationsManagementWidget")
        self.setStyleSheet(MEDICATION_PAGE_STYLESHEET)
        
        # Initialize action_buttons list
        self.action_buttons = []
        
        self.setup_ui()
        self.load_medications()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Heading "Medicine Management"
        heading_label = QLabel("Medicine Management")
        heading_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24pt;
                font-weight: bold;
                color: {COLOR_PRIMARY};
                margin-bottom: 15px;
            }}
        """)
        main_layout.addWidget(heading_label)
        
        # Header
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        search_icon = qta.icon('fa5s.search', color=COLOR_TEXT_DARK)
        search_label = QLabel()
        search_label.setPixmap(search_icon.pixmap(QSize(16, 16)))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search medications...")
        self.search_edit.textChanged.connect(self.load_medications)
        self.search_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_edit.setMinimumWidth(300)
        
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_edit, 1)
        header_layout.addStretch(1)
        
        buttons = [
            ("Add Medication", 'fa5s.plus', self.add_medication),
            ("Edit Medication", 'fa5s.edit', self.edit_medication),
            ("Delete Medication", 'fa5s.trash', self.delete_medication),
            ("Refresh", 'fa5s.sync', self.load_medications)
        ]
        
        for text, icon_name, callback in buttons:
            button = QPushButton(qta.icon(icon_name, color=COLOR_TEXT_LIGHT), f" {text}")
            button.clicked.connect(callback)
            header_layout.addWidget(button)
            # Store the buttons that need to be enabled/disabled
            if text in ["Edit Medication", "Delete Medication"]:
                self.action_buttons.append(button)
                button.setEnabled(False)  # Initially disabled
        
        main_layout.addWidget(header_frame)
        
        # Scroll Area for Medication Table
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Medication Table
        self.medications_table = QTableWidget()
        self.medications_table.setColumnCount(5)
        self.medications_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Price", "Active"])
        self.medications_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.medications_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.medications_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.medications_table.verticalHeader().setVisible(False)
        self.medications_table.horizontalHeader().setStretchLastSection(True)
        self.medications_table.setShowGrid(True)
        
        self.medications_table.setColumnWidth(0, 60)
        self.medications_table.setColumnWidth(1, 180)
        self.medications_table.setColumnWidth(2, 500)
        self.medications_table.setColumnWidth(3, 80)
        self.medications_table.setColumnWidth(4, 25)
        
        self.medications_table.itemSelectionChanged.connect(self.update_button_states)
        self.medications_table.itemDoubleClicked.connect(self.edit_medication)
        
        scroll_area.setWidget(self.medications_table)
        main_layout.addWidget(scroll_area)
    
    def load_medications(self):
        search_term = self.search_edit.text().strip()
        medications = get_all_medications(active_only=False)
        
        if search_term:
            medications = [m for m in medications if search_term.lower() in m['name'].lower() or 
                         (m['description'] and search_term.lower() in m['description'].lower())]
        
        self.medications_table.setRowCount(0)
        
        for row, medication in enumerate(medications):
            self.medications_table.insertRow(row)
            items = [
                str(medication['medication_id']),
                medication['name'],
                medication['description'] if medication['description'] else "",
                f"{medication['default_price']:.2f}",
                "Yes" if medication['is_active'] else "No"
            ]
            
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col == 0:  # ID
                    item.setData(Qt.ItemDataRole.UserRole, medication['medication_id'])
                if col in [3, 4]:  # Price and Status
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.medications_table.setItem(row, col, item)
    
    def update_button_states(self):
        """Enable/disable action buttons based on selection"""
        is_medication_selected = bool(self.medications_table.selectionModel().hasSelection())
        for button in self.action_buttons:
            button.setEnabled(is_medication_selected)
    
    def get_selected_medication_id(self):
        selected_rows = self.medications_table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            id_item = self.medications_table.item(selected_row, 0)
            if id_item:
                return id_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def add_medication(self):
        dialog = MedicationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_medications()
            self.medication_updated.emit()
    
    def edit_medication(self):
        medication_id = self.get_selected_medication_id()
        if not medication_id:
            QMessageBox.warning(self, "Selection Required", "Please select a medication to edit.")
            return
        dialog = MedicationDialog(self, medication_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_medications()
            self.medication_updated.emit()
    
    def delete_medication(self):
        medication_id = self.get_selected_medication_id()
        if not medication_id:
            QMessageBox.warning(self, "Selection Required", "Please select a medication to delete.")
            return
        
        medication = get_medication_by_id(medication_id)
        if not medication:
            QMessageBox.critical(self, "Error", "Medication not found.")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete",
                                   f"Are you sure you want to delete '{medication['name']}'?\n"
                                   "This action cannot be undone.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success = delete_medication(medication_id)
            if success:
                QMessageBox.information(self, "Success", f"Medication '{medication['name']}' deleted successfully!")
                self.load_medications()
                self.medication_updated.emit()
            else:
                QMessageBox.critical(self, "Error", "Could not delete medication. It may be in use.")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MedicationsManagementWidget()
    window.setWindowTitle("Medication Management System")
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())