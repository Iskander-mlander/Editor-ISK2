"""
Diagnostics Panel Widget
========================
Panel for displaying LSP diagnostics.
"""

from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor


class DiagnosticsPanel(QWidget):
    """
    Panel for displaying LSP diagnostics.
    """
    
    diagnostic_clicked = pyqtSignal(str, int, int)  # uri, line, column
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._diagnostics: List[Dict[str, Any]] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QHBoxLayout()
        
        self._error_count = QLabel("0 Errors")
        header.addWidget(self._error_count)
        
        self._warning_count = QLabel("0 Warnings")
        header.addWidget(self._warning_count)
        
        header.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_diagnostics)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # List widget
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list)
    
    def set_diagnostics(self, diagnostics: List[Dict[str, Any]]) -> None:
        """Set diagnostics to display."""
        self._diagnostics = diagnostics
        self._update_list()
    
    def _update_list(self) -> None:
        """Update the diagnostics list."""
        self._list.clear()
        
        errors = 0
        warnings = 0
        
        for diag in self._diagnostics:
            message = diag.get("message", "")
            severity = diag.get("severity", 4)
            range_data = diag.get("range", {})
            start = range_data.get("start", {})
            line = start.get("line", 0)
            
            # Count by severity
            if severity == 1:
                errors += 1
            elif severity == 2:
                warnings += 1
            
            # Create list item
            item = QListWidgetItem(f"Line {line + 1}: {message}")
            
            # Set icon based on severity
            if severity == 1:
                item.setForeground(QColor(242, 83, 80))  # Red
            elif severity == 2:
                item.setForeground(QColor(245, 189, 72))  # Orange
            
            item.setData(Qt.ItemDataRole.UserRole, diag)
            self._list.addItem(item)
        
        # Update counts
        self._error_count.setText(f"{errors} Errors")
        self._warning_count.setText(f"{warnings} Warnings")
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle item double click."""
        diag = item.data(Qt.ItemDataRole.UserRole)
        if diag:
            range_data = diag.get("range", {})
            start = range_data.get("start", {})
            line = start.get("line", 0)
            character = start.get("character", 0)
            self.diagnostic_clicked.emit("", line, character)
    
    def clear_diagnostics(self) -> None:
        """Clear all diagnostics."""
        self._diagnostics = []
        self._list.clear()
        self._error_count.setText("0 Errors")
        self._warning_count.setText("0 Warnings")


class GitPanel(QWidget):
    """
    Git integration panel widget.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        from PyQt6.QtWidgets import QLabel
        
        layout = QVBoxLayout(self)
        
        label = QLabel("Git Panel\n\nRepository status and operations will appear here.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


class NavigationBar(QWidget):
    """
    Navigation bar widget for file breadcrumbs.
    """
    
    path_selected = pyqtSignal(str)  # path
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        from PyQt6.QtWidgets import QHBoxLayout, QLabel
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        self._breadcrumb = QLabel("No file open")
        layout.addWidget(self._breadcrumb)
        
        layout.addStretch()
    
    def set_path(self, path: str) -> None:
        """Set the current path."""
        self._breadcrumb.setText(path)


class CommandPalette(QWidget):
    """
    Command palette for quick actions.
    """
    
    command_selected = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        from PyQt6.QtWidgets import QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
        from PyQt6.QtCore import Qt
        
        layout = QVBoxLayout(self)
        
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type a command...")
        layout.addWidget(self._search)
        
        self._commands = QListWidget()
        self._commands.itemDoubleClicked.connect(self._on_command_selected)
        layout.addWidget(self._commands)
        
        self._commands_dict: Dict[str, str] = {}
    
    def add_command(self, label: str, command: str) -> None:
        """Add a command to the palette."""
        item = QListWidgetItem(label)
        self._commands.addItem(item)
        self._commands_dict[command] = label
    
    def _on_command_selected(self, item: QListWidgetItem) -> None:
        """Handle command selection."""
        for cmd, lbl in self._commands_dict.items():
            if lbl == item.text():
                self.command_selected.emit(cmd)
                break