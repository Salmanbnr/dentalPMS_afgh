import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QProgressBar, QMessageBox,
                             QSplitter, QFrame, QSizePolicy, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
import qtawesome as qta
from database.data_manager import backup_database, restore_database

class WorkerThread(QThread):
    """Worker thread to handle database operations without freezing UI"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, operation_type, path):
        super().__init__()
        self.operation_type = operation_type  # 'backup' or 'restore'
        self.path = path
    
    def run(self):
        if self.operation_type == 'backup':
            success, message = backup_database(self.path)
        else:  # restore
            success, message = restore_database(self.path)
        self.finished.emit(success, message)

class ActionCard(QFrame):
    """A custom styled card widget for actions"""
    def __init__(self, title, description, icon_name, button_text, parent=None):
        super().__init__(parent)
        self.setObjectName("actionCard")
        self.setStyleSheet("""
            #actionCard {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            #actionCard:hover {
                border: 1px solid #c0c0c0;
                background-color: #f9f9f9;
            }
        """)
        
        # Shadow effect
        self.setGraphicsEffect(None)  # No shadow for now
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        icon = qta.icon(icon_name, color="#4a86e8", scale_factor=1.5)
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(48, 48))
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555;")
        
        # Button
        self.action_button = QPushButton(button_text)
        self.action_button.setFont(QFont("Segoe UI", 10))
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #3b78de;
            }
            QPushButton:pressed {
                background-color: #2c69d1;
            }
        """)
        
        # Add to layout
        layout.addLayout(header_layout)
        layout.addWidget(desc_label)
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.action_button)
        
        layout.addLayout(button_layout)
        layout.setContentsMargins(20, 20, 20, 20)

class OperationPage(QWidget):
    """Base class for operation pages"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Header
        self.header_layout = QHBoxLayout()
        self.back_button = QPushButton()
        self.back_button.setIcon(qta.icon('fa5s.arrow-left', color='#4a86e8'))
        self.back_button.setFixedSize(40, 40)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border-radius: 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        
        self.header_layout.addWidget(self.back_button)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Status section
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        self.status_layout = QVBoxLayout(self.status_frame)
        
        self.status_header = QHBoxLayout()
        self.status_icon = QLabel()
        self.status_icon.setPixmap(qta.icon('fa5s.info-circle', color='#4a86e8').pixmap(24, 24))
        self.status_title = QLabel("Status")
        self.status_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        self.status_header.addWidget(self.status_icon)
        self.status_header.addWidget(self.status_title)
        self.status_header.addStretch()
        
        self.status_message = QLabel("Ready")
        self.status_message.setWordWrap(True)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate progress
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 5px;
            }
        """)
        
        self.status_layout.addLayout(self.status_header)
        self.status_layout.addWidget(self.status_message)
        self.status_layout.addWidget(self.progress_bar)
        
        # Add common elements to layout
        self.layout.addLayout(self.header_layout)
        
        # Content will be added by subclasses
        
        # Add status frame at the bottom
        self.layout.addStretch()
        self.layout.addWidget(self.status_frame)
    
    def update_status(self, message, show_progress=False):
        """Update the status message and progress bar"""
        self.status_message.setText(message)
        self.progress_bar.setVisible(show_progress)

class BackupPage(OperationPage):
    """Page for backup operation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title_label.setText("Database Backup")
        
        # Path selection
        self.path_frame = QFrame()
        self.path_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        path_layout = QVBoxLayout(self.path_frame)
        
        path_header = QHBoxLayout()
        path_icon = QLabel()
        path_icon.setPixmap(qta.icon('fa5s.folder-open', color='#4a86e8').pixmap(24, 24))
        path_title = QLabel("Backup Location")
        path_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        path_header.addWidget(path_icon)
        path_header.addWidget(path_title)
        path_header.addStretch()
        
        path_layout.addLayout(path_header)
        
        self.path_select_layout = QHBoxLayout()
        self.path_label = QLabel("Select a folder for backup")
        self.path_label.setStyleSheet("color: #555;")
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.setIcon(qta.icon('fa5s.folder', color='white'))
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #3b78de;
            }
        """)
        
        self.path_select_layout.addWidget(self.path_label)
        self.path_select_layout.addStretch()
        self.path_select_layout.addWidget(self.browse_button)
        
        path_layout.addLayout(self.path_select_layout)
        
        # Backup button
        self.backup_button = QPushButton("Start Backup")
        self.backup_button.setIcon(qta.icon('fa5s.database', color='white'))
        self.backup_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.backup_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.backup_button.setEnabled(False)
        
        backup_button_layout = QHBoxLayout()
        backup_button_layout.addStretch()
        backup_button_layout.addWidget(self.backup_button)
        backup_button_layout.addStretch()
        
        # Add everything to layout
        self.layout.insertWidget(1, self.path_frame)
        self.layout.insertLayout(2, backup_button_layout)
        
        # Connect signals
        self.browse_button.clicked.connect(self.select_backup_folder)
        self.backup_button.clicked.connect(self.start_backup)
        
        self.selected_path = None
    
    def select_backup_folder(self):
        """Open folder dialog to select backup location"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder_path:
            self.selected_path = folder_path
            self.path_label.setText(f"{folder_path}")
            self.backup_button.setEnabled(True)
    
    def start_backup(self):
        """Start the backup process"""
        if self.selected_path:
            self.update_status("Backing up database, please wait...", True)
            self.backup_button.setEnabled(False)
            self.browse_button.setEnabled(False)
            
            # Start worker thread
            self.worker = WorkerThread('backup', self.selected_path)
            self.worker.finished.connect(self.backup_completed)
            self.worker.start()
    
    def backup_completed(self, success, message):
        """Handle backup completion"""
        self.progress_bar.setVisible(False)
        self.browse_button.setEnabled(True)
        self.backup_button.setEnabled(True)
        
        if success:
            self.status_icon.setPixmap(qta.icon('fa5s.check-circle', color='#4CAF50').pixmap(24, 24))
            QMessageBox.information(self, "Backup Successful", message)
        else:
            self.status_icon.setPixmap(qta.icon('fa5s.exclamation-circle', color='#f44336').pixmap(24, 24))
            QMessageBox.critical(self, "Backup Failed", message)
        
        self.update_status(message)

class RestorePage(OperationPage):
    """Page for restore operation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title_label.setText("Database Restore")
        
        # Path selection
        self.path_frame = QFrame()
        self.path_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        path_layout = QVBoxLayout(self.path_frame)
        
        path_header = QHBoxLayout()
        path_icon = QLabel()
        path_icon.setPixmap(qta.icon('fa5s.file-import', color='#4a86e8').pixmap(24, 24))
        path_title = QLabel("Restore File")
        path_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        path_header.addWidget(path_icon)
        path_header.addWidget(path_title)
        path_header.addStretch()
        
        path_layout.addLayout(path_header)
        
        self.path_select_layout = QHBoxLayout()
        self.path_label = QLabel("Select a backup file to restore")
        self.path_label.setStyleSheet("color: #555;")
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.setIcon(qta.icon('fa5s.file', color='white'))
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #3b78de;
            }
        """)
        
        self.path_select_layout.addWidget(self.path_label)
        self.path_select_layout.addStretch()
        self.path_select_layout.addWidget(self.browse_button)
        
        path_layout.addLayout(self.path_select_layout)
        
        # Warning message
        self.warning_label = QLabel(
            "Warning: Restoring will replace your current database. "
            "A backup of your current database will be created before restoring."
        )
        self.warning_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        
        # Restore button
        self.restore_button = QPushButton("Start Restore")
        self.restore_button.setIcon(qta.icon('fa5s.sync-alt', color='white'))
        self.restore_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restore_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.restore_button.setEnabled(False)
        
        restore_button_layout = QHBoxLayout()
        restore_button_layout.addStretch()
        restore_button_layout.addWidget(self.restore_button)
        restore_button_layout.addStretch()
        
        # Add everything to layout
        self.layout.insertWidget(1, self.path_frame)
        self.layout.insertWidget(2, self.warning_label)
        self.layout.insertLayout(3, restore_button_layout)
        
        # Connect signals
        self.browse_button.clicked.connect(self.select_restore_file)
        self.restore_button.clicked.connect(self.start_restore)
        
        self.selected_path = None
    
    def select_restore_file(self):
        """Open file dialog to select restore file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File to Restore", "", "Database Files (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        if file_path:
            self.selected_path = file_path
            self.path_label.setText(f"{file_path}")
            self.restore_button.setEnabled(True)
    
    def start_restore(self):
        """Start the restore process"""
        if self.selected_path:
            # Confirm restore
            reply = QMessageBox.question(
                self, "Confirm Restore", 
                "Are you sure you want to restore the database? This will replace your current database.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.update_status("Restoring database, please wait...", True)
                self.restore_button.setEnabled(False)
                self.browse_button.setEnabled(False)
                
                # Start worker thread
                self.worker = WorkerThread('restore', self.selected_path)
                self.worker.finished.connect(self.restore_completed)
                self.worker.start()
    
    def restore_completed(self, success, message):
        """Handle restore completion"""
        self.progress_bar.setVisible(False)
        self.browse_button.setEnabled(True)
        self.restore_button.setEnabled(True)
        
        if success:
            self.status_icon.setPixmap(qta.icon('fa5s.check-circle', color='#4CAF50').pixmap(24, 24))
            QMessageBox.information(self, "Restore Successful", message)
        else:
            self.status_icon.setPixmap(qta.icon('fa5s.exclamation-circle', color='#f44336').pixmap(24, 24))
            QMessageBox.critical(self, "Restore Failed", message)
        
        self.update_status(message)

class DatabaseBackupRestoreUI(QMainWindow):
    """Main window for database backup and restore operations"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Backup & Restore")
        self.resize(600, 500)
        
        # Set the window icon
        self.setWindowIcon(qta.icon('fa5s.database', color='#4a86e8'))
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.home_page = QWidget()
        self.create_home_page()
        
        self.backup_page = BackupPage()
        self.backup_page.back_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.home_page))
        
        self.restore_page = RestorePage()
        self.restore_page.back_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.home_page))
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.backup_page)
        self.stacked_widget.addWidget(self.restore_page)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.stacked_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Apply global stylesheet
        self.apply_stylesheet()
    
    def create_home_page(self):
        """Create the home page with action cards"""
        layout = QVBoxLayout(self.home_page)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Database Management")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Subtitle
        subtitle = QLabel("Choose an operation to perform")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #666;")
        
        # Cards layout
        cards_layout = QHBoxLayout()
        
        # Backup card
        backup_card = ActionCard(
            "Backup Database",
            "Create a backup copy of your database with timestamp",
            "fa5s.save",
            "Backup Now"
        )
        backup_card.action_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.backup_page))
        
        # Restore card
        restore_card = ActionCard(
            "Restore Database",
            "Restore your database from a previous backup",
            "fa5s.sync-alt",
            "Restore Now"
        )
        restore_card.action_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.restore_page))
        
        cards_layout.addWidget(backup_card)
        cards_layout.addWidget(restore_card)
        
        # Add to main layout
        layout.addLayout(header_layout)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addLayout(cards_layout)
        layout.addStretch()
        
        # Footer
        footer = QLabel("Your database is safe with us")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(footer)
        
        layout.setContentsMargins(30, 30, 30, 20)
    
    def apply_stylesheet(self):
        """Apply global stylesheet to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
            }
            QFrame {
                margin: 5px;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern look across platforms
    
    # Set application-wide palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Text, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.Button, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.Link, QColor(74, 134, 232))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(74, 134, 232))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)
    
    window = DatabaseBackupRestoreUI()
    window.show()
    sys.exit(app.exec())