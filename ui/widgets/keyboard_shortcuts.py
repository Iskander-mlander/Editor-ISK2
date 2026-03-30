"""
Keyboard Shortcuts Panel
=========================
Dialog to display all available keyboard shortcuts.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel,
                            QLineEdit, QWidget)

from core.utils.shortcuts import ShortcutManager


class KeyboardShortcutsDialog(QDialog):
    """
    Dialog to display and search keyboard shortcuts.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._shortcut_manager = ShortcutManager()
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_box = QLineEdit()
        self._search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_box)
        layout.addLayout(search_layout)
        
        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Action", "Shortcut", "Category"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # Load shortcuts
        self._load_shortcuts()
    
    def _load_shortcuts(self) -> None:
        """Load all shortcuts into the table."""
        shortcuts = self._shortcut_manager.get_all_shortcuts()
        
        self._table.setRowCount(len(shortcuts))
        
        for i, shortcut in enumerate(shortcuts):
            action_item = QTableWidgetItem(shortcut.description)
            action_item.setData(Qt.ItemDataRole.UserRole, shortcut.id)
            self._table.setItem(i, 0, action_item)
            
            key_seq = QKeySequence(shortcut.key_sequence)
            self._table.setItem(i, 1, QTableWidgetItem(key_seq.toString()))
            
            self._table.setItem(i, 2, QTableWidgetItem(shortcut.category.value))
    
    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        text = text.lower()
        
        for row in range(self._table.rowCount()):
            show = False
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                if item and text in item.text().lower():
                    show = True
                    break
            self._table.setRowHidden(row, not show)


def show_shortcuts_dialog(parent: Optional[QWidget] = None) -> None:
    """Show the keyboard shortcuts dialog."""
    dialog = KeyboardShortcutsDialog(parent)
    dialog.exec()