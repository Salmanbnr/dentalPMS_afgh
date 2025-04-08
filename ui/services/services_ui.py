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
    add_service, get_all_services, get_service_by_id, 
    update_service, delete_service
)

# Color constants
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#ecf0f1"
COLOR_ACCENT = "#3498db"
COLOR_TEXT_LIGHT = "#ffffff"
COLOR_TEXT_DARK = "#34495e"
COLOR_BORDER = "#bdc3c7"
COLOR_HOVER = "#4a6fa5"

SERVICE_PAGE_STYLESHEET = f"""
    /* Style the ServicesManagementWidget itself */
    #ServicesManagementWidget {{
        background-color: {COLOR_SECONDARY};
        padding: 15px;
    }}

    /* Header frame styling */
    #ServicesManagementWidget #HeaderFrame {{
        border-bottom: 1px solid {COLOR_BORDER};
        padding-bottom: 10px;
    }}

    /* Input fields and buttons */
    #ServicesManagementWidget QLineEdit, #ServicesManagementWidget QTextEdit, #ServicesManagementWidget QDoubleSpinBox {{
        padding: 8px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        font-size: 10pt;
        background-color: white;
    }}
    #ServicesManagementWidget QPushButton {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
        border: none;
        padding: 8px 15px;
        border-radius: 4px;
        font-size: 10pt;
        min-width: 120px;
    }}
    #ServicesManagementWidget QPushButton:hover {{
        background-color: {COLOR_HOVER};
    }}
    #ServicesManagementWidget QPushButton:disabled {{
        background-color: #95a5a6;
        color: #ecf0f1;
    }}

    /* Table Styling */
    #ServicesManagementWidget QTableWidget {{
        border: 1px solid {COLOR_BORDER};
        gridline-color: {COLOR_BORDER};
        font-size: 10pt;
        background-color: white;
    }}
    #ServicesManagementWidget QHeaderView::section {{
        background-color: {COLOR_PRIMARY};
        color: {COLOR_TEXT_LIGHT};
        padding: 6px;
        border: none;
        border-right: 1px solid {COLOR_BORDER};
        font-weight: bold;
    }}
    #ServicesManagementWidget QHeaderView::section:last {{
        border-right: none;
    }}
    #ServicesManagementWidget QTableWidget::item {{
        padding: 5px;
        color: {COLOR_TEXT_DARK};
    }}
    #ServicesManagementWidget QTableWidget::item:selected {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_TEXT_LIGHT};
    }}
    #ServicesManagementWidget QTableWidget::item:focus {{
        outline: none;
    }}

    /* Scroll Bars */
    #ServicesManagementWidget QScrollBar:vertical {{
        border: none;
        background: {COLOR_SECONDARY};
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    #ServicesManagementWidget QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}
    #ServicesManagementWidget QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        background: none;
    }}
    #ServicesManagementWidget QScrollBar:horizontal {{
        border: none;
        background: {COLOR_SECONDARY};
        height: 10px;
        margin: 0px 0px 0px 0px;
    }}
    #ServicesManagementWidget QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER};
        min-width: 20px;
        border-radius: 5px;
    }}
    #ServicesManagementWidget QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: none;
    }}
"""

class ServiceDialog(QDialog):
    """Dialog for adding or editing a service with modern styling"""
    
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
        
        # If editing, populate fields
        if self.service_data:
            self.name_edit.setText(self.service_data.get('name', ''))
            self.description_edit.setPlainText(self.service_data.get('description', ''))
            self.price_edit.setValue(float(self.service_data.get('default_price', 0.0)))
            self.active_checkbox.setChecked(bool(self.service_data.get('is_active', 1)))
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter service name")
        layout.addRow(QLabel("Name:"), self.name_edit)
        
        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter service description")
        self.description_edit.setMaximumHeight(120)
        layout.addRow(QLabel("Description:"), self.description_edit)
        
        # Price field
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setRange(0, 1000000)
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
            # Add new service (assuming add_service doesn't take is_active)
            new_id = add_service(name, description, price)  # Removed is_active
            success = new_id is not None  # Check if new_id is not None
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
        self.setObjectName("ServicesManagementWidget")
        self.setStyleSheet(SERVICE_PAGE_STYLESHEET)
        
        # Initialize action_buttons list
        self.action_buttons = []
        
        self.setup_ui()
        self.load_services()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Heading "Service Management"
        heading_label = QLabel("Service Management")
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
        self.search_edit.setPlaceholderText("Search services...")
        self.search_edit.textChanged.connect(self.load_services)
        self.search_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_edit.setMinimumWidth(300)
        
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_edit, 1)
        header_layout.addStretch(1)
        
        buttons = [
            ("Add Service", 'fa5s.plus', self.add_service),
            ("Edit Service", 'fa5s.edit', self.edit_service),
            ("Delete Service", 'fa5s.trash', self.delete_service),
            ("Refresh", 'fa5s.sync', self.load_services)
        ]
        
        for text, icon_name, callback in buttons:
            button = QPushButton(qta.icon(icon_name, color=COLOR_TEXT_LIGHT), f" {text}")
            button.clicked.connect(callback)
            header_layout.addWidget(button)
            # Store the buttons that need to be enabled/disabled
            if text in ["Edit Service", "Delete Service"]:
                self.action_buttons.append(button)
                button.setEnabled(False)  # Initially disabled
        
        main_layout.addWidget(header_frame)
        
        # Scroll Area for Service Table
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Service Table
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Price", "Active"])
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.services_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.services_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.services_table.verticalHeader().setVisible(False)
        self.services_table.horizontalHeader().setStretchLastSection(True)
        self.services_table.setShowGrid(True)
        
        # Adjusted column widths: even narrower Active, wider Description
        self.services_table.setColumnWidth(0, 60)  # ID
        self.services_table.setColumnWidth(1, 180)  # Name
        self.services_table.setColumnWidth(2, 500)  # Description (increased to 400)
        self.services_table.setColumnWidth(3, 80)   # Price (unchanged)
        self.services_table.setColumnWidth(4, 25)   # Active (narrower to 50)
        
        self.services_table.itemSelectionChanged.connect(self.update_button_states)
        self.services_table.itemDoubleClicked.connect(self.edit_service)
        
        scroll_area.setWidget(self.services_table)
        main_layout.addWidget(scroll_area)
    
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
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.services_table.setItem(row, 3, price_item)
            
            # Status
            status_item = QTableWidgetItem("Yes" if service['is_active'] else "No")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.services_table.setItem(row, 4, status_item)
    
    def update_button_states(self):
        """Enable/disable action buttons based on selection"""
        is_service_selected = bool(self.services_table.selectionModel().hasSelection())
        for button in self.action_buttons:
            button.setEnabled(is_service_selected)
    
    def get_selected_service_id(self):
        """Get the ID of the selected service"""
        selected_rows = self.services_table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            id_item = self.services_table.item(selected_row, 0)
            if id_item:
                return id_item.data(Qt.ItemDataRole.UserRole)
        return None
    
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
    window.setWindowTitle("Service Management System")
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())