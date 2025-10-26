from PyQt6.uic import loadUi
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
import sys, os, shutil
from pathlib import Path
from modules.Bot import BotManager

class WorkerThread(QThread):
    finished = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.bot_instance = None

    def add_log(self, message):
        self.log_signal.emit(message)

    def stop(self):
        self.is_running = False
        if self.bot_instance:
            try: self.bot_instance.exit()
            except: pass

    def run(self):
        self.is_running = True
        self.run_check_account()
        self.finished.emit()

    def prepare_driver(self, bot):
        try:
            if not Path(bot.chromedriver).is_file():
                found = shutil.which('chromedriver')
                if found:
                    bot.chromedriver = Path(found)
                    self.add_log(f"⚙️ Using chromedriver from PATH: {found}")
        except Exception: pass

    def run_check_account(self):
        self.bot_instance = BotManager(
            token="",  # Không cần token nữa
            num_threads=10,  # Cố định 10 luồng
            chromedriver="driver/chromedriver.exe",
            headless_mode=True  # Luôn chạy ngầm
        )
        bot = self.bot_instance
        self.prepare_driver(bot)

        try:
            self.add_log("🔄 Bắt đầu kiểm tra tài khoản...")
            bot.start()
            self.add_log("✅ Hoàn thành kiểm tra!")
        except Exception as e:
            self.add_log(f"❌ Lỗi: {e}")
        finally:
            bot.exit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/main.ui", self)
        self.thread = None
        self.run.clicked.connect(self.start_thread)
        self.stop.clicked.connect(self.stop_thread)

    def start_thread(self):
        self.thread = WorkerThread()
        self.thread.log_signal.connect(self.log.addItem)
        self.thread.finished.connect(self.thread_finished)
        self.thread.start()
        self.update_ui_state()

    def stop_thread(self):
        if self.thread: self.thread.stop()

    def thread_finished(self):
        self.thread = None
        self.update_ui_state()

    def show_message(self, text, title="Warning"):
        QMessageBox.warning(self, title, text)

    def update_ui_state(self):
        is_running = self.thread is not None
        self.run.setEnabled(not is_running)
        self.stop.setEnabled(is_running)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("WindowsVista")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
