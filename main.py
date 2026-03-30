#!/usr/bin/env python3
"""
Editor ISK - Main Entry Point
=============================
A professional Python code editor with AI assistance.
"""

import sys
import os

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
editor_isk_dir = script_dir

# Add the editor_isk_v2 directory to the path
sys.path.insert(0, editor_isk_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Import directly to avoid package issues
from ui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Editor ISK")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Editor ISK")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Print startup message
    print("[Editor ISK 2.0] Starting...")
    
    # Return from function, app will run
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())