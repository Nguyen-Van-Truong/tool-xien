"""
Main Window - Giao diện chính của ứng dụng
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QCheckBox, QTableWidget, 
    QTableWidgetItem, QTextEdit, QGroupBox, QHeaderView,
    QMessageBox, QFileDialog, QToolButton, QMenu, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QAction
# ChatGPTAutomation không còn được sử dụng - đã tách thành RegLoginThread và VerificationThread
from utils.file_loader import FileLoader
from utils.config import Config
import json
from datetime import datetime
import os


class RegLoginThread(QThread):
    """Thread để chạy register/login - chỉ đăng ký/đăng nhập, lưu cookie, đóng browser"""
    status_update = pyqtSignal(int, str, str)  # row_index, status, message
    log_message = pyqtSignal(str)
    
    def __init__(self, row_index, account_data, use_proxy=False, proxy_data=None, browser_id=None):
        super().__init__()
        self.row_index = row_index
        self.account_data = account_data
        self.use_proxy = use_proxy
        self.proxy_data = proxy_data
        self.browser_id = browser_id or f"{row_index}_{account_data.get('email', 'unknown')}"
        self.is_running = True
        self.automation = None
        
    def run(self):
        """Chạy register/login - Mở browser thật"""
        try:
            from automation.reg_login_automation import RegLoginAutomation
            
            self.automation = RegLoginAutomation(
                self.account_data,
                use_proxy=self.use_proxy,
                proxy_data=self.proxy_data,
                browser_id=self.browser_id
            )
            
            # Connect signals
            self.automation.log_message.connect(self.log_message.emit)
            
            # Run register/login (mở browser thật, không timeout)
            result = self.automation.run()
            
            if result['success']:
                self.status_update.emit(self.row_index, "Ready!", "✓ Registered/Logged in - Cookies saved")
            else:
                error_msg = result.get('error', 'Register/Login failed')
                self.status_update.emit(self.row_index, "Failed", f"✗ {error_msg}")
                
        except Exception as e:
            error_msg = str(e)
            self.status_update.emit(self.row_index, "Failed", f"✗ {error_msg}")
    
    def stop(self):
        """Dừng automation"""
        self.is_running = False
        if self.automation:
            self.automation.stop()


class VerificationThread(QThread):
    """Thread để chạy verification only - chỉ verify, đóng browser sau khi xong"""
    status_update = pyqtSignal(int, str, str)  # row_index, status, message
    log_message = pyqtSignal(str)
    
    def __init__(self, row_index, account_data, veteran_data, use_proxy=False, proxy_data=None, browser_id=None, veteran_index=None):
        super().__init__()
        self.row_index = row_index
        self.row_number = row_index  # Lưu row_number để hiển thị trong error
        self.account_data = account_data
        self.veteran_data = veteran_data
        self.veteran_index = veteran_index  # Lưu index của veteran_data để release sau
        self.use_proxy = use_proxy
        self.proxy_data = proxy_data
        self.browser_id = browser_id or f"{row_index}_{account_data.get('email', 'unknown')}"
        self.is_running = True
        self.automation = None
        
    def run(self):
        """Chạy verification only"""
        try:
            from automation.verification_only_automation import VerificationOnlyAutomation
            
            self.automation = VerificationOnlyAutomation(
                self.account_data,
                self.veteran_data,
                use_proxy=self.use_proxy,
                proxy_data=self.proxy_data,
                browser_id=self.browser_id
            )
            # Pass row_number để hiển thị trong error message
            self.automation.row_number = self.row_number
            
            # Connect signals
            self.automation.log_message.connect(self.log_message.emit)
            
            # Run verification
            result = self.automation.run()
            
            if result['success']:
                status = result.get('status', 'Verified!')
                message = result.get('message', f"✓ Verified! {result.get('name', '')}")
                self.status_update.emit(self.row_index, status, message)
            else:
                status = result.get('status', 'Failed')
                message = result.get('message', result.get('error', 'Verification failed'))
                # Format error message nếu chưa được format
                if status == 'Failed' and not message.startswith('❌') and not message.startswith('✗'):
                    if "Page.wait_for_selector" in message or "Target page" in message:
                        message = "Browser đã bị đóng hoặc element không tìm thấy"
                    elif "timeout" in message.lower():
                        message = "Timeout - Quá thời gian chờ"
                    message = f"✗ {message}"
                self.status_update.emit(self.row_index, status, message)
                
        except Exception as e:
            error_msg = str(e)
            # Format error message
            if "Page.wait_for_selector" in error_msg or "Target page" in error_msg:
                error_msg = "Browser đã bị đóng hoặc element không tìm thấy"
            elif "timeout" in error_msg.lower():
                error_msg = "Timeout - Quá thời gian chờ"
            self.status_update.emit(self.row_index, "Failed", f"✗ {error_msg}")
    
    def stop(self):
        """Dừng automation và cleanup browser"""
        self.is_running = False
        if self.automation:
            try:
                # Stop automation
                self.automation.is_running = False
                self.automation.stop()
                
                # Cleanup browser resources
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.automation.cleanup())
                    loop.close()
                except Exception as e:
                    # Ignore cleanup errors
                    pass
            except Exception:
                # Ignore errors when stopping
                pass


class MainWindow(QMainWindow):
    """Main Window class"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatGPT Military Verification Tool")
        self.setGeometry(100, 100, 950, 900)
        
        # Data storage
        self.accounts = []
        self.proxies = []
        self.veteran_data = []
        self.veteran_data_file_path = None  # Lưu đường dẫn file veteran data
        self.automation_threads = {}  # row_index -> thread
        self.use_direct_ip = True
        self.max_concurrent_browsers = 10  # Maximum browsers to process simultaneously
        # Track veteran data usage: {veteran_index: True if in use}
        self.veteran_data_in_use = {}  # veteran_index -> True/False
        
        # Apply global stylesheet
        self.apply_stylesheet()
        
        # Initialize UI
        self.init_ui()
        
        # Load saved config
        self.load_config()
    
    def apply_stylesheet(self):
        """Áp dụng stylesheet cho toàn bộ ứng dụng - Dense automation tool style"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 10pt;
                color: #d0d0d0;
                border: 1px solid #3a3a3a;
                border-radius: 6px;

                margin-top: 8px;
                padding-top: 0px;
}
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QLabel {
                color: #d0d0d0;
                font-size: 9pt;
            }
            QCheckBox {
                color: #d0d0d0;
                font-size: 9pt;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QCheckBox::indicator:checked {
                background-color: #10b981;
                border-color: #10b981;
            }
            QCheckBox::indicator:hover {
                border-color: #777777;
            }
            QTableWidget {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                gridline-color: #3a3a3a;
                color: #e0e0e0;
                selection-background-color: #3a3a3a;
                selection-color: #ffffff;
            }
            QTableWidget::item {
                padding: 4px 6px;
                border: none;
            }
            QTableWidget::item:hover {
                background-color: #2f2f2f;
            }
            QTableWidget::item:selected {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: #d0d0d0;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid #3a3a3a;
                font-weight: 600;
                font-size: 9pt;
            }
            QTextEdit {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 8pt;
                padding: 6px;
            }
        """)
    
    def get_button_style(self, color_type="primary", size="normal"):
        """Tạo style cho button với hover effects
        
        Args:
            color_type: 'primary' (green), 'secondary' (gray), 'danger' (red), 
                       'warning' (orange), 'info' (blue), 'purple' (purple)
            size: 'normal', 'small'
        """
        colors = {
            "primary": {
                "bg": "#10b981",
                "bg_hover": "#059669",
                "bg_pressed": "#047857",
                "shadow": "rgba(16, 185, 129, 0.3)"
            },
            "secondary": {
                "bg": "#475569",
                "bg_hover": "#64748b",
                "bg_pressed": "#334155",
                "shadow": "rgba(71, 85, 105, 0.3)"
            },
            "danger": {
                "bg": "#ef4444",
                "bg_hover": "#dc2626",
                "bg_pressed": "#b91c1c",
                "shadow": "rgba(239, 68, 68, 0.3)"
            },
            "warning": {
                "bg": "#f59e0b",
                "bg_hover": "#d97706",
                "bg_pressed": "#b45309",
                "shadow": "rgba(245, 158, 11, 0.3)"
            },
            "info": {
                "bg": "#3b82f6",
                "bg_hover": "#2563eb",
                "bg_pressed": "#1d4ed8",
                "shadow": "rgba(59, 130, 246, 0.3)"
            },
            "purple": {
                "bg": "#8b5cf6",
                "bg_hover": "#7c3aed",
                "bg_pressed": "#6d28d9",
                "shadow": "rgba(139, 92, 246, 0.3)"
            }
        }
        
        color = colors.get(color_type, colors["primary"])
        # Reduced height buttons (2/3 of original: 24px for normal, 19px for small)
        padding = "6px 12px" if size == "normal" else "4px 8px"
        font_size = "9pt" if size == "normal" else "8pt"
        border_radius = "6px" if size == "normal" else "6px"
        min_height = "24px" if size == "normal" else "19px"
        
        return f"""
            QPushButton {{
                background-color: {color["bg"]};
                color: white;
                font-weight: 600;
                font-size: {font_size};
                padding: {padding};
                border: none;
                border-radius: {border_radius};
                min-height: {min_height};
            }}
            QPushButton:hover {{
                background-color: {color["bg_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {color["bg_pressed"]};
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #888888;
                opacity: 0.5;
            }}
        """
    
    def init_ui(self):
        """Khởi tạo giao diện - Dense automation tool layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(8, 8, 8, 4)
        
        # Top control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Browser status table
        self.browser_table = self.create_browser_table()
        main_layout.addWidget(self.browser_table)
        
        # Log output
        log_section = self.create_log_section()
        main_layout.addWidget(log_section)
    
    def create_control_panel(self):
        """Tạo control panel - Dense horizontal layout như automation tool"""
        group = QGroupBox("Control Panel")
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Row 1: Setup buttons (Green/Blue) - Spread across full width
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.setContentsMargins(0, 0, 0, 0)
        
        btn_setup_vpn = QPushButton("Setup VPN (Launch Browsers)")
        btn_setup_vpn.setStyleSheet(self.get_button_style("primary"))
        btn_setup_vpn.clicked.connect(self.setup_vpn)
        btn_setup_vpn.setToolTip("Setup VPN and launch browser instances")
        btn_setup_vpn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_save_profiles = QPushButton("Save Profiles")
        btn_save_profiles.setStyleSheet(self.get_button_style("secondary"))
        btn_save_profiles.clicked.connect(self.save_profiles)
        btn_save_profiles.setToolTip("Save current configuration")
        btn_save_profiles.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_clear_data = QPushButton("Clear Data")
        btn_clear_data.setStyleSheet(self.get_button_style("danger"))
        btn_clear_data.clicked.connect(self.clear_data)
        btn_clear_data.setToolTip("Clear all loaded accounts and data")
        btn_clear_data.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        row1.addWidget(btn_setup_vpn)
        row1.addWidget(btn_save_profiles)
        row1.addWidget(btn_clear_data)
        
        # Row 2: Status info and load buttons - Spread across full width
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.setContentsMargins(0, 0, 0, 0)
        
        self.label_accounts = QLabel("Accounts: <span style='color: #10b981; font-weight: 700;'>0</span> loaded")
        self.label_accounts.setStyleSheet("font-size: 9pt; color: #d0d0d0;")
        self.label_accounts.setTextFormat(Qt.TextFormat.RichText)
        self.label_accounts.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        btn_load_accounts = QPushButton("Load Accounts")
        btn_load_accounts.setStyleSheet(self.get_button_style("primary"))
        btn_load_accounts.clicked.connect(self.load_accounts)
        btn_load_accounts.setToolTip("Load ChatGPT accounts from file")
        btn_load_accounts.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_load_proxies = QPushButton("Load Proxies")
        btn_load_proxies.setStyleSheet(self.get_button_style("purple"))
        btn_load_proxies.clicked.connect(self.load_proxies)
        btn_load_proxies.setToolTip("Load proxy list (optional)")
        btn_load_proxies.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.checkbox_direct_ip = QCheckBox("Use Direct IP (No Proxy)")
        self.checkbox_direct_ip.setChecked(True)
        self.checkbox_direct_ip.stateChanged.connect(self.on_direct_ip_changed)
        self.checkbox_direct_ip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.label_data = QLabel("Data: <span style='color: #10b981; font-weight: 700;'>0</span> entries loaded")
        self.label_data.setStyleSheet("font-size: 9pt; color: #d0d0d0;")
        self.label_data.setTextFormat(Qt.TextFormat.RichText)
        self.label_data.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        btn_load_data = QPushButton("Load Data")
        btn_load_data.setStyleSheet(self.get_button_style("primary"))
        btn_load_data.clicked.connect(self.load_data)
        btn_load_data.setToolTip("Load veteran verification data")
        btn_load_data.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        row2.addWidget(self.label_accounts)
        row2.addWidget(btn_load_accounts)
        row2.addWidget(btn_load_proxies)
        row2.addWidget(self.checkbox_direct_ip)
        row2.addWidget(self.label_data)
        row2.addWidget(btn_load_data)
        
        # Row 3: Authentication and automation controls - Spread across full width
        row3 = QHBoxLayout()
        row3.setSpacing(6)
        row3.setContentsMargins(0, 0, 0, 0)
        
        btn_login_outlook = QPushButton("Login Outlook")
        btn_login_outlook.setStyleSheet(self.get_button_style("secondary"))
        btn_login_outlook.clicked.connect(self.login_outlook)
        btn_login_outlook.setToolTip("Login to Outlook for email access")
        btn_login_outlook.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_get_code = QPushButton("Get Code")
        btn_get_code.setStyleSheet(self.get_button_style("primary"))
        btn_get_code.clicked.connect(self.get_code)
        btn_get_code.setToolTip("Get verification codes from email")
        btn_get_code.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_start_automation = QPushButton("Start Automation")
        btn_start_automation.setStyleSheet(self.get_button_style("secondary"))
        btn_start_automation.clicked.connect(self.start_automation)
        btn_start_automation.setToolTip("Start automated verification (headless)")
        btn_start_automation.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_stop_automation = QPushButton("Stop Automation")
        btn_stop_automation.setStyleSheet(self.get_button_style("secondary"))
        btn_stop_automation.clicked.connect(self.stop_automation)
        btn_stop_automation.setToolTip("Stop all running automation")
        btn_stop_automation.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        btn_run_current = QPushButton("Chạy Hiện")
        btn_run_current.setStyleSheet(self.get_button_style("purple"))
        btn_run_current.clicked.connect(self.run_current)
        btn_run_current.setToolTip("Run selected row with visible browser")
        btn_run_current.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        row3.addWidget(btn_login_outlook)
        row3.addWidget(btn_get_code)
        row3.addWidget(btn_start_automation)
        row3.addWidget(btn_stop_automation)
        row3.addWidget(btn_run_current)
        
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        group.setLayout(layout)
        
        return group
    
    def create_browser_table(self):
        """Tạo bảng browser status - Dense với tất cả action buttons visible"""
        group = QGroupBox("Browser Status")
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        
        table = QTableWidget()
        table.setColumnCount(8)
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "#", "Email", "Status", "Message", 
            "Retry", "Reg/Login", "Code", "Start Veri", "Clear"
        ])
        
        # Set column widths - All columns are resizable
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Set initial column widths - Match image exactly
        table.setColumnWidth(0, 35)   # #
        table.setColumnWidth(1, 180)  # Email
        table.setColumnWidth(2, 80)   # Status
        table.setColumnWidth(3, 250)  # Message
        table.setColumnWidth(4, 60)   # Retry
        table.setColumnWidth(5, 85)   # Reg/Login
        table.setColumnWidth(6, 60)   # Code
        table.setColumnWidth(7, 80)   # Start Veri
        table.setColumnWidth(8, 60)   # Clear
        
        # Set initial rows (0 rows, will be updated based on accounts)
        table.setRowCount(0)
        
        # Note: Rows will be populated when accounts are loaded via populate_table()
        
        # Set table properties
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Dense table styling - Match image exactly with tight spacing
        table.setStyleSheet("""
            QTableWidget {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                gridline-color: #3a3a3a;
                color: #e0e0e0;
                selection-background-color: #3a3a3a;
                selection-color: #ffffff;
            }
            QTableWidget::item {
                padding: 2px 4px;
                border: none;
            }
            QTableWidget::item:hover {
                background-color: #2f2f2f;
            }
            QTableWidget::item:selected {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QTableWidget::item:alternate {
                background-color: #252525;
            }
            QTableWidget QPushButton {
                margin: 0px;
            }
        """)
        
        # Set row height to be compact
        table.verticalHeader().setDefaultSectionSize(28)
        table.verticalHeader().setVisible(False)
        
        layout.addWidget(table)
        group.setLayout(layout)
        
        self.browser_table_widget = table
        return group
    
    
    def create_log_section(self):
        """Tạo phần log output - Giống như Browser Status, dùng QGroupBox"""
        group = QGroupBox("Log Output")
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)  # Giống Browser Status
        layout.setSpacing(0)  # Không có spacing giữa các widget
        
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setMinimumHeight(150)  # Tăng lại để hiển thị đủ
        log_text.setMaximumHeight(10)  # Giữ nguyên kích thước
        log_text.setStyleSheet("""
            QTextEdit {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 8pt;
                padding: 2px 4px;
                margin: 0px;
            }
        """)
        
        layout.addWidget(log_text)
        group.setLayout(layout)
        
        self.log_text = log_text
        return group
    
    # Control Panel Actions
    def setup_vpn(self):
        """Setup VPN và launch browsers"""
        self.log("Setting up VPN and launching browsers...")
        # TODO: Implement VPN setup
        QMessageBox.information(self, "Info", "VPN setup feature coming soon")
    
    def save_profiles(self):
        """Save profiles"""
        self.log("Saving profiles...")
        self.save_config()
        QMessageBox.information(self, "Info", "Profiles saved successfully")
    
    def clear_data(self):
        """Clear all data"""
        reply = QMessageBox.question(
            self, "Confirm", "Are you sure you want to clear all data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.accounts = []
            self.proxies = []
            self.veteran_data = []
            self.update_accounts_label()
            self.update_data_label()
            self.log("All data cleared")
    
    def load_accounts(self):
        """Load accounts from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Accounts", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                loader = FileLoader()
                self.accounts = loader.load_accounts(file_path)
                self.update_accounts_label()
                self.populate_table()
                self.log(f"Loaded {len(self.accounts)} accounts")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load accounts: {str(e)}")
    
    def load_proxies(self):
        """Load proxies from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Proxies", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                loader = FileLoader()
                self.proxies = loader.load_proxies(file_path)
                self.log(f"Loaded {len(self.proxies)} proxies")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load proxies: {str(e)}")
    
    def load_data(self):
        """Load veteran data from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Data", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                loader = FileLoader()
                self.veteran_data = loader.load_veteran_data(file_path)
                self.veteran_data_file_path = file_path  # Lưu đường dẫn file
                self.veteran_data_in_use = {}  # Reset tracking khi load lại data
                self.update_data_label()
                self.log(f"Loaded {len(self.veteran_data)} veteran data entries")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
    
    def on_direct_ip_changed(self, state):
        """Handle direct IP checkbox change"""
        self.use_direct_ip = (state == Qt.CheckState.Checked.value)
        self.log(f"Use Direct IP: {self.use_direct_ip}")
    
    def login_outlook(self):
        """Login Outlook"""
        self.log("Login Outlook feature coming soon")
        QMessageBox.information(self, "Info", "Login Outlook feature coming soon")
    
    def get_code(self):
        """Get code for all accounts"""
        self.log("Get Code feature coming soon")
        QMessageBox.information(self, "Info", "Get Code feature coming soon")
    
    def start_automation(self):
        """Start automation for all rows (headless mode) - Max 10 concurrent"""
        if not self.accounts or not self.veteran_data:
            QMessageBox.warning(self, "Warning", "Please load accounts and data first")
            return
        
        # Calculate how many rows to process (max 10)
        num_rows = min(len(self.accounts), self.max_concurrent_browsers, len(self.veteran_data))
        
        self.log(f"Starting automation for {num_rows} rows (headless mode, max {self.max_concurrent_browsers} concurrent)...")
        
        # Start automation for up to max_concurrent_browsers
        for i in range(num_rows):
            self.start_veri_row(i)
    
    def stop_automation(self):
        """Stop all automation"""
        self.log("Stopping all automation...")
        for thread in self.automation_threads.values():
            if thread.isRunning():
                thread.stop()
                thread.terminate()
        self.automation_threads.clear()
    
    def run_current(self):
        """Run current selected row - Start Veri"""
        current_row = self.browser_table_widget.currentRow()
        if current_row >= 0:
            self.start_veri_row(current_row)
    
    # Table Actions
    def retry_row(self, row):
        """Retry verification for a row"""
        self.log(f"Retrying row {row + 1}...")
        self.start_veri_row(row)
    
    def set_row_buttons_enabled(self, row, enabled):
        """Enable/Disable all buttons for a specific row"""
        try:
            # Retry button (column 4)
            btn_retry = self.browser_table_widget.cellWidget(row, 4)
            if btn_retry:
                btn_retry.setEnabled(enabled)
            
            # Reg/Login button (column 5)
            btn_reg_login = self.browser_table_widget.cellWidget(row, 5)
            if btn_reg_login:
                btn_reg_login.setEnabled(enabled)
            
            # Code button (column 6)
            btn_code = self.browser_table_widget.cellWidget(row, 6)
            if btn_code:
                btn_code.setEnabled(enabled)
            
            # Start Veri button (column 7)
            btn_start_veri = self.browser_table_widget.cellWidget(row, 7)
            if btn_start_veri:
                btn_start_veri.setEnabled(enabled)
            
            # Clear button (column 8)
            btn_clear = self.browser_table_widget.cellWidget(row, 8)
            if btn_clear:
                btn_clear.setEnabled(enabled)
        except Exception as e:
            # Ignore errors if buttons don't exist
            pass
    
    def reg_login_row(self, row):
        """Register/Login for a specific row - Mở browser để người dùng tự đăng ký/đăng nhập"""
        # Check if already running
        if row in self.automation_threads:
            thread = self.automation_threads[row]
            if thread.isRunning():
                QMessageBox.warning(self, "Warning", f"Row {row + 1} is already running")
                return
        
        if row >= len(self.accounts):
            QMessageBox.warning(self, "Warning", "Invalid row")
            return
        
        account = self.accounts[row]
        self.log(f"Opening browser for Reg/Login (row {row + 1}): {account.get('email', '')} - Please complete registration/login manually")
        
        # Update table status
        status_item = QTableWidgetItem("Waiting")
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        status_item.setForeground(QColor("#f59e0b"))
        status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.browser_table_widget.setItem(row, 2, status_item)
        
        message_item = QTableWidgetItem("Browser opened - Please complete registration/login manually")
        message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.browser_table_widget.setItem(row, 3, message_item)
        
        # Get proxy if needed
        proxy_data = None
        if not self.use_direct_ip and row < len(self.proxies):
            proxy_data = self.proxies[row]
        
        # Create and start thread for Reg/Login (chỉ mở browser, không tự động)
        browser_id = f"{row}_{account.get('email', 'unknown')}"
        thread = RegLoginThread(row, account, self.use_direct_ip, proxy_data, browser_id)
        thread.status_update.connect(self.on_status_update)
        thread.log_message.connect(self.log)
        self.automation_threads[row] = thread
        thread.start()
    
    def get_code_row(self, row):
        """Get OTP code from email API and display it"""
        if row >= len(self.accounts):
            QMessageBox.warning(self, "Warning", "Invalid row")
            return
        
        account = self.accounts[row]
        self.log(f"Getting OTP code for row {row + 1}: {account.get('email', '')}")
        
        # Check if email API credentials are available
        if not account.get('emailLogin') or not account.get('refreshToken') or not account.get('clientId'):
            QMessageBox.warning(self, "Warning", "Missing email API credentials (emailLogin, refreshToken, clientId)")
            return
        
        # Update table status
        status_item = QTableWidgetItem("Getting Code")
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        status_item.setForeground(QColor("#3b82f6"))
        status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.browser_table_widget.setItem(row, 2, status_item)
        
        message_item = QTableWidgetItem("Checking email for OTP...")
        message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.browser_table_widget.setItem(row, 3, message_item)
        
        # Create thread to get OTP code
        thread = GetCodeThread(row, account)
        thread.code_received.connect(self.on_code_received)
        thread.log_message.connect(self.log)
        thread.start()
    
    def on_code_received(self, row, otp_code):
        """Handle OTP code received"""
        if otp_code:
            # Show OTP in a message box
            msg = QMessageBox(self)
            msg.setWindowTitle("OTP Code")
            msg.setText(f"OTP Code for row {row + 1}:")
            msg.setInformativeText(f"<h2 style='color: #10b981; font-size: 24pt;'>{otp_code}</h2>")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
            # Update table
            status_item = QTableWidgetItem("Code Ready")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor("#10b981"))
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(row, 2, status_item)
            
            message_item = QTableWidgetItem(f"OTP: {otp_code} - Please enter in browser")
            message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(row, 3, message_item)
        else:
            QMessageBox.warning(self, "Warning", f"Could not get OTP code for row {row + 1}")
            
            # Update table
            status_item = QTableWidgetItem("Code Failed")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor("#ef4444"))
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(row, 2, status_item)
            
            message_item = QTableWidgetItem("Failed to get OTP code")
            message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(row, 3, message_item)
    
    def start_veri_row(self, row):
        """Start verification for a specific row (only verify, assumes already logged in)"""
        # Check max concurrent browsers limit
        running_count = sum(1 for thread in self.automation_threads.values() if thread.isRunning())
        if running_count >= self.max_concurrent_browsers:
            self.log(f"⚠️ Maximum {self.max_concurrent_browsers} browsers already running. Please wait...")
            return
        
        if row >= len(self.accounts) or row >= len(self.veteran_data):
            QMessageBox.warning(self, "Warning", "Not enough accounts or data")
            return
        
        # Check if already running
        if row in self.automation_threads:
            thread = self.automation_threads[row]
            if thread.isRunning():
                QMessageBox.warning(self, "Warning", f"Row {row + 1} is already running")
                return
        
        # Get account and data
        account = self.accounts[row]
        
        # Tìm veteran_data đầu tiên chưa được sử dụng
        veteran = None
        veteran_index = None
        
        # Reset tracking nếu cần (khi load lại data)
        if len(self.veteran_data_in_use) != len(self.veteran_data):
            # Reset nếu số lượng data thay đổi
            available_indices = set(range(len(self.veteran_data)))
            in_use_indices = set(self.veteran_data_in_use.keys())
            # Chỉ giữ lại những index hợp lệ
            self.veteran_data_in_use = {k: v for k, v in self.veteran_data_in_use.items() 
                                       if k in available_indices and v}
        
        # Tìm veteran_data chưa được sử dụng
        for idx in range(len(self.veteran_data)):
            if idx not in self.veteran_data_in_use or not self.veteran_data_in_use[idx]:
                veteran = self.veteran_data[idx]
                veteran_index = idx
                # Đánh dấu là đang được sử dụng
                self.veteran_data_in_use[idx] = True
                break
        
        # Nếu tất cả đều đang được sử dụng, dùng theo row modulo (fallback)
        if veteran is None:
            veteran_index = row % len(self.veteran_data)
            veteran = self.veteran_data[veteran_index]
            self.veteran_data_in_use[veteran_index] = True
        
        self.log(f"Starting verification for row {row + 1}: {account.get('email', '')}")
        
        # Update table status
        status_item = QTableWidgetItem("Running")
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        status_item.setForeground(QColor("#3b82f6"))
        status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.browser_table_widget.setItem(row, 2, status_item)
        
        message_item = QTableWidgetItem("Starting verification...")
        message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.browser_table_widget.setItem(row, 3, message_item)
        
        # Get proxy if needed
        proxy_data = None
        if not self.use_direct_ip and row < len(self.proxies):
            proxy_data = self.proxies[row]
        
        # Disable buttons for this row
        self.set_row_buttons_enabled(row, False)
        
        # Create and start thread for verification only
        browser_id = f"{row}_{account.get('email', 'unknown')}"
        thread = VerificationThread(row, account, veteran, self.use_direct_ip, proxy_data, browser_id, veteran_index)
        # Pass row_number để hiển thị trong error message
        thread.row_number = row
        thread.status_update.connect(self.on_status_update)
        thread.log_message.connect(self.log)
        self.automation_threads[row] = thread
        thread.start()
    
    def on_status_update(self, row_index, status, message):
        """Handle status update from automation thread"""
        
        # XỬ LÝ Not Approved/Limit Exceeded TRƯỚC - tự động retry không dừng
        # Phải check TRƯỚC khi update UI để tránh buttons bị disabled
        if status in ["Not Approved", "Limit Exceeded"] and row_index in self.automation_threads:
            thread = self.automation_threads[row_index]
            if hasattr(thread, 'veteran_index') and thread.veteran_index is not None:
                veteran_idx = thread.veteran_index
                
                # Log thông báo
                if status == "Not Approved":
                    self.log(f"⚠️ Row {row_index + 1}: Not Approved - trying next veteran data...")
                elif status == "Limit Exceeded":
                    self.log(f"⚠️ Row {row_index + 1}: Limit Exceeded - trying next veteran data...")
                
                # Xóa veteran data đã fail
                self.remove_veteran_data(veteran_idx)
                
                # Kiểm tra xem còn veteran data nào không
                if len(self.veteran_data) == 0:
                    # Không còn data, set status là Failed
                    status_item = QTableWidgetItem("Failed")
                    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    status_item.setForeground(QColor("#ef4444"))
                    status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.browser_table_widget.setItem(row_index, 2, status_item)
                    
                    message_item = QTableWidgetItem("No more veteran data available")
                    message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.browser_table_widget.setItem(row_index, 3, message_item)
                    
                    self.set_row_buttons_enabled(row_index, True)
                    return
                
                # Tự động retry với veteran data khác (không dừng)
                # IMPORTANT: Gọi auto-retry TRƯỚC khi return
                self.auto_retry_with_new_veteran(row_index, thread.account_data, thread.use_proxy, thread.proxy_data)
                return  # Return sớm để không xử lý status này như "Failed"
        
        # Update status column - Match image exactly
        status_item = QTableWidgetItem(status)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Color coding - Match image colors exactly
        # Note: "Not Approved" và "Limit Exceeded" đã được xử lý ở trên (auto-retry)
        if status == "Ready!" or status == "Verified!":
            status_item.setForeground(QColor("#10b981"))  # Green
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            # Enable buttons when completed successfully
            self.set_row_buttons_enabled(row_index, True)
        elif status == "Cloudflare Detected":
            status_item.setForeground(QColor("#f59e0b"))  # Orange/Warning
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            # Enable buttons để user có thể retry sau khi xử lý Cloudflare
            self.set_row_buttons_enabled(row_index, True)
        elif status == "Failed" or status == "sourcesUnavailable" or status == "Error":
            status_item.setForeground(QColor("#ef4444"))  # Red
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            # Enable buttons when failed
            self.set_row_buttons_enabled(row_index, True)
        elif status == "Stopped":
            status_item.setForeground(QColor("#888888"))  # Gray
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
            # Enable buttons when stopped
            self.set_row_buttons_enabled(row_index, True)
        else:
            # Status is still running, don't release veteran_data yet
            pass
        
        # Release veteran_data khi verification hoàn thành (không phải Running)
        # Note: "Not Approved" và "Limit Exceeded" đã được xử lý ở trên và return sớm
        if status != "Running" and status not in ["Not Approved", "Limit Exceeded"] and row_index in self.automation_threads:
            thread = self.automation_threads[row_index]
            if hasattr(thread, 'veteran_index') and thread.veteran_index is not None:
                veteran_idx = thread.veteran_index
                
                # Xử lý theo từng trạng thái
                if status == "Verified!":
                    # Lưu log khi Verified!
                    self.save_verified_log(thread.account_data, thread.veteran_data, message)
                    # Xóa veteran data khỏi file và list
                    self.remove_veteran_data(veteran_idx)
                    
                elif status in ["Failed", "Error", "sourcesUnavailable"]:
                    # Release veteran_data để có thể thử lại sau
                    if veteran_idx in self.veteran_data_in_use:
                        self.veteran_data_in_use[veteran_idx] = False
        
        if status == "Running":
            status_item.setForeground(QColor("#3b82f6"))  # Blue
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            # Buttons are already disabled when starting
        else:
            status_item.setForeground(QColor("#d0d0d0"))
            # Enable buttons for unknown status
            self.set_row_buttons_enabled(row_index, True)
        
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.browser_table_widget.setItem(row_index, 2, status_item)
        
        # Format message to match image: "✓ Verified! [Name]" for success
        formatted_message = message
        if status == "Verified!" and "Verified!" in message:
            # Keep the format as is
            formatted_message = message
        elif status == "Ready!":
            # Keep the format as is for Ready!
            formatted_message = message
        elif status == "Not Approved":
            formatted_message = "⚠️ Not Approved - trying next data..."
        elif status == "Limit Exceeded":
            formatted_message = "⚠️ Limit Exceeded - trying next data..."
        elif status == "sourcesUnavailable":
            formatted_message = "🚫 VPN/PROXY Error: sourcesUnavailable detected. Please change VPN/PROXY and restart."
        elif status == "Error":
            formatted_message = message if message.startswith("❌") else f"❌ {message}"
        elif status == "Stopped":
            formatted_message = "Stopped by user"
        elif status == "Failed":
            # Format error message for better readability
            if "Browser đã bị đóng" in message or "element không tìm thấy" in message:
                formatted_message = f"✗ {message}"
            elif "timeout" in message.lower():
                formatted_message = f"✗ {message}"
            else:
                # Extract meaningful error
                if ":" in message:
                    parts = message.split(":", 1)
                    if len(parts) > 1:
                        formatted_message = f"✗ {parts[1].strip()}"
                    else:
                        formatted_message = f"✗ {message}"
                else:
                    formatted_message = f"✗ {message}" if not message.startswith("✗") else message
        
        message_item = QTableWidgetItem(formatted_message)
        message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.browser_table_widget.setItem(row_index, 3, message_item)
        
        # Remove thread from dict if finished
        if row_index in self.automation_threads:
            thread = self.automation_threads[row_index]
            if not thread.isRunning():
                del self.automation_threads[row_index]
                # Log available slots
                running_count = sum(1 for t in self.automation_threads.values() if t.isRunning())
                available = self.max_concurrent_browsers - running_count
                if available > 0:
                    self.log(f"✓ Slot available. {available}/{self.max_concurrent_browsers} browsers can be started.")
    
    def populate_table(self):
        """Populate table with accounts (max 10 rows)"""
        # Calculate number of rows to show (max 10)
        num_rows = min(len(self.accounts), self.max_concurrent_browsers)
        self.browser_table_widget.setRowCount(num_rows)
        
        # Fill rows with account data
        for i in range(num_rows):
            # Row number
            row_num_item = QTableWidgetItem(str(i + 1))
            row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(i, 0, row_num_item)
            
            # Email
            account = self.accounts[i]
            email_item = QTableWidgetItem(account.get('email', ''))
            email_item.setFlags(email_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(i, 1, email_item)
            
            # Status (empty initially) - Read-only
            status_item = QTableWidgetItem("—")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(i, 2, status_item)
            
            # Message (empty initially) - Read-only
            message_item = QTableWidgetItem("")
            message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(i, 3, message_item)
            
            # Retry button (Orange/Yellow) - Compact spacing like image
            btn_retry = QPushButton("Retry")
            btn_retry.setStyleSheet("""
                QPushButton {
                    background-color: #f59e0b;
                    color: white;
                    font-weight: 600;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 3px;
                    min-height: 20px;
                    max-height: 20px;
                }
                QPushButton:hover {
                    background-color: #d97706;
                }
                QPushButton:pressed {
                    background-color: #b45309;
                }
                QPushButton:disabled {
                    background-color: #6b7280;
                    color: #9ca3af;
                }
            """)
            btn_retry.clicked.connect(lambda checked, row=i: self.retry_row(row))
            self.browser_table_widget.setCellWidget(i, 4, btn_retry)
            
            # Reg/Login button (Green) - Compact spacing
            btn_reg_login = QPushButton("Reg/Login")
            btn_reg_login.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    font-weight: 600;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 3px;
                    min-height: 20px;
                    max-height: 20px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
                QPushButton:pressed {
                    background-color: #047857;
                }
                QPushButton:disabled {
                    background-color: #6b7280;
                    color: #9ca3af;
                }
            """)
            btn_reg_login.clicked.connect(lambda checked, row=i: self.reg_login_row(row))
            self.browser_table_widget.setCellWidget(i, 5, btn_reg_login)
            
            # Code button (Blue) - Compact spacing
            btn_code = QPushButton("Code")
            btn_code.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    font-weight: 600;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 3px;
                    min-height: 20px;
                    max-height: 20px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
                QPushButton:disabled {
                    background-color: #6b7280;
                    color: #9ca3af;
                }
            """)
            btn_code.clicked.connect(lambda checked, row=i: self.get_code_row(row))
            self.browser_table_widget.setCellWidget(i, 6, btn_code)
            
            # Start Veri button (Blue) - Compact spacing
            btn_start_veri = QPushButton("Start Veri")
            btn_start_veri.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    font-weight: 600;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 3px;
                    min-height: 20px;
                    max-height: 20px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
                QPushButton:disabled {
                    background-color: #6b7280;
                    color: #9ca3af;
                }
            """)
            btn_start_veri.clicked.connect(lambda checked, row=i: self.start_veri_row(row))
            self.browser_table_widget.setCellWidget(i, 7, btn_start_veri)
            
            # Clear button (Red) - Compact spacing
            btn_clear = QPushButton("Clear")
            btn_clear.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    font-weight: 600;
                    font-size: 8pt;
                    padding: 2px 6px;
                    border: none;
                    border-radius: 3px;
                    min-height: 20px;
                    max-height: 20px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
                QPushButton:pressed {
                    background-color: #b91c1c;
                }
                QPushButton:disabled {
                    background-color: #6b7280;
                    color: #9ca3af;
                }
            """)
            btn_clear.clicked.connect(lambda checked, row=i: self.clear_row(row))
            self.browser_table_widget.setCellWidget(i, 8, btn_clear)
    
    def update_accounts_label(self):
        """Update accounts label"""
        count = len(self.accounts)
        color = "#10b981" if count > 0 else "#888888"
        self.label_accounts.setText(f"Accounts: <span style='color: {color}; font-weight: 700;'>{count}</span> loaded")
    
    def update_data_label(self):
        """Update data label"""
        count = len(self.veteran_data)
        color = "#10b981" if count > 0 else "#888888"
        self.label_data.setText(f"Data: <span style='color: {color}; font-weight: 700;'>{count}</span> entries loaded")
    
    def format_error_message(self, error_msg):
        """Format error message để dễ đọc hơn"""
        if not error_msg:
            return error_msg
        
        # Format Playwright errors
        if "Page.wait_for_selector" in error_msg:
            if "Target page, context or browser has been closed" in error_msg:
                return "❌ Browser đã bị đóng - Không thể tìm thấy element"
            elif "timeout" in error_msg.lower():
                return "❌ Timeout - Không tìm thấy element sau thời gian chờ"
            else:
                return f"❌ Không tìm thấy element: {error_msg.split(':')[-1].strip()}"
        
        # Format common errors
        if "Target page, context or browser has been closed" in error_msg:
            return "❌ Browser đã bị đóng đột ngột"
        
        if "timeout" in error_msg.lower():
            return f"❌ Timeout: {error_msg}"
        
        if "not found" in error_msg.lower() or "không tìm thấy" in error_msg.lower():
            return f"❌ Không tìm thấy: {error_msg}"
        
        if "Error" in error_msg or "error" in error_msg:
            # Extract meaningful part
            if ":" in error_msg:
                parts = error_msg.split(":", 1)
                if len(parts) > 1:
                    return f"❌ {parts[0].strip()}: {parts[1].strip()}"
            return f"❌ {error_msg}"
        
        # Default: add error prefix if not present
        if not error_msg.startswith("❌") and not error_msg.startswith("✓"):
            if "failed" in error_msg.lower() or "error" in error_msg.lower():
                return f"❌ {error_msg}"
        
        return error_msg
    
    def log(self, message):
        """Add message to log với format đẹp"""
        # Check if it's an error message
        if "error" in message.lower() or "Error" in message or "failed" in message.lower():
            formatted_msg = self.format_error_message(message)
            self.log_text.append(f"[{self.get_timestamp()}] {formatted_msg}")
        else:
            self.log_text.append(f"[{self.get_timestamp()}] {message}")
        
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def get_timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%H:%M:%S")
    
    def remove_veteran_data(self, veteran_index: int):
        """Xóa veteran data khỏi list và file"""
        try:
            # Xóa khỏi list
            if 0 <= veteran_index < len(self.veteran_data):
                removed_data = self.veteran_data.pop(veteran_index)
                
                # Reset tracking cho các index sau veteran_index
                new_tracking = {}
                for idx in self.veteran_data_in_use:
                    if idx < veteran_index:
                        new_tracking[idx] = self.veteran_data_in_use[idx]
                    elif idx > veteran_index:
                        new_tracking[idx - 1] = self.veteran_data_in_use[idx]
                self.veteran_data_in_use = new_tracking
                
                # Xóa khỏi file nếu có đường dẫn
                if self.veteran_data_file_path and os.path.exists(self.veteran_data_file_path):
                    # Xóa dòng chính xác từ file
                    loader = FileLoader()
                    original_line = removed_data.get('original', '')
                    if original_line:
                        loader.remove_veteran_data_from_file(self.veteran_data_file_path, original_line)
                
                # Cập nhật UI
                self.update_data_label()
                self.log(f"✓ Removed veteran data: {removed_data.get('first', '')} {removed_data.get('last', '')}")
        except Exception as e:
            self.log(f"⚠️ Error removing veteran data: {str(e)}")
    
    def save_verified_log(self, account_data: dict, veteran_data: dict, message: str):
        """Lưu log khi verified vào folder /data/"""
        try:
            # Tạo folder data nếu chưa có
            current_file = os.path.abspath(__file__)
            tool_dir = os.path.dirname(os.path.dirname(current_file))  # Chatgpt_veterans_tool
            data_dir = os.path.join(tool_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"verified_{timestamp}.txt"
            file_path = os.path.join(data_dir, filename)
            
            # Format log content
            log_content = f"""=== VERIFIED LOG ===
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Account Email: {account_data.get('email', 'N/A')}
Veteran Name: {veteran_data.get('first', '')} {veteran_data.get('last', '')}
Branch: {veteran_data.get('branch', 'N/A')}
Birth Date: {veteran_data.get('month', '')}/{veteran_data.get('day', '')}/{veteran_data.get('year', '')}
Status: {message}
Original Data: {veteran_data.get('original', 'N/A')}
========================
"""
            
            # Ghi vào file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            self.log(f"✓ Verified log saved: {filename}")
        except Exception as e:
            self.log(f"⚠️ Error saving verified log: {str(e)}")
    
    def auto_retry_with_new_veteran(self, row_index: int, account_data: dict, use_proxy: bool, proxy_data: dict):
        """Tự động retry với veteran data khác khi Not Approved/Limit Exceeded"""
        try:
            # Kiểm tra xem còn veteran data nào không
            if len(self.veteran_data) == 0:
                self.log(f"⚠️ Row {row_index + 1}: No more veteran data available")
                # Set status to Failed
                status_item = QTableWidgetItem("Failed")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setForeground(QColor("#ef4444"))
                status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.browser_table_widget.setItem(row_index, 2, status_item)
                
                message_item = QTableWidgetItem("No more veteran data available")
                message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.browser_table_widget.setItem(row_index, 3, message_item)
                
                self.set_row_buttons_enabled(row_index, True)
                return
            
            # Tìm veteran data chưa được sử dụng
            veteran = None
            veteran_index = None
            
            for idx in range(len(self.veteran_data)):
                if idx not in self.veteran_data_in_use or not self.veteran_data_in_use[idx]:
                    veteran = self.veteran_data[idx]
                    veteran_index = idx
                    self.veteran_data_in_use[idx] = True
                    break
            
            # Nếu tất cả đều đang được sử dụng, đợi một chút
            if veteran is None:
                self.log(f"⚠️ Row {row_index + 1}: All veteran data in use, will retry later...")
                # Set status to Waiting
                status_item = QTableWidgetItem("Waiting")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setForeground(QColor("#f59e0b"))
                status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.browser_table_widget.setItem(row_index, 2, status_item)
                
                message_item = QTableWidgetItem("Waiting for available veteran data...")
                message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.browser_table_widget.setItem(row_index, 3, message_item)
                
                # Release để có thể thử lại sau
                self.set_row_buttons_enabled(row_index, True)
                return
            
            # Đảm bảo thread cũ đã dừng và cleanup hoàn toàn trước khi tạo thread mới
            if row_index in self.automation_threads:
                old_thread = self.automation_threads[row_index]
                if old_thread.isRunning():
                    self.log(f"🛑 Row {row_index + 1}: Stopping old thread...")
                    old_thread.stop()
                    # Đợi thread dừng hoàn toàn (tối đa 5 giây)
                    if not old_thread.wait(5000):
                        self.log(f"⚠️ Row {row_index + 1}: Old thread did not stop in time, terminating...")
                        old_thread.terminate()
                        old_thread.wait(1000)
                
                # Cleanup automation object
                if hasattr(old_thread, 'automation') and old_thread.automation:
                    try:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(old_thread.automation.cleanup())
                        loop.close()
                    except Exception as e:
                        self.log(f"⚠️ Cleanup error: {str(e)}")
                
                # Xóa thread cũ khỏi dict
                del self.automation_threads[row_index]
            
            # Đợi thêm để đảm bảo browser cũ đã đóng hoàn toàn
            import time
            time.sleep(3)  # Tăng delay lên 3 giây để browser cũ đóng hoàn toàn
            
            # Tự động retry với veteran data mới
            self.log(f"🔄 Row {row_index + 1}: Auto-retry with new veteran data: {veteran.get('first', '')} {veteran.get('last', '')}")
            
            # Update status TRƯỚC khi tạo thread mới
            status_item = QTableWidgetItem("Running")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor("#3b82f6"))
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(row_index, 2, status_item)
            
            message_item = QTableWidgetItem(f"Retrying with: {veteran.get('first', '')} {veteran.get('last', '')} ({veteran.get('branch', '')})")
            message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.browser_table_widget.setItem(row_index, 3, message_item)
            
            # Disable buttons
            self.set_row_buttons_enabled(row_index, False)
            
            # Create and start new thread
            browser_id = f"{row_index}_{account_data.get('email', 'unknown')}"
            thread = VerificationThread(row_index, account_data, veteran, use_proxy, proxy_data, browser_id, veteran_index)
            # Pass row_number để hiển thị trong error message
            thread.row_number = row_index
            thread.status_update.connect(self.on_status_update)
            thread.log_message.connect(self.log)
            self.automation_threads[row_index] = thread
            thread.start()
            
            self.log(f"✓ Row {row_index + 1}: Auto-retry started with new veteran data")
        except Exception as e:
            self.log(f"❌ Error in auto-retry: {str(e)}")
            import traceback
            self.log(f"❌ Traceback: {traceback.format_exc()}")
            # Enable buttons nếu có lỗi
            self.set_row_buttons_enabled(row_index, True)
    
    def save_config(self):
        """Save configuration"""
        config = {
            'accounts_count': len(self.accounts),
            'proxies_count': len(self.proxies),
            'data_count': len(self.veteran_data),
            'use_direct_ip': self.use_direct_ip
        }
        Config.save(config)
    
    def load_config(self):
        """Load configuration"""
        config = Config.load()
        if config:
            self.use_direct_ip = config.get('use_direct_ip', True)
            self.checkbox_direct_ip.setChecked(self.use_direct_ip)

