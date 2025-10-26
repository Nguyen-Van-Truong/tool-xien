from PyQt6.uic import loadUi
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
import sys
import os
import shutil
from pathlib import Path
from modules.Bot import BotManager
import argparse

class WorkerThread(QThread):
    finished = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = False
        self.bot_instance = None

    def add_log(self, message):
        self.log_signal.emit(message)

    def stop(self):
        self.is_running = False
        if self.bot_instance:
            try:
                self.bot_instance.exit()
            except:
                pass

    def run(self):
        self.is_running = True
        data_file = self.config['data_file']
        backup_file = self.config['backup_file']

        # extract gg from pdf. Tạo file data nếu chưa tồn tại
        if not os.path.exists(data_file):
            with open(data_file, 'w', encoding='utf-8') as f:
                pass
            self.add_log(f"📄 Created new data file: {data_file}")

        # 2. Sao lưu nếu backup_file được cấu hình
        if backup_file:
            try:
                shutil.copy2(data_file, backup_file)
                self.add_log(f"📦 Backed up data file to: {backup_file}")
            except Exception as e:
                self.add_log(f"⚠️ Backup failed: {e}")

        # 3. Chạy tạo account
        self.run_create_account(data_file)
        self.finished.emit()

    def prepare_driver(self, bot):
        try:
            if not Path(bot.chromedriver).is_file():
                found = shutil.which('chromedriver')
                if found:
                    bot.chromedriver = Path(found)
                    self.add_log(f"⚙️ Using chromedriver from PATH: {found}")
        except Exception:
            pass

    def run_create_account(self, data_file):
        # Khởi tạo Bot
        self.bot_instance = BotManager(
            token=self.config['token'],
            num_threads=self.config['threads'],
            chromedriver=self.config['driver']
        )
        bot = self.bot_instance
        self.prepare_driver(bot)
        success_count = 0

        for i in range(1, self.config['tries'] + 1):
            if not self.is_running:
                self.add_log("💀 Stopped by user.")
                break

            try:
                self.add_log(f"🔄 Đang tạo account #{i}...")
                results = bot.start()
                
                if not results:
                    self.add_log(f"❌ Error creating account #{i}")
                    bot.exit()
                    self.prepare_driver(bot)
                    continue

                # Lưu tất cả các account đã tạo
                for result in results:
                    self.add_log(f"✅ Created account: {result['Email']}")
                    # Lưu account vào file
                    with open(data_file, 'a', encoding='utf-8') as f:
                        f.write(f"{result['Email']}:{result['Password']}\n")
                    success_count += 1
                
                self.add_log(f"🚩 Created {success_count}/{self.config['tries']} accounts")

            except Exception as e:
                self.add_log(f"❌ Exception on create: {e}")
                bot.exit()
                self.prepare_driver(bot)
                continue

        bot.exit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/main.ui", self)
        self.thread = None
        self.run.clicked.connect(self.start_thread)
        self.stop.clicked.connect(self.stop_thread)
        
        # Đọc token từ file token.txt
        try:
            with open("token.txt", "r", encoding="utf-8") as f:
                self.tempMailToken.setText(f.read().strip())
        except Exception as e:
            self.show_message(f"Không thể đọc token từ file: {str(e)}")
        
        # Set mặc định file lưu account
        if not self.dataFile.text().strip():
            self.dataFile.setText("acc.txt")

    def start_thread(self):
        token = self.tempMailToken.text().strip()
        data_file = self.dataFile.text().strip()
        backup_file = self.backupFile.text().strip()

        if not token:
            self.show_message("Nhập token của TempMail.")
            return
        if not data_file:
            data_file = "acc.txt"  # Set mặc định nếu không có file được chọn
            self.dataFile.setText(data_file)

        config = {
            'token': token,
            'data_file': data_file,
            'backup_file': backup_file,
            'tries': self.quantity.value(),
            'wait_sec': self.waitTime.value(),
            'headless_mode': self.headlessMode.isChecked(),
            'threads': self.threads.value(),
            'driver': self.driver.text()
        }

        self.thread = WorkerThread(config)
        self.thread.log_signal.connect(self.log.addItem)
        self.thread.finished.connect(self.thread_finished)
        self.thread.start()
        self.update_ui_state()

    def stop_thread(self):
        if self.thread:
            self.thread.stop()

    def thread_finished(self):
        self.thread = None
        self.update_ui_state()

    def show_message(self, text, title="Warning"):
        QMessageBox.warning(self, title, text)

    def update_ui_state(self):
        is_running = self.thread is not None
        self.run.setEnabled(not is_running)
        self.stop.setEnabled(is_running)
        self.tempMailToken.setEnabled(not is_running)
        self.dataFile.setEnabled(not is_running)
        self.backupFile.setEnabled(not is_running)
        self.quantity.setEnabled(not is_running)
        self.waitTime.setEnabled(not is_running)
        self.headlessMode.setEnabled(not is_running)
        self.threads.setEnabled(not is_running)
        self.driver.setEnabled(not is_running)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("WindowsVista")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
