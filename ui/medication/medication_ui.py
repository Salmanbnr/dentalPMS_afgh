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
    QDialog, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from database.data_manager import (
    add_medication, get_all_medications, get_medication_by_id, 
    update_medication, delete_medication
)

class MedicationDialog(QDialog):
    """Dialog for adding or editing a medication"""
    
    def __init__(self, parent=None, medication_id=None):
        super().__init__(parent)
        self.medication_id = medication_id
        self.medication_data = None
        
        if medication_id:
            self.setWindowTitle("Edit Medication")
            # Get medication data
            self.medication_data = get_medication_by_id(medication_id)
            if not self.medication_data:
                QMessageBox.critical(self, "Error", f"Could not find medication with ID {medication_id}")
                self.reject()
                return
        else:
            self.setWindowTitle("Add New Medication")
        
        self.setup_ui()
        
        # If editing, populate fields
        if self.medication_data:
            self.name_edit.setText(self.medication_data.get('name', ''))
            self.description_edit.setPlainText(self.medication_data.get('description', ''))
            self.price_edit.setValue(float(self.medication_data.get('default_price', 0.0)))
            self.active_checkbox.setChecked(bool(self.medication_data.get('is_active', 1)))
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter medication name")
        layout.addRow("Name:", self.name_edit)
        
        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter medication description (e.g., dosage, form)")
        self.description_edit.setMaximumHeight(100)
        layout.addRow("Description:", self.description_edit)
        
        # Price field
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setRange(0, 100000)
        self.price_edit.setDecimals(2)
        self.price_edit.setSingleStep(10)
        layout.addRow("Default Price:", self.price_edit)
        
        # Active checkbox
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)
        layout.addRow("Status:", self.active_checkbox)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                           QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
        
        self.setLayout(layout)
        self.resize(400, 300)
    
    def accept(self):
        # Validate inputs
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Medication name cannot be empty.")
            return
        
        description = self.description_edit.toPlainText().strip()
        price = self.price_edit.value()
        is_active = self.active_checkbox.isChecked()
        
        success = False
        if self.medication_id:
            # Update existing medication
            success = update_medication(
                self.medication_id, name, description, price, is_active
            )
            message = f"Medication '{name}' updated successfully!" if success else "Failed to update medication."
        else:
            # Add new medication
            new_id = add_medication(name, description, price)
            success = bool(new_id)
            message = f"Medication '{name}' added successfully!" if success else "Failed to add medication."
        
        if success:
            QMessageBox.information(self, "Success", message)
            super().accept()
        else:
            QMessageBox.critical(self, "Error", message)


class MedicationsManagementWidget(QWidget):
    """Widget for managing medications"""
    
    medication_updated = pyqtSignal()  # Signal to notify other components of changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_medications()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Medications Management")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search medications...")
        self.search_edit.textChanged.connect(self.load_medications)
        search_icon = qta.icon('fa5s.search')
        self.search_edit.addAction(search_icon, QLineEdit.ActionPosition.LeadingPosition)
        header_layout.addWidget(self.search_edit, 1)
        
        main_layout.addLayout(header_layout)
        
        # Table for displaying medications
        self.medications_table = QTableWidget()
        self.medications_table.setColumnCount(5)
        self.medications_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Price", "Active"])
        self.medications_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.medications_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.medications_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.medications_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.medications_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.medications_table.verticalHeader().setVisible(False)
        self.medications_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.medications_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        main_layout.addWidget(self.medications_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Medication")
        self.add_button.setIcon(qta.icon('fa5s.plus'))
        self.add_button.clicked.connect(self.add_medication)
        
        self.edit_button = QPushButton("Edit Medication")
        self.edit_button.setIcon(qta.icon('fa5s.edit'))
        self.edit_button.clicked.connect(self.edit_medication)
        
        self.delete_button = QPushButton("Delete Medication")
        self.delete_button.setIcon(qta.icon('fa5s.trash'))
        self.delete_button.clicked.connect(self.delete_medication)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setIcon(qta.icon('fa5s.sync'))
        self.refresh_button.clicked.connect(self.load_medications)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_medications(self):
        """Load medications from database and populate table"""
        search_term = self.search_edit.text().strip()
        medications = get_all_medications(active_only=False)
        
        # Filter by search term if provided
        if search_term:
            medications = [m for m in medications if search_term.lower() in m['name'].lower() or 
                           (m['description'] and search_term.lower() in m['description'].lower())]
        
        self.medications_table.setRowCount(0)  # Clear table
        
        for row, medication in enumerate(medications):
            self.medications_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(medication['medication_id']))
            id_item.setData(Qt.ItemDataRole.UserRole, medication['medication_id'])
            self.medications_table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(medication['name'])
            self.medications_table.setItem(row, 1, name_item)
            
            # Description
            desc_item = QTableWidgetItem(medication['description'] if medication['description'] else "")
            self.medications_table.setItem(row, 2, desc_item)
            
            # Price
            price_item = QTableWidgetItem(f"${medication['default_price']:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.medications_table.setItem(row, 3, price_item)
            
            # Status
            status_item = QTableWidgetItem("Yes" if medication['is_active'] else "No")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.medications_table.setItem(row, 4, status_item)
    
    def get_selected_medication_id(self):
        """Get the ID of the selected medication"""
        selected_items = self.medications_table.selectedItems()
        if not selected_items:
            return None
        
        selected_row = selected_items[0].row()
        id_item = self.medications_table.item(selected_row, 0)
        return id_item.data(Qt.ItemDataRole.UserRole)
    
    def add_medication(self):
        """Open dialog to add a new medication"""
        dialog = MedicationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_medications()
            self.medication_updated.emit()
    
    def edit_medication(self):
        """Edit the selected medication"""
        medication_id = self.get_selected_medication_id()
        if not medication_id:
            QMessageBox.warning(self, "Selection Required", "Please select a medication to edit.")
            return
        
        dialog = MedicationDialog(self, medication_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_medications()
            self.medication_updated.emit()
    
    def delete_medication(self):
        """Delete the selected medication"""
        medication_id = self.get_selected_medication_id()
        if not medication_id:
            QMessageBox.warning(self, "Selection Required", "Please select a medication to delete.")
            return
        
        # Confirm deletion
        medication = get_medication_by_id(medication_id)
        if not medication:
            QMessageBox.critical(self, "Error", "Medication not found.")
            return
        
        confirm = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to delete the medication '{medication['name']}'?\n\n"
            "This action cannot be undone, and may fail if the medication is used in patient prescriptions.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success = delete_medication(medication_id)
            if success:
                QMessageBox.information(self, "Success", f"Medication '{medication['name']}' deleted successfully!")
                self.load_medications()
                self.medication_updated.emit()
            else:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Could not delete medication '{medication['name']}'. It may be used in patient prescriptions."
                )


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MedicationsManagementWidget()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())