#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from datetime import datetime
import os

class Logger:
    """Thread-safe logger"""

    def __init__(self, log_file=None, console_output=True):
        self.lock = threading.Lock()
        self.log_file = log_file
        self.console_output = console_output

        # Create log directory if needed
        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

    def log(self, message, level="INFO", thread_id=None):
        """Thread-safe logging"""
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            thread_str = f"[T{thread_id}]" if thread_id is not None else ""

            icons = {
                "INFO": "[INFO]",
                "SUCCESS": "[OK]",
                "ERROR": "[ERR]",
                "WARNING": "[WARN]",
                "DEBUG": "[DBG]",
                "PROGRESS": "[PROG]"
            }
            icon = icons.get(level, "[LOG]")

            log_message = f"{timestamp} {thread_str} {icon} {message}"

            # Console output
            if self.console_output:
                print(log_message)

            # File output
            if self.log_file:
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(log_message + '\n')
                except:
                    pass

    def info(self, message, thread_id=None):
        self.log(message, "INFO", thread_id)

    def success(self, message, thread_id=None):
        self.log(message, "SUCCESS", thread_id)

    def error(self, message, thread_id=None):
        self.log(message, "ERROR", thread_id)

    def warning(self, message, thread_id=None):
        self.log(message, "WARNING", thread_id)

    def debug(self, message, thread_id=None):
        self.log(message, "DEBUG", thread_id)

    def progress(self, message, thread_id=None):
        self.log(message, "PROGRESS", thread_id)
