"""
ChatGPT Military Verification Tool - Main Entry Point
Tool tự động verify hàng loạt tài khoản ChatGPT Veterans
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ChatGPT Military Verification Tool")
    app.setOrganizationName("ChatGPTVeterans")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

