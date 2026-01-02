#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V11 Multi-Profile Login Tool - Main GUI Application
Công cụ đăng ký/đăng nhập ChatGPT đa profile với GUI
"""

import sys
import os
import threading
import queue
import json
import time
from datetime import datetime
from typing import List, Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox, QTextEdit,
    QSpinBox, QLineEdit, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCharFormat, QTextCursor

import config
from browser_manager import BrowserManager, BrowserInstance
from automation_engine import create_automation, AutomationEngine


class LogSignal(QObject):
    """Signal for thread-safe logging"""
    log_message = pyqtSignal(str, str, int)  # message, level, browser_id (0 = main)


class WorkerSignal(QObject):
    """Signals for worker threads"""
    finished = pyqtSignal(int, dict)  # instance_id, result
    status_update = pyqtSignal(int, str, str)  # instance_id, status, message


class MultiLoginTool(QMainWindow):
    """Main GUI Application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("V11 Multi-Profile Login Tool")
        self.setGeometry(100, 100, 800, 900)
        
        # State
        self.accounts: List[Dict] = []
        self.is_running = False
        self.browser_manager = BrowserManager(logger=self._log_to_queue)
        self.active_workers: Dict[int, threading.Thread] = {}
        self.worker_lock = threading.Lock()
        self.current_index = 0
        
        # Browser log tabs
        self.browser_log_tabs: Dict[int, QTextEdit] = {}  # browser_id -> QTextEdit
        
        # Stats
        self.stats = {
            'total': 0,
            'processed': 0,
            'success': 0,
            'exists': 0,
            'failed': 0
        }
        
        # Results storage
        self.success_accounts = []
        self.exists_accounts = []
        self.failed_accounts = []
        
        # Queue for thread-safe updates
        self.message_queue = queue.Queue()
        
        # Signals
        self.log_signal = LogSignal()
        self.log_signal.log_message.connect(self._append_log)
        
        self.worker_signal = WorkerSignal()
        self.worker_signal.finished.connect(self._on_worker_finished)
        self.worker_signal.status_update.connect(self._on_status_update)
        
        # Setup UI
        self._setup_dark_theme()
        self._setup_ui()
        
        # Timer for queue processing
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self._process_queue)
        self.queue_timer.start(100)
        
        # Load saved state
        self._load_saved_state()
        
        # Log file
        log_file_path = os.path.join(config.LOG_DIR, 'main.log')
        self.log_file = open(log_file_path, 'a', encoding='utf-8')
        self.log_file.write(f"\n{'='*60}\nSession started: {datetime.now().isoformat()}\n{'='*60}\n")
    
    def _setup_dark_theme(self):
        """Setup dark theme"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
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
            QLabel { color: #fff; }
            QLineEdit, QSpinBox {
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
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #555;
                color: #fff;
                gridline-color: #444;
            }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #3a9eff; }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #fff;
                padding: 5px;
                border: 1px solid #555;
            }
            QCheckBox { color: #fff; }
        """)
    
    def _setup_ui(self):
        """Setup UI components"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("V11 Multi-Profile Login Tool")
        title.setFont(QFont("", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #4ec9b0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Đăng ký/Đăng nhập ChatGPT đa profile - Không đóng browser")
        subtitle.setStyleSheet("color: #858585;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # File and Settings row
        top_row = QHBoxLayout()
        
        # File group
        file_group = QGroupBox("📁 Data File")
        file_layout = QVBoxLayout(file_group)
        
        file_btn_layout = QHBoxLayout()
        self.load_btn = self._create_button("📂 Load File", "#4a9eff", self._load_data_file)
        file_btn_layout.addWidget(self.load_btn)
        file_layout.addLayout(file_btn_layout)
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet("color: #858585;")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        self.count_label = QLabel("0 accounts")
        self.count_label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        file_layout.addWidget(self.count_label)
        
        top_row.addWidget(file_group)
        
        # Settings group
        settings_group = QGroupBox("⚙️ Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Max browsers
        browsers_row = QHBoxLayout()
        browsers_row.addWidget(QLabel("Max Browsers:"))
        self.max_browsers_spin = QSpinBox()
        self.max_browsers_spin.setRange(1, 10)
        self.max_browsers_spin.setValue(config.MAX_CONCURRENT_BROWSERS)
        browsers_row.addWidget(self.max_browsers_spin)
        browsers_row.addStretch()
        settings_layout.addLayout(browsers_row)
        
        # Browser path
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Browser:"))
        self.browser_path_edit = QLineEdit()
        self.browser_path_edit.setPlaceholderText("Auto-detect")
        path_row.addWidget(self.browser_path_edit)
        
        browse_btn = self._create_button("...", "#6c757d", self._browse_browser)
        browse_btn.setMaximumWidth(40)
        path_row.addWidget(browse_btn)
        settings_layout.addLayout(path_row)
        
        # Keep browser open
        self.keep_open_check = QCheckBox("Keep browsers open after completion")
        self.keep_open_check.setChecked(config.KEEP_BROWSER_OPEN)
        settings_layout.addWidget(self.keep_open_check)
        
        top_row.addWidget(settings_group)
        layout.addLayout(top_row)
        
        # Stats row
        stats_group = QGroupBox("📊 Statistics")
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.addStretch()
        
        self.stat_labels = {}
        stats_config = [
            ("Total", "total", "#858585"),
            ("Processed", "processed", "#4a9eff"),
            ("Success", "success", "#27ae60"),
            ("Exists", "exists", "#f39c12"),
            ("Failed", "failed", "#e74c3c"),
        ]
        
        for label, key, color in stats_config:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setSpacing(2)
            stat_layout.setContentsMargins(10, 0, 10, 0)
            
            name_label = QLabel(label)
            name_label.setStyleSheet("color: #aaa; font-size: 9pt;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(name_label)
            
            value_label = QLabel("0")
            value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18pt;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            self.stat_labels[key] = value_label
            stats_layout.addWidget(stat_widget)
        
        stats_layout.addStretch()
        layout.addWidget(stats_group)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = self._create_button("▶ START", "#27ae60", self._start_processing)
        self.start_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = self._create_button("■ STOP", "#e74c3c", self._stop_processing)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        self.save_btn = self._create_button("💾 Save Results", "#3498db", self._save_results)
        btn_layout.addWidget(self.save_btn)
        
        self.clear_btn = self._create_button("🗑️ Clear", "#95a5a6", self._clear_stats)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Accounts table
        table_group = QGroupBox("📋 Accounts")
        table_layout = QVBoxLayout(table_group)
        
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(4)
        self.accounts_table.setHorizontalHeaderLabels(["Email", "Status", "Browser ID", "Message"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.accounts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.accounts_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.accounts_table.setColumnWidth(1, 100)
        self.accounts_table.setColumnWidth(2, 80)
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.accounts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        table_layout.addWidget(self.accounts_table)
        layout.addWidget(table_group)
        
        # Log area with tabs
        log_group = QGroupBox("📝 Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_tab_widget = QTabWidget()
        self.log_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
                background: #252526;
            }
            QTabBar::tab {
                background: #3d3d3d;
                color: #fff;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #4a9eff;
            }
        """)
        self.log_tab_widget.setMaximumHeight(250)
        
        # Main log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_tab_widget.addTab(self.log_text, "📋 Main")
        
        log_layout.addWidget(self.log_tab_widget)
        layout.addWidget(log_group)
    
    def _create_button(self, text: str, color: str, callback) -> QPushButton:
        """Create styled button"""
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {color}; opacity: 0.8; }}
            QPushButton:disabled {{ background-color: #555; color: #888; }}
        """)
        btn.clicked.connect(callback)
        return btn
    
    def _log_to_queue(self, message: str, browser_id: int = 0):
        """Add log message to queue (thread-safe)"""
        self.message_queue.put(("log", message, "info", browser_id))
    
    def _process_queue(self):
        """Process messages from queue"""
        try:
            while True:
                msg_type, *args = self.message_queue.get_nowait()
                if msg_type == "log":
                    message, level, browser_id = args
                    self.log_signal.log_message.emit(message, level, browser_id)
                elif msg_type == "stats":
                    self._update_stats_display()
                elif msg_type == "create_browser_tab":
                    browser_id, email = args
                    self._create_browser_log_tab(browser_id, email)
        except queue.Empty:
            pass
    
    def _create_browser_log_tab(self, browser_id: int, email: str):
        """Create a new log tab for a browser (must be called from main thread)"""
        if browser_id in self.browser_log_tabs:
            return  # Already exists
        
        tab = QTextEdit()
        tab.setReadOnly(True)
        tab.setFont(QFont("Consolas", 9))
        tab.setStyleSheet("background-color: #252526; color: #d4d4d4;")
        
        # Truncate email for tab title
        short_email = email.split("@")[0][:12] if "@" in email else email[:12]
        tab_title = f"🌐 {browser_id}: {short_email}"
        
        self.browser_log_tabs[browser_id] = tab
        self.log_tab_widget.addTab(tab, tab_title)
        
        # Switch to new tab
        self.log_tab_widget.setCurrentWidget(tab)
    
    def _append_log(self, message: str, level: str = "info", browser_id: int = 0):
        """Append log message to text edit"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color based on level
        fmt = QTextCharFormat()
        if level == "success":
            fmt.setForeground(QColor("#2ecc71"))
        elif level == "error":
            fmt.setForeground(QColor("#e74c3c"))
        elif level == "warning":
            fmt.setForeground(QColor("#f39c12"))
        else:
            fmt.setForeground(QColor("#3498db"))
        
        # Determine which text edit to use
        if browser_id > 0 and browser_id in self.browser_log_tabs:
            target_text = self.browser_log_tabs[browser_id]
        else:
            target_text = self.log_text
        
        cursor = target_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{timestamp}] {message}\n", fmt)
        target_text.setTextCursor(cursor)
        target_text.ensureCursorVisible()
        
        # Also log to main tab if from browser (summary)
        if browser_id > 0 and target_text != self.log_text:
            main_cursor = self.log_text.textCursor()
            main_cursor.movePosition(QTextCursor.MoveOperation.End)
            summary_fmt = QTextCharFormat()
            summary_fmt.setForeground(QColor("#888888"))
            main_cursor.insertText(f"[{timestamp}] [Browser {browser_id}] {message}\n", fmt)
            self.log_text.setTextCursor(main_cursor)
        
        # Write to file
        try:
            log_prefix = f"[Browser {browser_id}] " if browser_id > 0 else ""
            self.log_file.write(f"[{timestamp}] [{level.upper()}] {log_prefix}{message}\n")
            self.log_file.flush()
        except:
            pass
    
    def log(self, message: str, level: str = "info", browser_id: int = 0):
        """Log message (thread-safe)"""
        self.message_queue.put(("log", message, level, browser_id))
    
    def _load_data_file(self):
        """
        Load accounts from file
        
        Supported formats:
        - 4 fields: email|password|token|clientId
        - 6 fields: email|password|emailLogin|passEmail|token|clientId
        - 12 fields: email|password|emailLogin|passEmail|token|clientId|first|last|branch|month|day|year
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", "Text files (*.txt);;All files (*.*)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            accounts = []
            
            for line in lines:
                parts = [p.strip() for p in line.split('|')]
                
                # 12-field format: signup + verify data
                if len(parts) >= 12:
                    accounts.append({
                        'email': parts[0],
                        'password': parts[1],
                        'emailLogin': parts[2],
                        'passEmail': parts[3],
                        'refreshToken': parts[4],
                        'clientId': parts[5],
                        # Verify data
                        'first': parts[6],
                        'last': parts[7],
                        'branch': parts[8],
                        'month': parts[9],
                        'day': parts[10],
                        'year': parts[11],
                        'original': line,
                        'status': 'pending',
                        'browser_id': None,
                        'message': ''
                    })
                # 6-field format: signup only
                elif len(parts) >= 6:
                    accounts.append({
                        'email': parts[0],
                        'password': parts[1],
                        'emailLogin': parts[2],
                        'passEmail': parts[3],
                        'refreshToken': parts[4],
                        'clientId': parts[5],
                        'original': line,
                        'status': 'pending',
                        'browser_id': None,
                        'message': ''
                    })
                # 4-field format: minimal
                elif len(parts) >= 4:
                    accounts.append({
                        'email': parts[0],
                        'password': parts[1],
                        'emailLogin': parts[0],
                        'passEmail': parts[1],
                        'refreshToken': parts[2],
                        'clientId': parts[3],
                        'original': line,
                        'status': 'pending',
                        'browser_id': None,
                        'message': ''
                    })
            
            self.accounts = accounts
            self.stats['total'] = len(accounts)
            self._update_stats_display()
            self._update_accounts_table()
            
            # Count accounts with verify data
            verify_count = sum(1 for a in accounts if 'first' in a)
            
            self.file_label.setText(os.path.basename(file_path))
            self.file_label.setStyleSheet("color: #4ec9b0;")
            
            if verify_count > 0:
                self.count_label.setText(f"{len(accounts)} accounts ({verify_count} with verify)")
            else:
                self.count_label.setText(f"{len(accounts)} accounts")
            
            self.start_btn.setEnabled(len(accounts) > 0)
            
            self.log(f"✅ Loaded {len(accounts)} accounts ({verify_count} with verify data)", "success")
            self._save_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
            self.log(f"❌ Error loading file: {e}", "error")
    
    def _update_accounts_table(self):
        """Update accounts table"""
        self.accounts_table.setRowCount(len(self.accounts))
        
        status_colors = {
            'pending': '#858585',
            'running': '#4a9eff',
            'success': '#27ae60',
            'exists': '#f39c12',
            'failed': '#e74c3c'
        }
        
        for i, acc in enumerate(self.accounts):
            # Email
            email_item = QTableWidgetItem(acc['email'])
            self.accounts_table.setItem(i, 0, email_item)
            
            # Status
            status = acc.get('status', 'pending')
            status_item = QTableWidgetItem(status.upper())
            status_item.setForeground(QColor(status_colors.get(status, '#fff')))
            self.accounts_table.setItem(i, 1, status_item)
            
            # Browser ID
            browser_id = acc.get('browser_id', '')
            browser_item = QTableWidgetItem(str(browser_id) if browser_id else "")
            self.accounts_table.setItem(i, 2, browser_item)
            
            # Message
            message_item = QTableWidgetItem(acc.get('message', ''))
            self.accounts_table.setItem(i, 3, message_item)
    
    def _update_stats_display(self):
        """Update statistics display"""
        for key, label in self.stat_labels.items():
            label.setText(str(self.stats.get(key, 0)))
    
    def _browse_browser(self):
        """Browse for browser executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Browser", "C:\\Program Files", "Executable (*.exe)"
        )
        if file_path:
            self.browser_path_edit.setText(file_path)
            self.log(f"✅ Browser: {file_path}", "success")
    
    def _start_processing(self):
        """Start processing accounts"""
        if not self.accounts:
            QMessageBox.warning(self, "Warning", "No accounts loaded!")
            return
        
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Update config from UI
        config.MAX_CONCURRENT_BROWSERS = self.max_browsers_spin.value()
        config.KEEP_BROWSER_OPEN = self.keep_open_check.isChecked()
        if self.browser_path_edit.text():
            config.BROWSER_PATH = self.browser_path_edit.text()
        
        # Reset current index to first pending account
        self.current_index = 0
        for i, acc in enumerate(self.accounts):
            if acc['status'] == 'pending':
                self.current_index = i
                break
        
        self.log(f"🚀 Starting with max {config.MAX_CONCURRENT_BROWSERS} browsers", "info")
        
        # Start initial batch
        self._start_next_batch()
    
    def _start_next_batch(self):
        """Start next batch of workers"""
        if not self.is_running:
            return
        
        with self.worker_lock:
            active_count = len(self.active_workers)
            available_slots = config.MAX_CONCURRENT_BROWSERS - active_count
            
            while available_slots > 0 and self.current_index < len(self.accounts):
                account = self.accounts[self.current_index]
                
                if account['status'] != 'pending':
                    self.current_index += 1
                    continue
                
                # Create worker thread
                thread = threading.Thread(
                    target=self._worker_thread,
                    args=(self.current_index, account),
                    daemon=True
                )
                thread.start()
                
                self.active_workers[self.current_index] = thread
                account['status'] = 'running'
                
                self.current_index += 1
                available_slots -= 1
        
        self._update_accounts_table()
        
        # Check if all done
        if len(self.active_workers) == 0 and self.current_index >= len(self.accounts):
            self._on_all_completed()
    
    def _worker_thread(self, index: int, account: dict):
        """Worker thread - process single account"""
        instance = None
        
        try:
            self.log(f"🔄 Starting browser for {account['email']}")
            
            # Create browser instance
            instance = self.browser_manager.create_browser(
                account_email=account['email'],
                browser_path=config.BROWSER_PATH
            )
            
            if not instance:
                self.worker_signal.finished.emit(index, {
                    'success': False,
                    'status': 'failed',
                    'message': 'Failed to create browser'
                })
                return
            
            # Update account with browser ID
            account['browser_id'] = instance.id
            self.worker_signal.status_update.emit(index, 'running', f'Browser {instance.id}')
            
            # Create browser log tab via queue (thread-safe)
            self.message_queue.put(("create_browser_tab", instance.id, account['email']))
            
            # Create logger with browser_id
            def browser_logger(message: str, level: str = "info", browser_id=instance.id):
                self.message_queue.put(("log", message, level, browser_id))
            
            # Use new AutomationEngine (handles both signup and verify)
            automation = create_automation(
                driver=instance.driver,
                account=account,
                logger=browser_logger,
                instance_id=instance.id
            )
            
            # Check if account has verify data (12 fields)
            has_verify_data = all(key in account for key in ['first', 'last', 'branch', 'month', 'day', 'year'])
            
            if has_verify_data:
                browser_logger("🎖️ Account has verify data, will run full flow", "info")
                result = automation.run()  # Runs signup + verify
            else:
                browser_logger("📝 Account has signup data only", "info")
                result = automation.run_signup_only()  # Runs signup only
            
            # Keep browser open based on config
            if not config.KEEP_BROWSER_OPEN:
                self.browser_manager.close_browser(instance.id, keep_open=False)
            
            self.worker_signal.finished.emit(index, result)
            
        except Exception as e:
            browser_id = instance.id if instance else 0
            self.log(f"❌ Worker error for {account['email']}: {e}", "error", browser_id)
            self.worker_signal.finished.emit(index, {
                'success': False,
                'status': 'failed',
                'message': str(e)
            })
    
    def _on_worker_finished(self, index: int, result: dict):
        """Handle worker completion"""
        account = self.accounts[index]
        status = result.get('status', 'failed')
        message = result.get('message', '')
        
        account['status'] = status
        account['message'] = message
        
        # Update stats
        with self.worker_lock:
            self.stats['processed'] += 1
            
            if status == 'success':
                self.stats['success'] += 1
                self.success_accounts.append(account)
            elif status == 'exists':
                self.stats['exists'] += 1
                self.exists_accounts.append(account)
            else:
                self.stats['failed'] += 1
                self.failed_accounts.append(account)
            
            # Remove from active workers
            if index in self.active_workers:
                del self.active_workers[index]
        
        self._update_stats_display()
        self._update_accounts_table()
        self._save_state()
        
        status_emoji = "✅" if status == "success" else ("⚠️" if status == "exists" else "❌")
        self.log(f"{status_emoji} {account['email']}: {status.upper()} - {message}", 
                 "success" if status == "success" else ("warning" if status == "exists" else "error"))
        
        # Start next
        if self.is_running:
            self._start_next_batch()
    
    def _on_status_update(self, index: int, status: str, message: str):
        """Handle status update from worker"""
        if index < len(self.accounts):
            self.accounts[index]['status'] = status
            self.accounts[index]['message'] = message
            self._update_accounts_table()
    
    def _on_all_completed(self):
        """Called when all accounts processed"""
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.log(f"🎉 All done! Success: {self.stats['success']}, Exists: {self.stats['exists']}, Failed: {self.stats['failed']}", "success")
        
        QMessageBox.information(
            self, "Complete",
            f"Processing complete!\n\n"
            f"Success: {self.stats['success']}\n"
            f"Already Exists: {self.stats['exists']}\n"
            f"Failed: {self.stats['failed']}"
        )
    
    def _stop_processing(self):
        """Stop processing"""
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("⏹️ Stopped", "warning")
    
    def _save_results(self):
        """Save results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Save success accounts
            if self.success_accounts:
                with open(f'success_{timestamp}.txt', 'w', encoding='utf-8') as f:
                    for acc in self.success_accounts:
                        f.write(f"{acc.get('original', acc['email'])}\n")
                self.log(f"✅ Saved {len(self.success_accounts)} success accounts", "success")
            
            # Save exists accounts
            if self.exists_accounts:
                with open(f'exists_{timestamp}.txt', 'w', encoding='utf-8') as f:
                    for acc in self.exists_accounts:
                        f.write(f"{acc.get('original', acc['email'])}\n")
                self.log(f"✅ Saved {len(self.exists_accounts)} exists accounts", "success")
            
            # Save failed accounts
            if self.failed_accounts:
                with open(f'failed_{timestamp}.txt', 'w', encoding='utf-8') as f:
                    for acc in self.failed_accounts:
                        f.write(f"{acc.get('original', acc['email'])}|{acc.get('message', '')}\n")
                self.log(f"✅ Saved {len(self.failed_accounts)} failed accounts", "success")
            
            QMessageBox.information(self, "Saved", "Results saved successfully!")
            
        except Exception as e:
            self.log(f"❌ Save error: {e}", "error")
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")
    
    def _clear_stats(self):
        """Clear statistics"""
        reply = QMessageBox.question(
            self, "Clear", "Clear all statistics and reset accounts?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.stats = {'total': len(self.accounts), 'processed': 0, 'success': 0, 'exists': 0, 'failed': 0}
            self.success_accounts = []
            self.exists_accounts = []
            self.failed_accounts = []
            
            for acc in self.accounts:
                acc['status'] = 'pending'
                acc['browser_id'] = None
                acc['message'] = ''
            
            self._update_stats_display()
            self._update_accounts_table()
            self.log("🧹 Cleared all stats", "info")
    
    def _save_state(self):
        """Save current state"""
        try:
            state = {
                'accounts': self.accounts,
                'stats': self.stats,
                'browser_path': self.browser_path_edit.text(),
                'max_browsers': self.max_browsers_spin.value(),
                'keep_open': self.keep_open_check.isChecked()
            }
            with open('state.json', 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _load_saved_state(self):
        """Load saved state"""
        try:
            with open('state.json', 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            if state.get('browser_path'):
                self.browser_path_edit.setText(state['browser_path'])
            if state.get('max_browsers'):
                self.max_browsers_spin.setValue(state['max_browsers'])
            if 'keep_open' in state:
                self.keep_open_check.setChecked(state['keep_open'])
        except:
            pass
    
    def closeEvent(self, event):
        """Handle window close"""
        self.is_running = False
        
        # Close log file
        try:
            self.log_file.close()
        except:
            pass
        
        # Note: browsers are kept open if KEEP_BROWSER_OPEN is True
        if not config.KEEP_BROWSER_OPEN:
            self.browser_manager.close_all_browsers(keep_open=False)
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MultiLoginTool()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
