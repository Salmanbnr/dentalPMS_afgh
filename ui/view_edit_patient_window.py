import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta
from pathlib import Path

# Use absolute imports assuming running from project root
try:
    from database.data_manager import get_all_patients
    from ui.patient.patient_detail_widget import PatientDetailWidget
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from database.data_manager import get_all_patients
    from ui.patient.patient_detail_widget import PatientDetailWidget

class PatientViewEditWindow(QMainWindow):
    """
    Window displaying detailed patient information and visit management.
    Uses a PatientDetailWidget to show patient details and manage visits.
    """
    data_changed = pyqtSignal(int)

    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        self.current_patient_id = patient_id
        self.setWindowTitle(f"Patient Details & Visits (ID: {patient_id})")
        self.resize(800, 650)
        self.setWindowIcon(qta.icon('fa5s.notes-medical'))

        # Create main widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)

        # Create a patient detail widget with the buttons at the bottom
        self.detail_area = CustomPatientDetailWidget(patient_id)
        self.main_layout.addWidget(self.detail_area)
        
        # Connect signals for buttons that may be in the detail widget
        self.detail_area.connect_signals()
        
        # Set global stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QWidget {
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                color: #333;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 15px;
                background-color: white;
               
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
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

    def closeEvent(self, event):
        print(f"Closing PatientViewEditWindow for patient ID: {self.current_patient_id}")
        self.data_changed.emit(self.current_patient_id)
        super().closeEvent(event)


class CustomPatientDetailWidget(QWidget):
    """
    Extended PatientDetailWidget that handles its own scrolling and ensures
    all buttons are visible within the scrollable area.
    """
    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        
        # Main layout without scrolling
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create scroll area for the contents
        self.scroll_area = QFrame()
        self.scroll_area_layout = QVBoxLayout(self.scroll_area)
        self.scroll_area_layout.setContentsMargins(0, 0, 10, 0)  # Right margin for scrollbar
        self.scroll_area_layout.setSpacing(15)
        
        # Create the actual PatientDetailWidget and add it to scroll area
        self.detail_widget = PatientDetailWidget()
        self.scroll_area_layout.addWidget(self.detail_widget)
        
        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)
        
        # Load patient data
        self.load_patient(patient_id)
        
    def load_patient(self, patient_id):
        if patient_id:
            self.detail_widget.load_patient(patient_id)
        else:
            self.detail_widget.clear_details()
            self.detail_widget.patient_info_group.setTitle("No Patient ID Provided")
    
    def connect_signals(self):
        """Connect any signals from the detail widget to this widget"""
        # Add any signal connections needed here
        # For example: self.detail_widget.some_signal.connect(self.some_handler)
        pass
    
    def resizeEvent(self, event):
        """Handle resize events to update the layout if needed"""
        super().resizeEvent(event)
        # Any additional resize handling would go here