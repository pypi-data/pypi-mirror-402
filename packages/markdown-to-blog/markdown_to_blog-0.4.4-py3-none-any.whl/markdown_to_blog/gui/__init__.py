import sys
from PySide6.QtWidgets import QApplication
from loguru import logger

from .main_window import MainWindow


def run_gui():
    """Run the GUI application"""
    app = QApplication(sys.argv)
    app.setApplicationName("Markdown to Blog")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    logger.info("Starting Markdown to Blog GUI")
    sys.exit(app.exec())


def run_shell(shell_command=None):
    """Run interactive shell with Tortoise ORM."""
    from .shell import run_shell as _run_shell
    return _run_shell(shell_command)