"""
Navigation Bar Widget
=====================
File path navigation and symbol selector.
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QMenu, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class NavigationBar(QWidget):
    """
    Navigation bar for showing file path and symbols.
    """
    
    symbol_selected = pyqtSignal(str, int)  # symbol, line
    path_clicked = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._symbols: List[Dict[str, Any]] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # File path label
        self._path_label = QLabel("No file open")
        self._path_label.setFont(QFont("sans-serif", 9))
        self._path_label.mousePressEvent = self._on_path_click
        layout.addWidget(self._path_label)
        
        layout.addStretch()
        
        # Symbol selector
        self._symbol_combo = QComboBox()
        self._symbol_combo.setMinimumWidth(150)
        self._symbol_combo.currentIndexChanged.connect(self._on_symbol_changed)
        layout.addWidget(self._symbol_combo)
    
    def set_path(self, path: str) -> None:
        """Set the file path."""
        self._path_label.setText(path)
    
    def set_symbols(self, symbols: List[Dict[str, Any]]) -> None:
        """Set the list of symbols."""
        self._symbols = symbols
        
        self._symbol_combo.clear()
        self._symbol_combo.addItem("-- Symbols --")
        
        for symbol in symbols:
            name = symbol.get("name", "")
            kind = symbol.get("kind", "")
            self._symbol_combo.addItem(f"{kind}: {name}")
    
    def _on_path_click(self, event) -> None:
        """Handle path label click."""
        self.path_clicked.emit(self._path_label.text())
    
    def _on_symbol_changed(self, index: int) -> None:
        """Handle symbol selection change."""
        if index > 0 and index <= len(self._symbols):
            symbol = self._symbols[index - 1]
            name = symbol.get("name", "")
            line = symbol.get("line", 0)
            self.symbol_selected.emit(name, line)


class CommandPalette(QWidget):
    """
    Command palette for quick command execution.
    """
    
    command_selected = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        from PyQt6.QtWidgets import QVBoxLayout, QLineEdit, QListWidget
        
        layout = QVBoxLayout(self)
        
        # Search input
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type command...")
        layout.addWidget(self._search)
        
        # Results list
        self._list = QListWidget()
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)
        
        self._commands: Dict[str, str] = {}
    
    def add_command(self, label: str, command: str) -> None:
        """Add a command."""
        self._commands[command] = label
        self._list.addItem(label)
    
    def _on_item_clicked(self, item) -> None:
        """Handle item click."""
        for cmd, lbl in self._commands.items():
            if lbl == item.text():
                self.command_selected.emit(cmd)
                break