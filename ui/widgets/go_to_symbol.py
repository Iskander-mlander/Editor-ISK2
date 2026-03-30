"""
Go to Symbol Dialog
===================
Quick navigation dialog to jump to symbols in the current file.
"""

from typing import Optional, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QPushButton
)
from PyQt6.QtGui import QFont

from core.utils import icon_manager


class GoToSymbolDialog(QDialog):
    """
    Dialog to quickly navigate to a symbol in the current file.
    """
    
    symbol_selected = pyqtSignal(int)  # line number
    
    def __init__(self, symbols: List[dict], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._symbols = symbols
        
        self.setWindowTitle("Go to Symbol")
        self.setMinimumSize(400, 300)
        self.setModal(True)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Search input
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter symbols...")
        self._search.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self._search)
        
        # Symbol list
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_select)
        layout.addWidget(self._list)
        
        # Buttons
        buttons = QHBoxLayout()
        
        go_btn = QPushButton("Go to")
        go_btn.clicked.connect(self._on_select)
        buttons.addWidget(go_btn)
        
        buttons.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        
        # Populate list
        self._populate_list()
    
    def _populate_list(self, filter_text: str = "") -> None:
        """Populate the symbol list."""
        self._list.clear()
        
        for symbol in self._symbols:
            name = symbol.get("name", "")
            if filter_text and filter_text.lower() not in name.lower():
                continue
            
            line = symbol.get("line", 0)
            symbol_type = symbol.get("type", "")
            
            item = QListWidgetItem(f"{name} ({symbol_type}) - Line {line}")
            item.setData(Qt.ItemDataRole.UserRole, line)
            
            if symbol_type == "function":
                item.setIcon(icon_manager.get_icon("function", 16))
            elif symbol_type == "class":
                item.setIcon(icon_manager.get_icon("class", 16))
            elif symbol_type == "method":
                item.setIcon(icon_manager.get_icon("method", 16))
            
            self._list.addItem(item)
    
    def _on_filter_changed(self, text: str) -> None:
        """Handle filter text change."""
        self._populate_list(text)
    
    def _on_select(self) -> None:
        """Handle selection."""
        item = self._list.currentItem()
        if item:
            line = item.data(Qt.ItemDataRole.UserRole)
            self.symbol_selected.emit(line)
            self.accept()


def show_go_to_symbol(symbols: List[dict], parent: Optional[QWidget] = None) -> Optional[int]:
    """
    Show the go to symbol dialog.
    Returns the selected line number or None.
    """
    dialog = GoToSymbolDialog(symbols, parent)
    
    result = dialog.exec()
    if result == dialog.Accepted:
        return dialog.symbol_selected.emit
    return None