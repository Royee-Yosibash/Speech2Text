"""Entry point for the Speech2Text desktop application and worker.

Usage:
    python main.py
    Speech2Text --worker

The default mode launches the PyQt6 desktop window. ``--worker`` runs the
headless JSON-lines interface used by external applications.
"""

import sys

WORKER_ARGUMENT = "--worker"


def main():
    """Run the worker mode or launch the desktop application."""
    if len(sys.argv) > 1 and sys.argv[1] == WORKER_ARGUMENT:
        from speech2text.worker import main as worker_main

        worker_main()
        return

    from PyQt6.QtWidgets import QApplication

    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
