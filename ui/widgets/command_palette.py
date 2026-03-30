"""
Command Palette Widget
=======================
Quick command execution and search.
"""

from typing import Optional, Dict, Callable, List
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent


@dataclass
class Command:
    """Represents a command."""
    id: str
    label: str
    shortcut: str = ""
    callback: Optional[Callable] = None


class CommandPalette(QWidget):
    """
    Command palette for quick command execution.
    """
    
    command_executed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._commands: Dict[str, Command] = {}
        self._filtered_commands: List[Command] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        from PyQt6.QtCore import Qt
        
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type a command...")
        self._search.textChanged.connect(self._on_text_changed)
        self._search.keyPressEvent = self._on_key_press
        layout.addWidget(self._search)
        
        # Results list
        self._list = QListWidget()
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list)
        
        # Info label
        self._info = QLabel("")
        self._info.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self._info)
    
    def add_command(
        self,
        command_id: str,
        label: str,
        shortcut: str = "",
        callback: Optional[Callable] = None
    ) -> None:
        """Add a command to the palette."""
        command = Command(
            id=command_id,
            label=label,
            shortcut=shortcut,
            callback=callback
        )
        self._commands[command_id] = command
        self._filtered_commands.append(command)
    
    def remove_command(self, command_id: str) -> None:
        """Remove a command from the palette."""
        if command_id in self._commands:
            del self._commands[command_id]
            self._filtered_commands = [
                c for c in self._filtered_commands if c.id != command_id
            ]
    
    def _on_text_changed(self, text: str) -> None:
        """Handle text change."""
        self._filter_commands(text)
        self._update_list()
    
    def _filter_commands(self, query: str) -> None:
        """Filter commands by query."""
        if not query:
            self._filtered_commands = list(self._commands.values())
        else:
            query_lower = query.lower()
            self._filtered_commands = [
                c for c in self._commands.values()
                if query_lower in c.label.lower()
            ]
    
    def _update_list(self) -> None:
        """Update the command list."""
        self._list.clear()
        
        for command in self._filtered_commands:
            item = QListWidgetItem(command.label)
            if command.shortcut:
                item.setText(f"{command.label}  ({command.shortcut})")
            item.setData(Qt.ItemDataRole.UserRole, command.id)
            self._list.addItem(item)
        
        if self._filtered_commands:
            self._list.setCurrentRow(0)
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click."""
        self._execute_selected()
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle item double click."""
        self._execute_selected()
    
    def _on_key_press(self, event: QKeyEvent) -> None:
        """Handle key press."""
        if event.key() == Qt.Key.Key_Down:
            self._select_next()
        elif event.key() == Qt.Key.Key_Up:
            self._select_previous()
        elif event.key() == Qt.Key.Key_Return:
            self._execute_selected()
        elif event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            QLineEdit.keyPressEvent(self._search, event)
    
    def _select_next(self) -> None:
        """Select the next command."""
        current = self._list.currentRow()
        if current < self._list.count() - 1:
            self._list.setCurrentRow(current + 1)
    
    def _select_previous(self) -> None:
        """Select the previous command."""
        current = self._list.currentRow()
        if current > 0:
            self._list.setCurrentRow(current - 1)
    
    def _execute_selected(self) -> None:
        """Execute the selected command."""
        current_item = self._list.currentItem()
        if current_item:
            command_id = current_item.data(Qt.ItemDataRole.UserRole)
            command = self._commands.get(command_id)
            
            if command:
                if command.callback:
                    command.callback()
                
                self.command_executed.emit(command_id)
                self.hide()
    
    def show_at(self, x: int, y: int) -> None:
        """Show the palette at the specified position."""
        self._search.clear()
        self._filter_commands("")
        self._update_list()
        
        self.setFixedSize(400, 300)
        self.move(x, y)
        self.show()
        self._search.setFocus()
    
    def hide(self) -> None:
        """Hide the palette."""
        super().hide()
        self._search.clear()