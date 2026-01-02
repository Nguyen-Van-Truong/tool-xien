#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT Auto Signup - Python GUI Application (PyQt6)
Tự động đăng ký tài khoản ChatGPT với GUI và đa luồng
"""

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QMessageBox, QTextEdit,
                             QSpinBox, QLineEdit, QGroupBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCharFormat, QTextCursor
import threading
import queue
import json
import time
import random
import re
import os
import tempfile
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import requests
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False


class LogSignal(QObject):
    """Signal for thread-safe logging"""
    log_message = pyqtSignal(str, str)  # message, tag


class ChatGPTSignupGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatGPT Auto Signup - Python GUI")
        self.setGeometry(100, 100, 450, 900)  # Portrait orientation
        
        # State variables
        self.data_list = []
        self.is_running = False
        self.stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'exists': 0
        }
        self.success_accounts = []
        self.exists_accounts = []
        self.failed_accounts = []
        self.threads = []
        self.max_threads = 1
        self.thread_lock = threading.Lock()
        self.driver_creation_lock = threading.Lock()  # Lock to prevent chromedriver conflicts
        self.current_index = 0
        self.summary_shown = False
        
        # Queue for thread-safe GUI updates
        self.message_queue = queue.Queue()
        self.log_signal = LogSignal()
        self.log_signal.log_message.connect(self._append_log)
        
        # Initialize file logging
        self.log_file = open('debug.log', 'a', encoding='utf-8')
        self.log_file.write(f"\n\n{'='*60}\nNew session started at {datetime.now().isoformat()}\n{'='*60}\n")
        
        # Setup dark theme
        self.setup_dark_theme()
        
        # Setup UI
        self.setup_ui()
        
        # Timer for checking queue
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.check_queue)
        self.queue_timer.start(100)
        
        # Load saved data
        self.load_saved_data()
    
    def setup_dark_theme(self):
        """Setup dark theme"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Set stylesheet for better dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #fff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #fff;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: #fff;
            }
            QLineEdit:focus {
                border: 1px solid #3a9eff;
            }
            QSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: #fff;
            }
            QTextEdit {
                background-color: #252526;
                border: 1px solid #555;
                border-radius: 3px;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
            }
        """)
    
    def setup_ui(self):
        """Setup the UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("ChatGPT Auto Signup")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #4ec9b0; margin-bottom: 5px;")
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Tự động đăng ký tài khoản ChatGPT")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #858585; margin-bottom: 15px;")
        main_layout.addWidget(subtitle_label)
        
        # File selection group
        file_group = QGroupBox("📁 Data File")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(10)
        
        file_button_layout = QHBoxLayout()
        self.load_file_btn = self.create_button("📂 Load Data File", "#4a9eff", "#5aaeff", self.load_data_file)
        file_button_layout.addWidget(self.load_file_btn)
        file_layout.addLayout(file_button_layout)
        
        self.file_path_label = QLabel("No file loaded")
        self.file_path_label.setStyleSheet("color: #858585; padding: 5px;")
        self.file_path_label.setWordWrap(True)
        file_layout.addWidget(self.file_path_label)
        
        self.data_count_label = QLabel("0 accounts")
        self.data_count_label.setStyleSheet("color: #4ec9b0; font-weight: bold; padding: 5px;")
        file_layout.addWidget(self.data_count_label)
        main_layout.addWidget(file_group)
        
        # Settings group
        settings_group = QGroupBox("⚙️ Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)
        
        threads_layout = QHBoxLayout()
        threads_label = QLabel("Max Threads:")
        threads_label.setStyleSheet("color: #fff;")
        threads_layout.addWidget(threads_label)
        self.threads_spinbox = QSpinBox()
        self.threads_spinbox.setRange(1, 10)
        self.threads_spinbox.setValue(1)
        self.threads_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: #fff;
                min-width: 60px;
            }
        """)
        threads_layout.addWidget(self.threads_spinbox)
        threads_layout.addStretch()
        settings_layout.addLayout(threads_layout)
        
        browser_layout = QVBoxLayout()
        browser_label = QLabel("Browser Path:")
        browser_label.setStyleSheet("color: #fff;")
        browser_layout.addWidget(browser_label)
        
        browser_path_layout = QHBoxLayout()
        self.browser_path_edit = QLineEdit()
        self.browser_path_edit.setPlaceholderText("Select browser executable...")
        browser_path_layout.addWidget(self.browser_path_edit)
        
        browse_btn = self.create_button("Browse...", "#6c757d", "#7c858d", self.browse_browser_path)
        browse_btn.setMaximumWidth(100)
        browser_path_layout.addWidget(browse_btn)
        
        auto_find_btn = self.create_button("Auto Find", "#6c757d", "#7c858d", self.auto_find_browser)
        auto_find_btn.setMaximumWidth(100)
        browser_path_layout.addWidget(auto_find_btn)
        browser_layout.addLayout(browser_path_layout)
        settings_layout.addLayout(browser_layout)
        main_layout.addWidget(settings_group)
        
        # Statistics group - Compact horizontal layout (centered)
        stats_group = QGroupBox("📊 Thống Kê")
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.setSpacing(15)
        stats_layout.setContentsMargins(10, 15, 10, 10)
        
        # Add stretch before stats to center them
        stats_layout.addStretch()
        
        # Create compact stat items
        self.total_label = self.create_compact_stat("Tổng số", "0", "#858585", stats_layout)
        self.processed_label = self.create_compact_stat("Đã xử lý", "0", "#4a9eff", stats_layout)
        self.success_label = self.create_compact_stat("Success", "0", "#27ae60", stats_layout)
        self.exists_label = self.create_compact_stat("Exists", "0", "#f39c12", stats_layout)
        self.failed_label = self.create_compact_stat("Failed", "0", "#e74c3c", stats_layout)
        
        # Add stretch after stats to center them
        stats_layout.addStretch()
        main_layout.addWidget(stats_group)
        
        # Control buttons - Horizontal layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.start_btn = self.create_button("▶ START", "#27ae60", "#229954", self.start_signup)
        self.start_btn.setEnabled(False)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = self.create_button("■ STOP", "#e74c3c", "#c0392b", self.stop_signup)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        save_btn = self.create_button("💾 Save", "#3498db", "#2980b9", self.save_success_accounts)
        buttons_layout.addWidget(save_btn)
        
        clear_btn = self.create_button("🗑️ Clear", "#95a5a6", "#7f8c8d", self.clear_stats)
        buttons_layout.addWidget(clear_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Log area
        log_group = QGroupBox("📝 Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)
        
        # Set stretch factors
        main_layout.setStretchFactor(log_group, 1)
    
    def create_button(self, text, color, hover_color, callback):
        """Create a styled button with hover effect"""
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {color};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #888;
            }}
        """)
        btn.clicked.connect(callback)
        return btn
    
    def create_stat_row(self, label_text, value, color, layout):
        """Create a statistics row"""
        row_layout = QHBoxLayout()
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #fff; font-weight: bold;")
        label.setMinimumWidth(100)
        row_layout.addWidget(label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14pt;")
        row_layout.addWidget(value_label)
        row_layout.addStretch()
        
        layout.addLayout(row_layout)
        return value_label
    
    def create_compact_stat(self, label_text, value, color, layout):
        """Create a compact statistics item (horizontal layout)"""
        stat_widget = QWidget()
        stat_layout = QVBoxLayout(stat_widget)
        stat_layout.setSpacing(2)
        stat_layout.setContentsMargins(5, 0, 5, 0)
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #aaa; font-size: 9pt;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stat_layout.addWidget(label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18pt;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stat_layout.addWidget(value_label)
        
        layout.addWidget(stat_widget)
        return value_label
    
    def log(self, message, tag="info"):
        """Thread-safe logging"""
        self.message_queue.put(("log", message, tag))
        # Also write to file
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_file.write(f"[{timestamp}] [{tag.upper()}] {message}\n")
            self.log_file.flush()
        except:
            pass
    
    def _append_log(self, message, tag):
        """Append log message to text edit"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Set text format based on tag
        format = QTextCharFormat()
        if tag == "success":
            format.setForeground(QColor("#2ecc71"))
            format.setFontWeight(QFont.Weight.Bold)
        elif tag == "error":
            format.setForeground(QColor("#e74c3c"))
            format.setFontWeight(QFont.Weight.Bold)
        elif tag == "warning":
            format.setForeground(QColor("#f39c12"))
        else:  # info
            format.setForeground(QColor("#3498db"))
        
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{timestamp}] {message}\n", format)
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
    
    def update_stats_display(self):
        """Thread-safe stats update"""
        self.message_queue.put(("stats", self.stats.copy()))
    
    def check_queue(self):
        """Process messages from queue"""
        try:
            while True:
                msg_type, *args = self.message_queue.get_nowait()
                if msg_type == "log":
                    message, tag = args
                    self.log_signal.log_message.emit(message, tag)
                elif msg_type == "stats":
                    stats = args[0]
                    self.total_label.setText(str(len(self.data_list)))
                    self.processed_label.setText(str(stats['processed']))
                    self.success_label.setText(str(stats['success']))
                    self.exists_label.setText(str(stats['exists']))
                    self.failed_label.setText(str(stats['failed']))
                elif msg_type == "check_completion":
                    self.check_all_completed()
        except queue.Empty:
            pass
    
    def load_data_file(self):
        """Load data from text file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Data File",
            "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse data
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            parsed_data = []
            
            for line in lines:
                # Skip comment lines
                if line.startswith('#'):
                    continue
                    
                parts = [p.strip() for p in line.split('|')]
                
                # Format 1: 6 fields (email|pass|emailLogin|passEmail|refreshToken|clientId)
                if len(parts) >= 6:
                    parsed_data.append({
                        'email': parts[0],
                        'password': parts[1],
                        'emailLogin': parts[2],
                        'passEmail': parts[3],
                        'refreshToken': parts[4],
                        'clientId': parts[5],
                        'original': line
                    })
                # Format 2: 4 fields (email|pass|refreshToken|clientId) - email same as emailLogin
                elif len(parts) >= 4:
                    parsed_data.append({
                        'email': parts[0],
                        'password': parts[1],
                        'emailLogin': parts[0],  # Same as email
                        'passEmail': parts[1],   # Same as password
                        'refreshToken': parts[2],
                        'clientId': parts[3],
                        'original': line
                    })
            
            self.data_list = parsed_data
            self.file_path_label.setText(file_path)
            self.file_path_label.setStyleSheet("color: #4ec9b0; padding: 5px;")
            self.data_count_label.setText(f"{len(parsed_data)} accounts")
            self.start_btn.setEnabled(len(parsed_data) > 0)
            
            self.log(f"✅ Loaded {len(parsed_data)} accounts from file", "success")
            self.save_data_to_file()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            self.log(f"❌ Error loading file: {str(e)}", "error")
    
    def save_data_to_file(self):
        """Save current state to JSON file"""
        try:
            data = {
                'data_list': self.data_list,
                'stats': self.stats,
                'success_accounts': self.success_accounts,
                'exists_accounts': self.exists_accounts,
                'failed_accounts': self.failed_accounts,
                'browser_path': self.browser_path_edit.text()
            }
            with open('signup_state.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"⚠️ Could not save state: {str(e)}", "warning")
    
    def browse_browser_path(self):
        """Browse and select browser executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Browser Executable",
            "C:\\Program Files",
            "Executable files (*.exe);;All files (*.*)"
        )
        if file_path:
            self.browser_path_edit.setText(file_path)
            self.log(f"✅ Browser path set: {file_path}", "success")
            self.save_data_to_file()
    
    def auto_find_browser(self):
        """Auto find browser executables"""
        import shutil
        
        # Common browser paths
        browser_paths = {
            "Chrome": [
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],
            "Brave": [
                os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            ],
            "Edge": [
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ],
            "Opera": [
                os.path.expanduser(r"~\AppData\Local\Programs\Opera\opera.exe"),
                r"C:\Program Files\Opera\opera.exe",
            ]
        }
        
        found_browsers = []
        for browser_name, paths in browser_paths.items():
            for path in paths:
                if os.path.exists(path):
                    found_browsers.append((browser_name, path))
                    break
        
        # Also try to find in PATH
        browsers_in_path = ["chrome.exe", "brave.exe", "msedge.exe", "opera.exe"]
        for browser_exe in browsers_in_path:
            browser_path = shutil.which(browser_exe)
            if browser_path:
                browser_name = browser_exe.replace(".exe", "").capitalize()
                found_browsers.append((browser_name, browser_path))
        
        if found_browsers:
            # Use first found browser
            browser_name, browser_path = found_browsers[0]
            self.browser_path_edit.setText(browser_path)
            self.log(f"✅ Auto found {browser_name}: {browser_path}", "success")
            if len(found_browsers) > 1:
                self.log(f"ℹ️ Also found: {', '.join([f'{name} ({path})' for name, path in found_browsers[1:]])}", "info")
            self.save_data_to_file()
        else:
            QMessageBox.information(self, "Info", "No browsers found automatically. Please browse manually.")
            self.log("⚠️ No browsers found automatically", "warning")
    
    def load_saved_data(self):
        """Load saved state from JSON file"""
        try:
            with open('signup_state.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.data_list = data.get('data_list', [])
                # Only load data_list, not stats - stats will be reset to 0
                # This prevents showing old stats when just starting the tool
                browser_path = data.get('browser_path', '')
                
                if browser_path:
                    self.browser_path_edit.setText(browser_path)
                
                if self.data_list:
                    self.file_path_label.setText("Loaded from saved state")
                    self.file_path_label.setStyleSheet("color: #4a9eff; padding: 5px;")
                    self.data_count_label.setText(f"{len(self.data_list)} accounts")
                    self.start_btn.setEnabled(True)
                    # Update stats display (will show 0 for all stats since we reset them)
                    self.update_stats_display()
        except FileNotFoundError:
            pass
        except Exception as e:
            self.log(f"⚠️ Could not load saved state: {str(e)}", "warning")
    
    def start_signup(self):
        """Start signup process"""
        if not self.data_list:
            QMessageBox.warning(self, "Warning", "Please load data file first!")
            return
        
        self.is_running = True
        self.summary_shown = False
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Reset index to start from beginning or continue from processed
        with self.thread_lock:
            self.current_index = self.stats['processed']
        
        self.max_threads = self.threads_spinbox.value()
        self.log(f"🚀 Starting signup with {self.max_threads} threads", "info")
        
        # Clear old threads
        self.threads = []
        
        # Start worker threads
        for i in range(self.max_threads):
            thread = threading.Thread(target=self.worker_thread, daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def stop_signup(self):
        """Stop signup process"""
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("⏹️ Signup stopped", "warning")
    
    def worker_thread(self):
        """Worker thread to process accounts"""
        while self.is_running:
            # Get next unprocessed account (thread-safe)
            account = None
            account_index = -1
            
            with self.thread_lock:
                if self.current_index < len(self.data_list):
                    account_index = self.current_index
                    account = self.data_list[account_index]
                    self.current_index += 1
                else:
                    break  # All accounts processed
            
            if not account:
                break
            
            try:
                self.log(f"🔄 Processing {account_index + 1}/{len(self.data_list)}: {account['email']}", "info")
                self.process_account(account, account_index)
            except Exception as e:
                self.log(f"❌ Thread error: {str(e)}", "error")
                with self.thread_lock:
                    self.stats['failed'] += 1
                    self.stats['processed'] += 1
                    account_data = {
                        'email': account['email'],
                        'password': account['password'],
                        'emailLogin': account.get('emailLogin', ''),
                        'passEmail': account.get('passEmail', ''),
                        'refreshToken': account.get('refreshToken', ''),
                        'clientId': account.get('clientId', ''),
                        'original': account.get('original', ''),
                        'timestamp': datetime.now().isoformat(),
                        'reason': f'Thread Error: {str(e)}'
                    }
                    self.failed_accounts.append(account_data)
                    self.update_stats_display()
                    self.save_data_to_file()
                    self.message_queue.put(("check_completion",))
    
    def process_account(self, account, index):
        """Process a single account"""
        driver = None
        thread_id = threading.get_ident()
        profile_dir = None
        otp_requested = False  # Flag to track if OTP flow was triggered (signup vs login)
        
        try:
            # Create unique profile directory for THIS account (each account gets its own profile)
            profile_base = os.path.join(tempfile.gettempdir(), 'chatgpt_signup_profiles')
            os.makedirs(profile_base, exist_ok=True)
            # Use thread_id, index, and timestamp to ensure uniqueness
            profile_dir = os.path.join(profile_base, f'profile_t{thread_id}_a{index}_{int(time.time() * 1000)}')
            os.makedirs(profile_dir, exist_ok=True)
            
            # Get browser path from user selection
            browser_path = self.browser_path_edit.text().strip()
            
            # Use custom browser path if provided
            browser_executable = None
            if browser_path and os.path.exists(browser_path):
                browser_executable = browser_path
                browser_name = os.path.basename(browser_path)
                self.log(f"✅ Using custom browser: {browser_name} ({browser_path})", "info")
            else:
                # Auto-find if path not set or invalid
                if browser_path:
                    self.log(f"⚠️ Browser path not found: {browser_path}, trying auto-find...", "warning")
                
                # Try to find browser automatically
                import shutil
                browser_paths_to_try = [
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                    os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
                    os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                ]
                
                for path in browser_paths_to_try:
                    if os.path.exists(path):
                        browser_executable = path
                        break
                
                if not browser_executable:
                    # Try in PATH
                    for exe_name in ["chrome.exe", "brave.exe", "msedge.exe"]:
                        browser_executable = shutil.which(exe_name)
                        if browser_executable:
                            break
                
                if browser_executable:
                    browser_name = os.path.basename(browser_executable)
                    self.log(f"✅ Auto-using browser: {browser_name} ({browser_executable})", "info")
                else:
                    self.log("⚠️ No browser found, using default ChromeDriver", "warning")
            
            # Use lock to prevent chromedriver file conflicts when multiple threads start simultaneously
            with self.driver_creation_lock:
                # Use undetected-chromedriver to avoid bot detection (REAL BROWSER MODE)
                if UC_AVAILABLE:
                    try:
                        self.log("🚀 Starting browser in REAL mode (undetected-chromedriver)...", "info")
                        
                        # Create options for undetected-chromedriver
                        uc_options = uc.ChromeOptions()
                        uc_options.add_argument(f'--user-data-dir={profile_dir}')
                        uc_options.add_argument('--disable-dev-shm-usage')
                        uc_options.add_argument('--no-sandbox')
                        uc_options.add_argument('--disable-gpu')
                        
                        # Try to use undetected-chromedriver with error handling
                        try:
                            # Use custom browser executable if provided
                            if browser_executable:
                                driver = uc.Chrome(
                                    browser_executable_path=browser_executable,
                                    user_data_dir=profile_dir,
                                    options=uc_options,
                                    version_main=None,  # Auto-detect Chrome version
                                    use_subprocess=True
                                )
                            else:
                                driver = uc.Chrome(
                                    user_data_dir=profile_dir,
                                    options=uc_options,
                                    version_main=None,
                                    use_subprocess=True
                                )
                            
                            self.log("✅ Browser opened in REAL mode (not detected as bot)", "success")
                        except (OSError, ConnectionError) as network_error:
                            # Network error when trying to download ChromeDriver - fallback immediately
                            self.log(f"⚠️ Network error with undetected-chromedriver (cannot download ChromeDriver): {str(network_error)}", "warning")
                            self.log("⚠️ Falling back to regular Chrome...", "warning")
                            raise  # Re-raise to trigger fallback
                        except Exception as uc_error:
                            # Check if it's a URL/network related error
                            error_str = str(uc_error).lower()
                            if 'urlopen error' in error_str or 'unreachable host' in error_str or 'socket operation' in error_str:
                                self.log(f"⚠️ Network error with undetected-chromedriver (cannot download ChromeDriver): {str(uc_error)}", "warning")
                                self.log("⚠️ Falling back to regular Chrome...", "warning")
                            else:
                                self.log(f"⚠️ undetected-chromedriver error: {str(uc_error)}", "warning")
                                self.log("⚠️ Falling back to regular Chrome...", "warning")
                            raise  # Re-raise to trigger fallback
                    except Exception as e:
                        # Fallback to regular Chrome
                        chrome_options = Options()
                        chrome_options.add_argument(f'--user-data-dir={profile_dir}')
                        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                        chrome_options.add_experimental_option('useAutomationExtension', False)
                        if browser_executable:
                            chrome_options.binary_location = browser_executable
                        driver = webdriver.Chrome(options=chrome_options)
                        self.log("✅ Using regular Chrome (with anti-detection flags)", "info")
                else:
                    # Fallback: Use regular Chrome with minimal automation flags
                    self.log("⚠️ undetected-chromedriver not available, using regular Chrome (may be detected)", "warning")
                    chrome_options = Options()
                    chrome_options.add_argument(f'--user-data-dir={profile_dir}')
                    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    chrome_options.add_experimental_option('useAutomationExtension', False)
                    if browser_executable:
                        chrome_options.binary_location = browser_executable
                    driver = webdriver.Chrome(options=chrome_options)
            
            # Lock released - driver created successfully
            driver.set_page_load_timeout(30)
            
            # Auto-arrange browser windows in grid layout
            try:
                # Window size settings - larger size to prevent layout issues
                window_width = 800
                window_height = 900
                
                # Calculate grid position based on index
                # Get screen size (default to 1920x1080 if not available)
                screen_width = 1920
                screen_height = 1080
                
                # Calculate how many windows fit per row
                cols = max(1, screen_width // window_width)
                
                # Calculate row and column for this window
                col = index % cols
                row = index // cols
                
                # Calculate position
                x_pos = col * window_width
                y_pos = row * window_height
                
                # Set window to FULLSCREEN for faster operation
                driver.maximize_window()
                
                self.log(f"🪟 Window {index + 1}: FULLSCREEN", "info")
            except Exception as e:
                self.log(f"⚠️ Could not arrange window: {str(e)}", "warning")
            
            # Navigate to ChatGPT
            self.log(f"🌐 Navigating to ChatGPT for {account['email']}", "info")
            driver.get('https://chatgpt.com')
            
            # Simulate human-like behavior: random delay
            time.sleep(random.uniform(3, 5))
            
            # Simulate mouse movement and scrolling (human-like behavior)
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(random.uniform(0.5, 1.5))
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(0.5, 1))
            except:
                pass
            
            # Check if already logged in (should not be in incognito, but check anyway)
            # If logged in, it might mean account already exists from previous session
            if self.is_logged_in(driver):
                self.log(f"⚠️ Already logged in state detected for {account['email']}, skipping...", "warning")
                with self.thread_lock:
                    self.stats['exists'] += 1
                    self.stats['processed'] += 1
                    self.update_stats_display()
                driver.quit()
                return
            
            # Click Sign Up button
            self.click_signup_button(driver)
            time.sleep(2)
            
            # Fill email
            self.fill_email(driver, account['email'])
            time.sleep(2)
            
            # Check URL state after email - browser may skip password page
            current_url = driver.current_url
            self.log(f"🔍 After email, URL is: {current_url[:60]}...", "info")
            
            # Case 1: Already on OTP/verification page (browser remembered password)
            if 'email-verification' in current_url or 'verify' in current_url.lower():
                self.log(f"📧 Browser skipped password, already on OTP page for {account['email']}", "info")
                otp_requested = True  # Mark as signup flow
                # Continue to OTP handling below
            
            # Case 2: On password page (create-account or log-in)
            elif 'auth.openai.com' in current_url and 'password' in current_url:
                is_login = 'log-in' in current_url
                if is_login:
                    self.log(f"🔐 On LOGIN password page for {account['email']}", "info")
                else:
                    self.log(f"🔐 On SIGNUP password page for {account['email']}", "info")
                
                # Fill password with retry
                password_filled = self.fill_password_with_retry(driver, account['password'])
                if not password_filled:
                    raise Exception("Failed to fill password after retries")
                time.sleep(3)
                
                # If login, no OTP expected
                if is_login:
                    otp_requested = False
            
            # Case 3: Still on same page or chatgpt.com
            elif 'chatgpt.com' in current_url:
                # May already be logged in, check
                if self.is_logged_in(driver):
                    self.log(f"✅ Already logged in after email for {account['email']}", "success")
                    otp_requested = False
                else:
                    # Try to fill password anyway
                    try:
                        self.fill_password_with_retry(driver, account['password'])
                        time.sleep(3)
                    except:
                        self.log(f"⚠️ No password form found, checking state...", "warning")
            
            # Case 4: Other auth.openai.com pages
            else:
                # Try to fill password
                try:
                    self.fill_password_with_retry(driver, account['password'])
                    time.sleep(3)
                except Exception as e:
                    self.log(f"⚠️ Password fill failed: {str(e)}, checking URL...", "warning")
            
            # Handle OTP verification with retry logic
            if 'email-verification' in driver.current_url or 'verify' in driver.current_url.lower():
                self.log(f"📧 On email verification page for {account['email']}", "info")
                otp_requested = True  # Mark as signup flow (OTP was requested)
                time.sleep(10)  # Wait for email to be sent
                
                # Handle OTP with retry (max 2 retries)
                result = self.handle_otp_verification_with_retry(driver, account, retry_count=0)
                
                if result['status'] == 'account_banned':
                    # Account is banned/locked
                    self.log(f"❌ Account banned/locked for {account['email']}", "error")
                    with self.thread_lock:
                        self.stats['failed'] += 1
                        self.stats['processed'] += 1
                        account_data = {
                            'email': account['email'],
                            'password': account['password'],
                            'emailLogin': account['emailLogin'],
                            'passEmail': account['passEmail'],
                            'refreshToken': account['refreshToken'],
                            'clientId': account['clientId'],
                            'original': account['original'],
                            'timestamp': datetime.now().isoformat(),
                            'reason': 'Banned/Locked'
                        }
                        self.failed_accounts.append(account_data)
                        self.update_stats_display()
                        self.save_data_to_file()
                        self.message_queue.put(("check_completion",))
                    driver.quit()
                    return
                elif result['status'] == 'otp_failed':
                    # OTP failed after 2 retries - skip this account
                    self.log(f"❌ OTP verification failed after retries for {account['email']}", "error")
                    with self.thread_lock:
                        self.stats['failed'] += 1
                        self.stats['processed'] += 1
                        account_data = {
                            'email': account['email'],
                            'password': account['password'],
                            'emailLogin': account['emailLogin'],
                            'passEmail': account['passEmail'],
                            'refreshToken': account['refreshToken'],
                            'clientId': account['clientId'],
                            'original': account['original'],
                            'timestamp': datetime.now().isoformat(),
                            'reason': 'OTP Failed'
                        }
                        self.failed_accounts.append(account_data)
                        self.update_stats_display()
                        self.save_data_to_file()
                        self.message_queue.put(("check_completion",))
                    driver.quit()
                    return
                elif result['status'] == 'account_exists':
                    # Account already exists - redirected to homepage
                    self.log(f"ℹ️ Account already exists for {account['email']}", "info")
                    with self.thread_lock:
                        self.stats['exists'] += 1
                        self.stats['processed'] += 1
                        account_data = {
                            'email': account['email'],
                            'password': account['password'],
                            'emailLogin': account['emailLogin'],
                            'passEmail': account['passEmail'],
                            'refreshToken': account['refreshToken'],
                            'clientId': account['clientId'],
                            'original': account['original'],
                            'timestamp': datetime.now().isoformat()
                        }
                        self.exists_accounts.append(account_data)
                        self.update_stats_display()
                        self.save_data_to_file()
                        self.message_queue.put(("check_completion",))
                    driver.quit()
                    return
                elif result['status'] == 'success':
                    # OTP verified successfully - check next step
                    pass  # Continue to check for About You page or homepage
                else:
                    raise Exception(f"Unknown OTP verification result: {result['status']}")
            
            # Handle About You page (for new accounts)
            if 'about-you' in driver.current_url:
                self.log(f"📝 On About You page for {account['email']}", "info")
                self.fill_about_you(driver, account)
                time.sleep(5)
            
            # Check final status
            time.sleep(3)
            current_url = driver.current_url
            
            # Check for error page (account banned)
            if self.check_for_error_page(driver):
                self.log(f"❌ Account error/banned detected for {account['email']}", "error")
                with self.thread_lock:
                    self.stats['failed'] += 1
                    self.stats['processed'] += 1
                    account_data = {
                        'email': account['email'],
                        'password': account['password'],
                        'emailLogin': account['emailLogin'],
                        'passEmail': account['passEmail'],
                        'refreshToken': account['refreshToken'],
                        'clientId': account['clientId'],
                        'original': account['original'],
                        'timestamp': datetime.now().isoformat(),
                        'reason': 'Banned/Blocked/Error'
                    }
                    self.failed_accounts.append(account_data)
                    self.update_stats_display()
                    self.save_data_to_file()
                    self.message_queue.put(("check_completion",))
                driver.quit()
                return
            
            # Check if on homepage (success - either new account or existing)
            if 'chatgpt.com' in current_url and 'auth' not in current_url and 'signup' not in current_url and 'verify' not in current_url:
                # If we reached homepage after going through auth flow, it's a success
                # Check if OTP was requested to determine if it's signup or login
                if otp_requested:
                    # OTP was requested = new signup
                    self.log(f"✅ Signup SUCCESS (new account) for {account['email']}", "success")
                    self.handle_success(account)
                else:
                    # No OTP = account already existed, this was a login
                    self.log(f"✅ Login SUCCESS (account exists) for {account['email']}", "success")
                    self.handle_exists(account)
                # driver.quit()  # Keep browser open for inspection
                return
            
            # Still on email-verification or auth page - wait and retry
            elif 'email-verification' in current_url or 'auth.openai.com' in current_url:
                self.log(f"⏳ Still on auth page, waiting for redirect for {account['email']}...", "info")
                
                # Wait for redirect (up to 30 seconds)
                for wait_check in range(15):
                    time.sleep(2)
                    current_url = driver.current_url
                    
                    # Check if redirected to homepage
                    if 'chatgpt.com' in current_url and 'auth' not in current_url and 'verify' not in current_url:
                        self.log(f"✅ Redirected to homepage for {account['email']}", "success")
                        if otp_requested:
                            self.handle_success(account)
                        else:
                            self.handle_exists(account)
                        # driver.quit()  # Keep browser open for inspection
                        return
                    
                    # Check if logged in by looking at page content
                    if self.is_logged_in(driver):
                        self.log(f"✅ Login detected for {account['email']}", "success")
                        self.handle_exists(account)
                        # driver.quit()  # Keep browser open for inspection
                        return
                
                # If still stuck after waiting, treat as exists (account likely valid)
                self.log(f"ℹ️ Account already exists for {account['email']}", "info")
                self.handle_exists(account)
                # driver.quit()  # Keep browser open for inspection
                return
            
            else:
                raise Exception(f"Unexpected URL after processing: {current_url}")
            
            # driver.quit()  # Keep browser open for inspection
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ Error for {account['email']}: {error_msg}", "error")
            
            # Check if account already exists
            if 'already' in error_msg.lower() or 'exists' in error_msg.lower() or 'registered' in error_msg.lower():
                with self.thread_lock:
                    self.stats['exists'] += 1
                    self.stats['processed'] += 1
                    account_data = {
                        'email': account['email'],
                        'password': account['password'],
                        'emailLogin': account['emailLogin'],
                        'passEmail': account['passEmail'],
                        'refreshToken': account['refreshToken'],
                        'clientId': account['clientId'],
                        'original': account['original'],
                        'timestamp': datetime.now().isoformat()
                    }
                    self.exists_accounts.append(account_data)
                    self.update_stats_display()
                    self.save_data_to_file()
                    self.message_queue.put(("check_completion",))
            else:
                with self.thread_lock:
                    self.stats['failed'] += 1
                    self.stats['processed'] += 1
                    account_data = {
                        'email': account['email'],
                        'password': account['password'],
                        'emailLogin': account['emailLogin'],
                        'passEmail': account['passEmail'],
                        'refreshToken': account['refreshToken'],
                        'clientId': account['clientId'],
                        'original': account['original'],
                        'timestamp': datetime.now().isoformat(),
                        'reason': error_msg
                    }
                    self.failed_accounts.append(account_data)
                    self.update_stats_display()
                    self.save_data_to_file()
                    self.message_queue.put(("check_completion",))
            
            if driver:
                try:
                    # driver.quit()  # Keep browser open for inspection
                    pass
                except:
                    pass
            
            # Clean up profile directory after use (each account gets fresh profile)
            if profile_dir and os.path.exists(profile_dir):
                try:
                    import shutil
                    time.sleep(1)  # Wait a bit for Chrome to fully close
                    shutil.rmtree(profile_dir, ignore_errors=True)
                except:
                    pass


    def is_logged_in(self, driver):
        """Check if user is logged in"""
        try:
            # Check for both textarea and sidebar
            textarea = driver.find_element(By.ID, "prompt-textarea")
            sidebar = driver.find_element(By.CSS_SELECTOR, '[data-testid="sidebar"]')
            return textarea and sidebar
        except:
            return False
    
    def click_signup_button(self, driver):
        """Click Sign Up button - follows extension JavaScript logic"""
        try:
            self.log("🔍 Looking for Sign up for free button...", "info")
            
            # Wait for page to fully load
            time.sleep(5)  # Wait longer for page to render
            
            # Strategy 1: Check if email input already exists (modal might be open)
            try:
                email_selectors = [
                    (By.CSS_SELECTOR, 'input[type="email"]'),
                    (By.CSS_SELECTOR, 'input[name*="email" i]'),
                    (By.CSS_SELECTOR, 'input[id*="email" i]'),
                    (By.CSS_SELECTOR, 'input[placeholder*="Email address" i]'),
                    (By.CSS_SELECTOR, 'input[placeholder*="email" i]')
                ]
                
                for by, selector in email_selectors:
                    try:
                        email_input = driver.find_element(by, selector)
                        if email_input and email_input.is_displayed():
                            self.log("ℹ️ Email form already visible, skipping button click", "info")
                            return
                    except:
                        continue
            except:
                pass
            
            # Strategy 2: Find button by scanning all buttons and links (MAIN strategy)
            # Try multiple times as page might still be loading
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    # Get all buttons and links
                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                    all_links = driver.find_elements(By.TAG_NAME, "a")
                    all_elements = all_buttons + all_links
                    
                    self.log(f"🔍 Scanning {len(all_elements)} elements (attempt {attempt + 1}/{max_attempts})...", "info")
                    
                    sign_up_button = None
                    
                    # Find element with exact text "Sign up for free" or variations
                    for element in all_elements:
                        try:
                            # Skip if element is not displayed
                            if not element.is_displayed():
                                continue
                            
                            # Get text - try multiple methods
                            text = ""
                            try:
                                text = element.text.strip()
                            except:
                                try:
                                    text = element.get_attribute("textContent") or ""
                                    text = text.strip()
                                except:
                                    try:
                                        text = element.get_attribute("innerText") or ""
                                        text = text.strip()
                                    except:
                                        pass
                            
                            if not text:
                                continue
                            
                            text_lower = text.lower()
                            
                            # Check for exact match "sign up for free" (PRIORITY)
                            if text_lower == "sign up for free" or text_lower.find("sign up for free") != -1:
                                sign_up_button = element
                                self.log(f"✅ Found button with exact text: '{text}'", "success")
                                break
                            
                            # Check for "sign up" (secondary)
                            if text_lower.find("sign up") != -1 and "sign up" in text_lower:
                                # Prefer buttons with "free" in text
                                if "free" in text_lower:
                                    sign_up_button = element
                                    self.log(f"✅ Found button with text: '{text}'", "success")
                                    break
                                elif not sign_up_button:  # Use as fallback
                                    sign_up_button = element
                        
                        except Exception as e:
                            continue
                    
                    # If not found by text, try by href
                    if not sign_up_button:
                        for element in all_links:
                            try:
                                if not element.is_displayed():
                                    continue
                                href = element.get_attribute("href") or ""
                                if "signup" in href.lower() or "register" in href.lower():
                                    sign_up_button = element
                                    self.log(f"✅ Found link by href: {href}", "success")
                                    break
                            except:
                                continue
                    
                    if sign_up_button:
                        self.log("✅ Found Sign up for free button, clicking...", "success")
                        
                        # Make sure element is in viewport and simulate human behavior
                        try:
                            # Scroll smoothly to button (human-like)
                            driver.execute_script("""
                                arguments[0].scrollIntoView({
                                    block: 'center',
                                    behavior: 'smooth'
                                });
                            """, sign_up_button)
                            time.sleep(random.uniform(0.8, 1.5))
                            
                            # Simulate mouse hover (move to element first)
                            try:
                                ActionChains(driver).move_to_element(sign_up_button).pause(random.uniform(0.2, 0.5)).perform()
                            except:
                                pass
                        except:
                            pass
                        
                        # Try multiple click methods with human-like delays
                        clicked = False
                        click_errors = []
                        
                        # Method 1: ActionChains with mouse movement (most human-like)
                        try:
                            ActionChains(driver).move_to_element(sign_up_button).pause(random.uniform(0.1, 0.3)).click().perform()
                            clicked = True
                            self.log("✅ Clicked using ActionChains (human-like)", "success")
                        except Exception as e1:
                            click_errors.append(f"ActionChains: {str(e1)}")
                        
                        # Method 2: JavaScript with mouse events (simulate real click)
                        if not clicked:
                            try:
                                driver.execute_script("""
                                    var element = arguments[0];
                                    var rect = element.getBoundingClientRect();
                                    var x = rect.left + rect.width / 2;
                                    var y = rect.top + rect.height / 2;
                                    
                                    // Create and dispatch mouse events
                                    var mouseDown = new MouseEvent('mousedown', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true,
                                        clientX: x,
                                        clientY: y
                                    });
                                    var mouseUp = new MouseEvent('mouseup', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true,
                                        clientX: x,
                                        clientY: y
                                    });
                                    var click = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true,
                                        clientX: x,
                                        clientY: y
                                    });
                                    
                                    element.dispatchEvent(mouseDown);
                                    setTimeout(function() {
                                        element.dispatchEvent(mouseUp);
                                        element.dispatchEvent(click);
                                    }, 10);
                                """, sign_up_button)
                                time.sleep(0.2)
                                clicked = True
                                self.log("✅ Clicked using mouse events", "success")
                            except Exception as e2:
                                click_errors.append(f"Mouse events: {str(e2)}")
                        
                        # Method 3: Regular click (fallback)
                        if not clicked:
                            try:
                                sign_up_button.click()
                                clicked = True
                                self.log("✅ Clicked using regular click()", "success")
                            except Exception as e3:
                                click_errors.append(f"Regular click: {str(e3)}")
                        
                        # Method 4: Simple JavaScript click (last resort)
                        if not clicked:
                            try:
                                driver.execute_script("arguments[0].click();", sign_up_button)
                                clicked = True
                                self.log("✅ Clicked using JavaScript", "success")
                            except Exception as e4:
                                click_errors.append(f"JS click: {str(e4)}")
                        
                        if not clicked:
                            raise Exception(f"All click methods failed: {'; '.join(click_errors)}")
                        
                        # Small delay after click (human-like)
                        time.sleep(random.uniform(0.3, 0.7))
                        
                        self.log("✅ Clicked button, waiting for email form to appear...", "success")
                        time.sleep(3)
                        
                        # Wait for email form to appear or URL change
                        max_wait = 10
                        for wait_attempt in range(max_wait):
                            current_url = driver.current_url.lower()
                            if 'signup' in current_url or 'auth' in current_url or 'email' in current_url:
                                self.log("✅ URL changed, email form should be visible", "success")
                                return
                            
                            try:
                                email_input = driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
                                if email_input and email_input.is_displayed():
                                    self.log("✅ Email form appeared", "success")
                                    return
                            except:
                                pass
                            time.sleep(1)
                        
                        # Even if email form not found, continue (might already be on next page)
                        return
                
                except Exception as e:
                    if attempt < max_attempts - 1:
                        self.log(f"⚠️ Attempt {attempt + 1} failed: {str(e)}, retrying...", "warning")
                        time.sleep(2)
                        continue
                    else:
                        self.log(f"⚠️ All attempts failed: {str(e)}", "warning")
            
            # Strategy 3: Fallback - Try XPath with exact text
            try:
                self.log("🔍 Trying XPath fallback...", "info")
                xpath_selectors = [
                    "//button[normalize-space(text())='Sign up for free']",
                    "//a[normalize-space(text())='Sign up for free']",
                    "//button[contains(normalize-space(text()), 'Sign up for free')]",
                    "//a[contains(normalize-space(text()), 'Sign up for free')]",
                ]
                
                for xpath in xpath_selectors:
                    try:
                        element = driver.find_element(By.XPATH, xpath)
                        if element.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", element)
                            self.log("✅ Clicked using XPath fallback", "success")
                            time.sleep(3)
                            return
                    except:
                        continue
            except:
                pass
            
            # Check if already on signup/auth page
            current_url = driver.current_url.lower()
            if 'signup' in current_url or 'auth' in current_url:
                self.log("ℹ️ Already on signup/auth page", "info")
                return
            
            raise Exception("Sign Up button not found after trying all methods")
        except Exception as e:
            raise Exception(f"Failed to click Sign Up: {str(e)}")
    
    def fill_email(self, driver, email):
        """Fill email input with detailed debugging"""
        try:
            # Log current state for debugging
            current_url = driver.current_url
            self.log(f"🔍 [DEBUG] fill_email - Current URL: {current_url}", "info")
            
            # Take page source snapshot for debugging
            try:
                page_source = driver.page_source
                self.log(f"🔍 [DEBUG] Page source length: {len(page_source)} chars", "info")
                
                # Check if we have any inputs on page
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                self.log(f"🔍 [DEBUG] Found {len(all_inputs)} input elements on page", "info")
                for inp in all_inputs[:5]:  # Log first 5 inputs
                    try:
                        inp_type = inp.get_attribute("type") or "unknown"
                        inp_name = inp.get_attribute("name") or "no-name"
                        inp_id = inp.get_attribute("id") or "no-id"
                        self.log(f"🔍 [DEBUG] Input: type={inp_type}, name={inp_name}, id={inp_id}", "info")
                    except:
                        pass
            except Exception as debug_e:
                self.log(f"🔍 [DEBUG] Error getting page info: {str(debug_e)}", "warning")
            
            # Wait longer for page to fully load
            wait = WebDriverWait(driver, 30)  # Increased timeout
            
            # Try multiple selectors with logging
            selectors = [
                (By.CSS_SELECTOR, 'input[type="email"]'),
                (By.CSS_SELECTOR, 'input[name*="email" i]'),
                (By.CSS_SELECTOR, 'input[id*="email" i]'),
                (By.CSS_SELECTOR, 'input[placeholder*="email" i]'),
                (By.ID, 'email'),
                (By.ID, 'email-input'),
                (By.CSS_SELECTOR, 'input[autocomplete="email"]'),
            ]
            
            for by, selector in selectors:
                try:
                    self.log(f"🔍 [DEBUG] Trying selector: {selector}", "info")
                    email_input = wait.until(EC.presence_of_element_located((by, selector)))
                    if email_input.is_displayed():
                        email_input.clear()
                        email_input.send_keys(email)
                        self.log(f"✅ Filled email: {email} (using {selector})", "success")
                        
                        # Click Continue button
                        time.sleep(1)
                        self.click_continue_button(driver)
                        return
                    else:
                        self.log(f"⚠️ [DEBUG] Found but not displayed: {selector}", "warning")
                except Exception as sel_e:
                    self.log(f"⚠️ [DEBUG] Selector {selector} failed: {str(sel_e)[:50]}", "warning")
                    continue
            
            raise Exception("Email input not found")
        except Exception as e:
            raise Exception(f"Failed to fill email: {str(e)}")
    def fill_password(self, driver, password):
        """Fill password input"""
        try:
            wait = WebDriverWait(driver, 10)
            
            # Try multiple selectors
            selectors = [
                (By.CSS_SELECTOR, 'input[name="new-password"]'),
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.CSS_SELECTOR, 'input[id*="-new-password"]')
            ]
            
            for by, selector in selectors:
                try:
                    password_input = wait.until(EC.presence_of_element_located((by, selector)))
                    password_input.clear()
                    password_input.send_keys(password)
                    self.log("✅ Filled password", "success")
                    
                    # Click Continue button
                    time.sleep(1)
                    self.click_continue_button(driver)
                    return
                except:
                    continue
            
            raise Exception("Password input not found")
        except Exception as e:
            raise Exception(f"Failed to fill password: {str(e)}")
    
    def fill_password_with_retry(self, driver, password):
        """Fill password input with retry logic (like extension)"""
        max_attempts = 15
        
        selectors = [
            (By.CSS_SELECTOR, 'input[name="new-password"]'),
            (By.CSS_SELECTOR, 'input[id*="-new-password"]'),
            (By.CSS_SELECTOR, 'input[type="password"][placeholder="Password"]'),
            (By.CSS_SELECTOR, 'input[type="password"][name*="password" i]'),
            (By.CSS_SELECTOR, 'input[type="password"]')
        ]
        
        for attempt in range(max_attempts):
            # Check if we're still on a password page
            current_url = driver.current_url
            if 'email-verification' in current_url or 'verify' in current_url.lower():
                self.log("📧 Redirected to OTP page, skipping password fill", "info")
                return True  # Consider this success, password was auto-filled
            
            for by, selector in selectors:
                try:
                    password_input = driver.find_element(by, selector)
                    if password_input and password_input.is_displayed():
                        password_input.clear()
                        password_input.send_keys(password)
                        self.log(f"✅ Filled password (attempt {attempt + 1})", "success")
                        
                        # Click Continue button
                        time.sleep(1)
                        self.click_continue_button(driver)
                        return True
                except:
                    continue
            
            # Wait before retry
            if attempt < max_attempts - 1:
                time.sleep(0.5)
        
        self.log(f"⚠️ Password input not found after {max_attempts} attempts", "warning")
        return False
    def click_continue_button(self, driver):
        """lick Continue button"""
        try:
            wait = WebDriverWait(driver, 5)
            
            # Try multiple selectors
            selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, "//button[contains(., 'Continue')]"),
                (By.CSS_SELECTOR, 'button[data-dd-action-name="Continue"]')
            ]
            
            for by, selector in selectors:
                try:
                    button = wait.until(EC.element_to_be_clickable((by, selector)))
                    if not button.get_attribute('disabled'):
                        button.click()
                        time.sleep(1)
                        return
                except:
                    continue
        except:
            pass  # Continue button might not always be needed
    def get_otp_from_email(self, account):
        """et OTP code from email via API"""
        try:
            api_url = 'https://phamducdung.net/api/get_messages_oauth2.php'
            payload = {
                'email': account['emailLogin'],
                'refresh_token': account['refreshToken'],
                'client_id': account['clientId']
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('status') or not data.get('messages'):
                raise Exception("No messages returned from API")
            
            messages = data['messages']
            # Sort by date (newest first)
            messages.sort(key=lambda x: x.get('date', 0), reverse=True)
            
            # Find OTP code in subject or body
            for msg in messages:
                subject = msg.get('subject', '').lower()
                body = msg.get('message', '') or msg.get('html_body', '')
                
                # Look for OTP in subject: "Your ChatGPT code is XXXXXX"
                subject_match = re.search(r'code\s*(?:is\s*)?(\d{6})', subject, re.I)
                if subject_match:
                    otp = subject_match.group(1)
                    self.log(f"✅ Found OTP in email: {otp}", "success")
                    return otp
                
                # Look for OTP in body
                body_match = re.search(r'code\s*(?:is\s*)?(\d{6})', body, re.I)
                if body_match:
                    otp = body_match.group(1)
                    self.log(f"✅ Found OTP in email body: {otp}", "success")
                    return otp
                
                # Fallback: any 6-digit code
                code_match = re.search(r'\b(\d{6})\b', subject + ' ' + body)
                if code_match:
                    otp = code_match.group(1)
                    self.log(f"✅ Found OTP (fallback): {otp}", "success")
                    return otp
            
            raise Exception("OTP code not found in emails")
        except Exception as e:
            raise Exception(f"Failed to get OTP: {str(e)}")
    def check_for_error_page(self, driver):
        """heck if error page is shown (account banned/locked)"""
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            if "oops, an error occurred" in page_text or "error occurred" in page_text:
                return True
            
            # Also check for error message elements
            error_selectors = [
                (By.XPATH, "//*[contains(text(), 'Oops, an error occurred')]"),
                (By.XPATH, "//*[contains(text(), 'error occurred')]"),
                (By.CSS_SELECTOR, '[class*="error"]'),
            ]
            
            for by, selector in error_selectors:
                try:
                    error_element = driver.find_element(by, selector)
                    if error_element.is_displayed():
                        error_text = error_element.text.lower()
                        if "error occurred" in error_text or "deleted" in error_text or "deactivated" in error_text:
                            return True
                except:
                    continue
            
            return False
        except:
            return False
    def handle_otp_verification_with_retry(self, driver, account, retry_count=0):
        """andle OTP verification with retry (max 2 retries, 10s between each)"""
        MAX_RETRIES = 2
        
        try:
            self.log(f"📧 Getting OTP code from email... (Attempt {retry_count + 1}/{MAX_RETRIES + 1})", "info")
            result = self.handle_otp_verification(driver, account)
            
            # Check result status
            if result.get('status') == 'account_banned':
                return result
            elif result.get('status') == 'account_exists':
                return result
            elif result.get('status') == 'otp_wrong' and retry_count < MAX_RETRIES:
                # OTP wrong - retry
                self.log(f"⚠️ OTP incorrect, retrying in 10s... (Attempt {retry_count + 1}/{MAX_RETRIES})", "warning")
                time.sleep(10)
                
                # Check if still on OTP page
                current_url = driver.current_url
                if 'email-verification' in current_url or 'verify' in current_url.lower():
                    # Clear OTP input
                    try:
                        otp_input = driver.find_element(By.CSS_SELECTOR, 'input[name="code"], input[id*="-code"], input[type="text"]')
                        otp_input.clear()
                    except:
                        pass
                    
                    return self.handle_otp_verification_with_retry(driver, account, retry_count + 1)
                else:
                    # Page changed, check status again
                    return self.check_otp_result_status(driver)
            elif result.get('status') == 'otp_wrong' and retry_count >= MAX_RETRIES:
                # Max retries reached
                return {'status': 'otp_failed'}
            else:
                # Success or other status
                return result
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if account is banned from error message
            if ('error occurred' in error_msg or 'deleted' in error_msg or 
                'deactivated' in error_msg or 'banned' in error_msg):
                return {'status': 'account_banned'}
            
            # Check page status
            result = self.check_otp_result_status(driver)
            if result.get('status') == 'otp_wrong' and retry_count < MAX_RETRIES:
                # Retry
                self.log(f"⚠️ OTP error, retrying in 10s... (Attempt {retry_count + 1}/{MAX_RETRIES})", "warning")
                time.sleep(10)
                
                current_url = driver.current_url
                if 'email-verification' in current_url or 'verify' in current_url.lower():
                    try:
                        otp_input = driver.find_element(By.CSS_SELECTOR, 'input[name="code"], input[id*="-code"], input[type="text"]')
                        otp_input.clear()
                    except:
                        pass
                    return self.handle_otp_verification_with_retry(driver, account, retry_count + 1)
                else:
                    return self.check_otp_result_status(driver)
            elif result.get('status') == 'otp_wrong':
                return {'status': 'otp_failed'}
            else:
                return result
    def check_otp_result_status(self, driver):
        """heck the status after OTP submission"""
        time.sleep(5)  # Wait longer for page to load after redirect
        current_url = driver.current_url
        
        # Check for error page (account banned)
        if self.check_for_error_page(driver):
            return {'status': 'account_banned'}
        
        # Check if redirected to homepage (account exists)
        # According to user: when account exists, after OTP it redirects to homepage without errors
        # So if we're on homepage (correct URL: chatgpt.com without auth/signup/verify/about-you) 
        # and no error page, it's account exists
        if ('chatgpt.com' in current_url and 'auth' not in current_url and 
            'signup' not in current_url and 'verify' not in current_url and 
            'about-you' not in current_url):
            # We're on homepage - if no error page, this means account exists
            # (User confirmed: when account exists, redirects to homepage without errors)
            return {'status': 'account_exists'}
        
        # Check if on About You page (new account)
        if 'about-you' in current_url:
            return {'status': 'success', 'next_step': 'about_you'}
        
        # Still on verification page - might be wrong OTP
        if 'email-verification' in current_url or 'verify' in current_url.lower():
            # Check for error message
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                if 'invalid' in page_text or 'incorrect' in page_text or 'wrong' in page_text:
                    return {'status': 'otp_wrong'}
            except:
                pass
        
        # Unknown status
        return {'status': 'success'}
    def handle_otp_verification(self, driver, account):
        """andle single OTP verification attempt"""
        # Get OTP from email
        otp = self.get_otp_from_email(account)
        if not otp:
            raise Exception("Could not get OTP code from email")
        
        # Fill OTP
        self.fill_otp(driver, otp)
        time.sleep(3)
        
        # Check result status
        return self.check_otp_result_status(driver)
    def fill_otp(self, driver, otp):
        """ill OTP code and submit"""
        try:
            wait = WebDriverWait(driver, 10)
            
            selectors = [
                (By.CSS_SELECTOR, 'input[name="code"]'),
                (By.CSS_SELECTOR, 'input[id*="-code"]'),
                (By.CSS_SELECTOR, 'input[type="text"]')
            ]
            
            otp_input = None
            for by, selector in selectors:
                try:
                    otp_input = wait.until(EC.presence_of_element_located((by, selector)))
                    break
                except:
                    continue
            
            if not otp_input:
                raise Exception("OTP input not found")
            
            otp_input.clear()
            otp_input.send_keys(otp)
            self.log("✅ Filled OTP code", "success")
            
            # Click verify/continue button
            time.sleep(1)
            self.click_continue_button(driver)
            
        except Exception as e:
            raise Exception(f"Failed to fill OTP: {str(e)}")
    def fill_about_you(self, driver, account):
        """ill About You page (name and birthday)"""
        try:
            wait = WebDriverWait(driver, 10)
            
            # Generate name from email
            email_prefix = account['email'].split('@')[0]
            full_name = email_prefix[:10]
            
            # Generate random birthday (10-12 for month, 10-28 for day)
            year = random.randint(1960, 1980)
            month = random.choice([10, 11, 12])
            day = random.randint(10, 28)
            
            # Fill name
            try:
                name_selectors = [
                    (By.CSS_SELECTOR, 'input[name="name"]'),
                    (By.CSS_SELECTOR, 'input[id*="-name"]'),
                    (By.CSS_SELECTOR, 'input[placeholder*="name" i]')
                ]
                
                for by, selector in name_selectors:
                    try:
                        name_input = driver.find_element(by, selector)
                        name_input.clear()
                        name_input.send_keys(full_name)
                        self.log(f"✅ Filled name: {full_name}", "success")
                        break
                    except:
                        continue
            except:
                pass
            
            time.sleep(1)
            
            # Fill birthday (React Aria DateField - segments)
            # Need to fill using JavaScript events similar to extension
            try:
                month_segment = driver.find_element(By.CSS_SELECTOR, '[data-type="month"][role="spinbutton"]')
                day_segment = driver.find_element(By.CSS_SELECTOR, '[data-type="day"][role="spinbutton"]')
                year_segment = driver.find_element(By.CSS_SELECTOR, '[data-type="year"][role="spinbutton"]')
                
                # Fill each segment using JavaScript (mimicking extension's fillSegment function)
                month_str = str(month).zfill(2)
                day_str = str(day).zfill(2)
                year_str = str(year)
                
                # JavaScript function to fill a segment (same as extension)
                # First, define the function in the page context
                define_function_js = """
                window.fillBirthdaySegment = function(segment, value) {
                    if (!segment) return false;
                    
                    // Focus on segment
                    segment.focus();
                    
                    // Click to ensure focus
                    segment.click();
                    
                    // Clear existing content
                    segment.textContent = '';
                    segment.innerText = '';
                    
                    // Type each digit one by one
                    for (let i = 0; i < value.length; i++) {
                        const digit = value[i];
                        
                        // beforeinput event (React Aria listens to this)
                        const beforeInputEvent = new InputEvent('beforeinput', {
                            inputType: 'insertText',
                            data: digit,
                            bubbles: true,
                            cancelable: true,
                            composed: true
                        });
                        const beforeInputAllowed = segment.dispatchEvent(beforeInputEvent);
                        
                        if (beforeInputAllowed) {
                            // Update text content
                            segment.textContent = (segment.textContent || '') + digit;
                            segment.innerText = (segment.innerText || '') + digit;
                            
                            // input event
                            const inputEvent = new InputEvent('input', {
                                inputType: 'insertText',
                                data: digit,
                                bubbles: true,
                                cancelable: true,
                                composed: true
                            });
                            segment.dispatchEvent(inputEvent);
                            
                            // Keyboard events for compatibility
                            const keydownEvent = new KeyboardEvent('keydown', {
                                key: digit,
                                code: 'Digit' + digit,
                                keyCode: 48 + parseInt(digit),
                                which: 48 + parseInt(digit),
                                bubbles: true,
                                cancelable: true,
                                composed: true
                            });
                            segment.dispatchEvent(keydownEvent);
                            
                            const keypressEvent = new KeyboardEvent('keypress', {
                                key: digit,
                                code: 'Digit' + digit,
                                keyCode: 48 + parseInt(digit),
                                which: 48 + parseInt(digit),
                                bubbles: true,
                                cancelable: true,
                                composed: true
                            });
                            segment.dispatchEvent(keypressEvent);
                            
                            const keyupEvent = new KeyboardEvent('keyup', {
                                key: digit,
                                code: 'Digit' + digit,
                                keyCode: 48 + parseInt(digit),
                                which: 48 + parseInt(digit),
                                bubbles: true,
                                cancelable: true,
                                composed: true
                            });
                            segment.dispatchEvent(keyupEvent);
                        }
                    }
                    
                    // Dispatch change event to finalize
                    const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                    segment.dispatchEvent(changeEvent);
                    
                    // Blur to finalize
                    segment.blur();
                    
                    return true;
                };
                """
                
                # Define the function once
                driver.execute_script(define_function_js)
                
                # Fill month segment
                driver.execute_script("window.fillBirthdaySegment(arguments[0], arguments[1]);", month_segment, month_str)
                time.sleep(0.3)
                
                # Fill day segment
                driver.execute_script("window.fillBirthdaySegment(arguments[0], arguments[1]);", day_segment, day_str)
                time.sleep(0.3)
                
                # Fill year segment
                driver.execute_script("window.fillBirthdaySegment(arguments[0], arguments[1]);", year_segment, year_str)
                time.sleep(0.5)
                
                self.log(f"✅ Filled birthday: {month}/{day}/{year}", "success")
            except Exception as e:
                self.log(f"⚠️ Could not fill birthday segments: {str(e)}", "warning")
            
            time.sleep(2)
            
            # Click Continue
            self.click_continue_button(driver)
            
        except Exception as e:
            raise Exception(f"Failed to fill About You: {str(e)}")
    def check_for_survey(self, driver):
        """heck if survey page is shown"""
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            return 'what brings you to chatgpt' in page_text or 'survey' in page_text
        except:
            return False
    def handle_success(self, account):
        """andle successful signup"""
        with self.thread_lock:
            self.stats['success'] += 1
            self.stats['processed'] += 1
            
            account_data = {
                'email': account['email'],
                'password': account['password'],
                'emailLogin': account['emailLogin'],
                'passEmail': account['passEmail'],
                'refreshToken': account['refreshToken'],
                'clientId': account['clientId'],
                'original': account['original'],
                'timestamp': datetime.now().isoformat()
            }
            self.success_accounts.append(account_data)
            
            self.update_stats_display()
            self.save_data_to_file()
            self.message_queue.put(("check_completion",))
    
    def handle_exists(self, account):
        """Handle login success (account already exists)"""
        with self.thread_lock:
            self.stats['exists'] += 1
            self.stats['processed'] += 1
            
            account_data = {
                'email': account['email'],
                'password': account['password'],
                'emailLogin': account['emailLogin'],
                'passEmail': account['passEmail'],
                'refreshToken': account['refreshToken'],
                'clientId': account['clientId'],
                'original': account['original'],
                'timestamp': datetime.now().isoformat()
            }
            self.exists_accounts.append(account_data)
            
            self.update_stats_display()
            self.save_data_to_file()
            self.message_queue.put(("check_completion",))

    def save_success_accounts(self):
        """Save success accounts to file"""
        if not self.success_accounts:
            QMessageBox.information(self, "Info", "No successful accounts to save")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Success Accounts",
            "",
            "Text files (*.txt);;All files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, acc in enumerate(self.success_accounts):
                    f.write(f"Account ChatGPT: {acc['email']}||{acc['password']}\n")
                    f.write(f"Full email info: {acc['emailLogin']}|{acc['passEmail']}|{acc['refreshToken']}|{acc['clientId']}\n")
                    f.write(f"Timestamp: {acc['timestamp']}\n")
                    if i < len(self.success_accounts) - 1:
                        f.write("\n--------------------------------\n\n")
            
            QMessageBox.information(self, "Success", f"Saved {len(self.success_accounts)} accounts to {file_path}")
            self.log(f"✅ Saved {len(self.success_accounts)} success accounts", "success")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
    
    def clear_stats(self):
        """Clear statistics"""
        self.stats = {'processed': 0, 'success': 0, 'failed': 0, 'exists': 0}
        self.success_accounts = []
        self.exists_accounts = []
        self.failed_accounts = []
        self.update_stats_display()
        self.log("📊 Statistics cleared", "info")
    
    def check_all_completed(self):
        """Check if all accounts have been processed"""
        if self.summary_shown:
            return  # Already shown summary
        
        with self.thread_lock:
            if self.stats['processed'] >= len(self.data_list) and len(self.data_list) > 0:
                # Use after to check threads status in GUI thread (thread-safe)
                QTimer.singleShot(1000, self._check_threads_completed)
    
    def _check_threads_completed(self):
        """Check if all threads completed (called from GUI thread)"""
        if self.summary_shown:
            return
        
        # Check if all threads have finished
        all_finished = all(not thread.is_alive() for thread in self.threads) if self.threads else True
        
        if all_finished and self.stats['processed'] >= len(self.data_list) and len(self.data_list) > 0:
            self.is_running = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.summary_shown = True
            self.show_final_summary()
        elif self.stats['processed'] < len(self.data_list):
            # Still processing, check again later
            QTimer.singleShot(1000, self._check_threads_completed)
    
    def show_final_summary(self):
        """Display final summary after all processing is complete"""
        self.log("", "info")  # Empty line
        self.log("=" * 80, "info")
        self.log("🎉 HOÀN THÀNH XỬ LÝ TẤT CẢ TÀI KHOẢN", "success")
        self.log("=" * 80, "info")
        self.log("", "info")  # Empty line
        
        # Success accounts
        if self.success_accounts:
            self.log("✅ TÀI KHOẢN ĐĂNG KÝ THÀNH CÔNG:", "success")
            for idx, acc in enumerate(self.success_accounts, 1):
                self.log(f"   {idx}. {acc['email']}", "success")
        else:
            self.log("✅ TÀI KHOẢN ĐĂNG KÝ THÀNH CÔNG: (Không có)", "info")
        
        self.log("", "info")  # Empty line
        
        # Exists accounts
        if self.exists_accounts:
            self.log("ℹ️ TÀI KHOẢN ĐÃ TỒN TẠI:", "info")
            for idx, acc in enumerate(self.exists_accounts, 1):
                self.log(f"   {idx}. {acc['email']}", "info")
        else:
            self.log("ℹ️ TÀI KHOẢN ĐÃ TỒN TẠI: (Không có)", "info")
        
        self.log("", "info")  # Empty line
        
        # Failed accounts
        if self.failed_accounts:
            self.log("❌ TÀI KHOẢN LỖI/BANNED/BLOCKED:", "error")
            for idx, acc in enumerate(self.failed_accounts, 1):
                reason = acc.get('reason', 'Error')
                self.log(f"   {idx}. {acc['email']} - ({reason})", "error")
        else:
            self.log("❌ TÀI KHOẢN LỖI/BANNED/BLOCKED: (Không có)", "info")
        
        self.log("", "info")  # Empty line
        self.log("=" * 80, "info")
        self.log(f"📊 TỔNG KẾT: Tổng={len(self.data_list)}, Đã xử lý={self.stats['processed']}, "
                f"Thành công={self.stats['success']}, Đã tồn tại={self.stats['exists']}, "
                f"Lỗi={self.stats['failed']}", "info")
        self.log("=" * 80, "info")


def main():
    app = QApplication([])
    window = ChatGPTSignupGUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
