# ui/services/services_ui.py
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
    add_service, get_all_services, get_service_by_id, 
    update_service, delete_service
)

class ServiceDialog(QDialog):
    """Dialog for adding or editing a service"""
    
    def __init__(self, parent=None, service_id=None):
        super().__init__(parent)
        self.service_id = service_id
        self.service_data = None
        
        if service_id:
            self.setWindowTitle("Edit Service")
            # Get service data
            self.service_data = get_service_by_id(service_id)
            if not self.service_data:
                QMessageBox.critical(self, "Error", f"Could not find service with ID {service_id}")
                self.reject()
                return
        else:
            self.setWindowTitle("Add New Service")
        
        self.setup_ui()
        
        # If editing, populate fields
        if self.service_data:
            self.name_edit.setText(self.service_data.get('name', ''))
            self.description_edit.setPlainText(self.service_data.get('description', ''))
            self.price_edit.setValue(float(self.service_data.get('default_price', 0.0)))
            self.active_checkbox.setChecked(bool(self.service_data.get('is_active', 1)))
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter service name")
        layout.addRow("Name:", self.name_edit)
        
        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter service description")
        self.description_edit.setMaximumHeight(100)
        layout.addRow("Description:", self.description_edit)
        
        # Price field
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setRange(0, 1000000)
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
            QMessageBox.warning(self, "Input Error", "Service name cannot be empty.")
            return
        
        description = self.description_edit.toPlainText().strip()
        price = self.price_edit.value()
        is_active = self.active_checkbox.isChecked()
        
        success = False
        if self.service_id:
            # Update existing service
            success = update_service(
                self.service_id, name, description, price, is_active
            )
            message = f"Service '{name}' updated successfully!" if success else "Failed to update service."
        else:
            # Add new service
            new_id = add_service(name, description, price)
            success = bool(new_id)
            message = f"Service '{name}' added successfully!" if success else "Failed to add service."
        
        if success:
            QMessageBox.information(self, "Success", message)
            super().accept()
        else:
            QMessageBox.critical(self, "Error", message)


class ServicesManagementWidget(QWidget):
    """Widget for managing dental services"""
    
    service_updated = pyqtSignal()  # Signal to notify other components of changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_services()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Services Management")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search services...")
        self.search_edit.textChanged.connect(self.load_services)
        search_icon = qta.icon('fa5s.search')
        self.search_edit.addAction(search_icon, QLineEdit.ActionPosition.LeadingPosition)
        header_layout.addWidget(self.search_edit, 1)
        
        main_layout.addLayout(header_layout)
        
        # Table for displaying services
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Price", "Active"])
        self.services_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.services_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.services_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.services_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.services_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.services_table.verticalHeader().setVisible(False)
        self.services_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        main_layout.addWidget(self.services_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Service")
        self.add_button.setIcon(qta.icon('fa5s.plus'))
        self.add_button.clicked.connect(self.add_service)
        
        self.edit_button = QPushButton("Edit Service")
        self.edit_button.setIcon(qta.icon('fa5s.edit'))
        self.edit_button.clicked.connect(self.edit_service)
        
        self.delete_button = QPushButton("Delete Service")
        self.delete_button.setIcon(qta.icon('fa5s.trash'))
        self.delete_button.clicked.connect(self.delete_service)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setIcon(qta.icon('fa5s.sync'))
        self.refresh_button.clicked.connect(self.load_services)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_services(self):
        """Load services from database and populate table"""
        search_term = self.search_edit.text().strip()
        services = get_all_services(active_only=False)
        
        # Filter by search term if provided
        if search_term:
            services = [s for s in services if search_term.lower() in s['name'].lower() or 
                        (s['description'] and search_term.lower() in s['description'].lower())]
        
        self.services_table.setRowCount(0)  # Clear table
        
        for row, service in enumerate(services):
            self.services_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(service['service_id']))
            id_item.setData(Qt.ItemDataRole.UserRole, service['service_id'])
            self.services_table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(service['name'])
            self.services_table.setItem(row, 1, name_item)
            
            # Description
            desc_item = QTableWidgetItem(service['description'] if service['description'] else "")
            self.services_table.setItem(row, 2, desc_item)
            
            # Price
            price_item = QTableWidgetItem(f"${service['default_price']:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.services_table.setItem(row, 3, price_item)
            
            # Status
            status_item = QTableWidgetItem("Yes" if service['is_active'] else "No")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.services_table.setItem(row, 4, status_item)
    
    def get_selected_service_id(self):
        """Get the ID of the selected service"""
        selected_items = self.services_table.selectedItems()
        if not selected_items:
            return None
        
        selected_row = selected_items[0].row()
        id_item = self.services_table.item(selected_row, 0)
        return id_item.data(Qt.ItemDataRole.UserRole)
    
    def add_service(self):
        """Open dialog to add a new service"""
        dialog = ServiceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_services()
            self.service_updated.emit()
    
    def edit_service(self):
        """Edit the selected service"""
        service_id = self.get_selected_service_id()
        if not service_id:
            QMessageBox.warning(self, "Selection Required", "Please select a service to edit.")
            return
        
        dialog = ServiceDialog(self, service_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_services()
            self.service_updated.emit()
    
    def delete_service(self):
        """Delete the selected service"""
        service_id = self.get_selected_service_id()
        if not service_id:
            QMessageBox.warning(self, "Selection Required", "Please select a service to delete.")
            return
        
        # Confirm deletion
        service = get_service_by_id(service_id)
        if not service:
            QMessageBox.critical(self, "Error", "Service not found.")
            return
        
        confirm = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to delete the service '{service['name']}'?\n\n"
            "This action cannot be undone, and may fail if the service is used in patient visits.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success = delete_service(service_id)
            if success:
                QMessageBox.information(self, "Success", f"Service '{service['name']}' deleted successfully!")
                self.load_services()
                self.service_updated.emit()
            else:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Could not delete service '{service['name']}'. It may be used in patient visits."
                )


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ServicesManagementWidget()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())