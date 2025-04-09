import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QApplication, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QColor
import qtawesome as qta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.main_window import PatientListPage
from database.schema import initialize_database
from ui.inventory_management import InventoryManagementWindow
from ui.due import DuePatientsWidget
from ui.analysis.patient_analysis import PatientAnalysis
from ui.analysis.service_analysis import ServiceAnalysis
from ui.analysis.financial_analysis import FinancialAnalysis
from ui.analysis.operational_analysis import OperationalAnalysis

CLINIC_NAME = "Salman Dental Clinic"
LOGO_FILENAME = "logo.png"
LOGO_PATH = LOGO_FILENAME

# Premium Color Palette
COLOR_PRIMARY = "#1a2b4a"      # Deep Navy Blue (Sidebar, Headers)
COLOR_SECONDARY = "#f5f7fa"    # Soft Off-White (Background)
COLOR_ACCENT = "#00aaff"       # Vibrant Sky Blue (Highlights, Buttons)
COLOR_TEXT_LIGHT = "#ffffff"   # Pure White (Light Text)
COLOR_TEXT_DARK = "#1f2a44"    # Dark Slate (Body Text)
COLOR_BORDER = "#d0d7de"       # Light Gray (Borders)
COLOR_HOVER = "#007acc"        # Darker Blue (Hover Effects)
COLOR_SHADOW = "rgba(0, 0, 0, 0.15)"  # Subtle Shadow

DASHBOARD_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_SECONDARY};
    }}
    #Sidebar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 {COLOR_PRIMARY}, stop:1 #2c3e60);
        border-right: 1px solid {COLOR_BORDER};
        box-shadow: 5px 0px 15px {COLOR_SHADOW};
    }}
    #Sidebar QLabel#ClinicNameLabel {{
        color: {COLOR_TEXT_LIGHT};
        font-size: 18pt;
        font-weight: bold;
        font-family: 'Roboto', sans-serif;
        padding: 15px;
        text-align: center;
        background: transparent;
    }}
    #Sidebar QLabel#LogoLabel {{
        margin: 20px 0;
        background: transparent;
    }}
    #Sidebar QPushButton {{
        background-color: transparent;
        color: {COLOR_TEXT_LIGHT};
        border: none;
        padding: 14px 20px;
        text-align: left;
        font-size: 12pt;
        font-family: 'Roboto', sans-serif;
        border-radius: 8px;
        margin: 5px 15px;
        transition: background-color 0.3s;
    }}
    #Sidebar QPushButton:hover {{
        background-color: {COLOR_HOVER};
    }}
    #Sidebar QPushButton:checked {{
        background-color: {COLOR_ACCENT};
        font-weight: bold;
        box-shadow: 0 4px 12px {COLOR_SHADOW};
    }}
    #ContentStackWidget {{
        background-color: {COLOR_SECONDARY};
        border-radius: 12px;
        margin: 10px;
    }}
    QScrollArea {{
        border: none;
        background-color: {COLOR_SECONDARY};
    }}
    QScrollBar:vertical {{
        border: none;
        background: {COLOR_SECONDARY};
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}
    QWidget#sectionWidget {{
        background-color: {COLOR_SECONDARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px {COLOR_SHADOW};
    }}
"""

class AnalysisWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        sections = [
            ("Patient Analytics", PatientAnalysis(), qta.icon('fa5s.user', color=COLOR_TEXT_DARK)),
            ("Service Analytics", ServiceAnalysis(), qta.icon('fa5s.tooth', color=COLOR_TEXT_DARK)),
            ("Financial Analytics", FinancialAnalysis(), qta.icon('fa5s.dollar-sign', color=COLOR_TEXT_DARK)),
            ("Operational Analytics", OperationalAnalysis(), qta.icon('fa5s.calendar', color=COLOR_TEXT_DARK)),
        ]

        for title, widget, icon in sections:
            section_widget = QWidget(objectName="sectionWidget")
            section_layout = QVBoxLayout(section_widget)
            section_layout.setContentsMargins(15, 15, 15, 15)
            section_layout.setSpacing(10)
            section_layout.addWidget(widget)
            content_layout.addWidget(section_widget)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

class DashboardWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{CLINIC_NAME} - Dashboard")
        self.setGeometry(50, 50, 1400, 800)  # Slightly larger for premium feel
        self.setStyleSheet(DASHBOARD_STYLESHEET)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar with Gradient and Shadow
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(10)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        logo_label = QLabel()
        logo_label.setObjectName("LogoLabel")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            pixmap = QPixmap(str(LOGO_PATH))
            logo_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except:
            logo_label.setText("Logo Missing")
            logo_label.setStyleSheet("color: white; font-style: italic;")
        sidebar_layout.addWidget(logo_label)

        clinic_name_label = QLabel(CLINIC_NAME)
        clinic_name_label.setObjectName("ClinicNameLabel")
        clinic_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clinic_name_label.setWordWrap(True)
        sidebar_layout.addWidget(clinic_name_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"background-color: {COLOR_BORDER}; height: 2px; margin: 15px 20px;")
        sidebar_layout.addWidget(line)

        self.nav_buttons = {}
        self.home_button = self.add_nav_button(sidebar_layout, "HOME", 'fa5s.home', self.refresh_home_page)
        self.due_patients_button = self.add_nav_button(sidebar_layout, "DUE PATIENTS", 'fa5s.money-bill-alt', self.refresh_due_patients)
        self.inventory_button = self.add_nav_button(sidebar_layout, "INVENTORY", 'fa5s.box', self.refresh_inventory)
        self.analysis_button = self.add_nav_button(sidebar_layout, "ANALYSIS", 'fa5s.chart-bar', self.refresh_analysis)

        sidebar_layout.addStretch(1)
        main_layout.addWidget(self.sidebar)

        # Content Stack
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStackWidget")

        self.home_page = None
        self.init_home_page()

        self.due_patients_page = None
        self.init_due_patients_page()

        self.inventory_page = None
        self.init_inventory_page()

        self.analysis_page = None
        self.init_analysis_page()

        main_layout.addWidget(self.content_stack)

        self.home_button.setChecked(True)
        self.current_button = self.home_button
        self.content_stack.setCurrentIndex(0)

    def init_home_page(self):
        try:
            if self.home_page is not None:
                self.content_stack.removeWidget(self.home_page)
                self.home_page.deleteLater()
            self.home_page = PatientListPage(self)
            self.content_stack.insertWidget(0, self.home_page)
        except Exception as e:
            error_widget = QLabel(f"Error loading PatientListPage: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.home_page = error_widget
            self.content_stack.insertWidget(0, error_widget)

    def init_due_patients_page(self):
        try:
            if self.due_patients_page is not None:
                self.content_stack.removeWidget(self.due_patients_page)
                self.due_patients_page.deleteLater()
            self.due_patients_page = DuePatientsWidget(self)
            self.content_stack.insertWidget(1, self.due_patients_page)
        except Exception as e:
            error_widget = QLabel(f"Error loading DuePatientsWidget: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.due_patients_page = error_widget
            self.content_stack.insertWidget(1, error_widget)

    def init_inventory_page(self):
        try:
            if self.inventory_page is not None:
                self.content_stack.removeWidget(self.inventory_page)
                self.inventory_page.deleteLater()
            inventory_window = InventoryManagementWindow()
            self.inventory_page = inventory_window.get_central_widget()
            self.content_stack.insertWidget(2, self.inventory_page)
        except Exception as e:
            error_widget = QLabel(f"Error loading InventoryManagementWindow: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.inventory_page = error_widget
            self.content_stack.insertWidget(2, error_widget)

    def init_analysis_page(self):
        try:
            if self.analysis_page is not None:
                self.content_stack.removeWidget(self.analysis_page)
                self.analysis_page.deleteLater()
            self.analysis_page = AnalysisWindow(self)
            self.content_stack.insertWidget(3, self.analysis_page)
        except Exception as e:
            error_widget = QLabel(f"Error loading AnalysisWindow: {str(e)}")
            error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.analysis_page = error_widget
            self.content_stack.insertWidget(3, error_widget)

    def add_nav_button(self, layout, text, icon_name, callback_function):
        button = QPushButton(qta.icon(icon_name, color=COLOR_TEXT_LIGHT), f" {text}")
        button.setCheckable(True)
        button.setIconSize(QSize(20, 20))
        button.clicked.connect(callback_function)
        layout.addWidget(button)
        return button

    def update_button_states(self, active_button):
        for btn in [self.home_button, self.due_patients_button, self.inventory_button, self.analysis_button]:
            if btn != active_button:
                btn.setChecked(False)
        active_button.setChecked(True)
        self.current_button = active_button

    def refresh_home_page(self):
        self.init_home_page()
        self.content_stack.setCurrentIndex(0)
        self.update_button_states(self.home_button)

    def refresh_due_patients(self):
        self.init_due_patients_page()
        self.content_stack.setCurrentIndex(1)
        self.update_button_states(self.due_patients_button)

    def refresh_inventory(self):
        self.init_inventory_page()
        self.content_stack.setCurrentIndex(2)
        self.update_button_states(self.inventory_button)

    def refresh_analysis(self):
        self.init_analysis_page()
        self.content_stack.setCurrentIndex(3)
        self.update_button_states(self.analysis_button)

    def show_home_page(self):
        self.refresh_home_page()

    def closeEvent(self, event):
        current_page = self.content_stack.currentWidget()
        if hasattr(current_page, 'close_active_child_window') and callable(current_page.close_active_child_window):
            current_page.close_active_child_window()

        reply = QMessageBox.question(self, 'Confirm Exit',
                                     "Are you sure you want to exit the application?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    initialize_database()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern base style
    mainWin = DashboardWindow()
    mainWin.show()
    sys.exit(app.exec())