"""Entry point for the Speech2Text application.

Usage:
    python main.py

Launches the PyQt6 desktop window. No arguments required.
"""

import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> None:
    """Initialize the Qt application and show the main window."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
