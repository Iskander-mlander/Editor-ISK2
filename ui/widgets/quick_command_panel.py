"""
Quick Command Panel
===================
A panel to quickly execute terminal commands.
"""

from typing import Optional, List, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QLabel
)
from PyQt6.QtGui import QKeyEvent


class QuickCommand:
    """Represents a quick command."""
    
    def __init__(self, name: str, command: str, description: str = "",
                 shortcut: str = "") -> None:
        self.name = name
        self.command = command
        self.description = description
        self.shortcut = shortcut


class QuickCommandPanel(QDialog):
    """
    Quick command panel for terminal commands.
    """
    
    command_selected = pyqtSignal(str)  # command
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._commands: List[QuickCommand] = []
        
        self.setWindowTitle("Quick Command")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self._setup_ui()
        self._load_default_commands()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Quick Commands")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Search input
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search commands...")
        self._search.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self._search)
        
        # Command list
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_select)
        layout.addWidget(self._list)
        
        # Buttons
        buttons = QHBoxLayout()
        
        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self._on_select)
        buttons.addWidget(execute_btn)
        
        buttons.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(close_btn)
        
        layout.addLayout(buttons)
    
    def _load_default_commands(self) -> None:
        """Load default quick commands."""
        self._commands = [
            QuickCommand("Git Status", "git status", "Show git status", "Ctrl+G"),
            QuickCommand("Git Add All", "git add .", "Stage all changes"),
            QuickCommand("Git Commit", "git commit -m", "Commit changes"),
            QuickCommand("Git Pull", "git pull", "Pull from remote"),
            QuickCommand("Git Push", "git push", "Push to remote"),
            QuickCommand("Run Python", "python3", "Run Python script"),
            QuickCommand("Run Tests", "python -m pytest", "Run pytest"),
            QuickCommand("Install Package", "pip install", "Install pip package"),
            QuickCommand("List Files", "ls -la", "List files with details"),
            QuickCommand("Disk Usage", "du -sh", "Show disk usage"),
            QuickCommand("Process List", "ps aux", "Show processes"),
            QuickCommand("Kill Process", "kill -9", "Kill process by PID"),
            QuickCommand("Docker PS", "docker ps", "List containers"),
            QuickCommand("Docker Images", "docker images", "List images"),
            QuickCommand("NPM Install", "npm install", "Install npm packages"),
            QuickCommand("NPM Run", "npm run", "Run npm script"),
        ]
        
        self._populate_list()
    
    def _populate_list(self, filter_text: str = "") -> None:
        """Populate the command list."""
        self._list.clear()
        
        for cmd in self._commands:
            if filter_text and filter_text.lower() not in cmd.name.lower():
                continue
            
            text = f"{cmd.name}"
            if cmd.shortcut:
                text += f" ({cmd.shortcut})"
            if cmd.description:
                text += f" - {cmd.description}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, cmd.command)
            self._list.addItem(item)
    
    def _on_filter_changed(self, text: str) -> None:
        """Handle filter text change."""
        self._populate_list(text)
    
    def _on_select(self) -> None:
        """Handle selection."""
        item = self._list.currentItem()
        if item:
            command = item.data(Qt.ItemDataRole.UserRole)
            self.command_selected.emit(command)
            self.accept()
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return:
            self._on_select()
        else:
            super().keyPressEvent(event)


def show_quick_command_panel(parent: Optional[QWidget] = None) -> Optional[str]:
    """Show quick command panel and return selected command."""
    dialog = QuickCommandPanel(parent)
    
    result = dialog.exec()
    if result == dialog.Accepted:
        return dialog.command_selected.emit
    return None