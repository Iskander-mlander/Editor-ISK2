"""
Quick Open Dialog
=================
Fast file picker dialog similar to VS Code's Ctrl+P.
"""

from typing import Optional, List
import os
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QListWidget, QListWidgetItem, QLabel, QPushButton, QWidget)
from PyQt6.QtGui import QFont, QKeyEvent


class QuickOpenDialog(QDialog):
    """
    Quick file open dialog with fuzzy search.
    """
    
    file_selected = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None, root_path: str = "") -> None:
        super().__init__(parent)
        
        self._root_path = root_path or os.getcwd()
        self._files: List[str] = []
        self._filtered_files: List[str] = []
        self._setup_ui()
        self._scan_files()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        self.setWindowTitle("Quick Open")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search files...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 10px;
                font-size: 14px;
                background: #2d2d2d;
                color: #fff;
            }
        """)
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.installEventFilter(self)
        layout.addWidget(self._search_input)
        
        # Results list
        self._results_list = QListWidget()
        self._results_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: #1e1e1e;
                color: #fff;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background: #264f78;
            }
        """)
        self._results_list.itemDoubleClicked.connect(self._on_item_selected)
        layout.addWidget(self._results_list)
        
        # Status bar
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        self._status_label = QLabel("0 files")
        self._status_label.setStyleSheet("color: #888; font-size: 12px;")
        status_layout.addWidget(self._status_label)
        
        status_layout.addStretch()
        
        close_btn = QPushButton("Esc to close")
        close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #666;
            }
        """)
        close_btn.clicked.connect(self.close)
        status_layout.addWidget(close_btn)
        
        layout.addLayout(status_layout)
    
    def _scan_files(self) -> None:
        """Scan for files in the project."""
        self._files = []
        
        extensions = {'.py', '.txt', '.md', '.json', '.js', '.ts', '.jsx', '.tsx',
                    '.html', '.css', '.scss', '.yaml', '.yml', '.sh', '.bat',
                    '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs', '.xml'}
        
        for root, dirs, files in os.walk(self._root_path):
            # Skip hidden and common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                      ('__pycache__', 'node_modules', 'venv', '.venv', 'build', 'dist')]
            
            for file in files:
                if Path(file).suffix in extensions:
                    rel_path = os.path.relpath(os.path.join(root, file), self._root_path)
                    self._files.append(rel_path)
        
        self._files.sort()
        self._filtered_files = self._files[:100]  # Initial limit
        self._update_results()
    
    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        if not text:
            self._filtered_files = self._files[:100]
        else:
            text_lower = text.lower()
            self._filtered_files = [f for f in self._files if text_lower in f.lower()][:100]
        
        self._update_results()
    
    def _update_results(self) -> None:
        """Update the results list."""
        self._results_list.clear()
        
        for file_path in self._filtered_files:
            item = QListWidgetItem(file_path)
            self._results_list.addItem(item)
        
        self._status_label.setText(f"{len(self._filtered_files)} files")
        
        if self._filtered_files:
            self._results_list.setCurrentRow(0)
    
    def _on_item_selected(self, item: QListWidgetItem) -> None:
        """Handle item selection."""
        file_path = item.text()
        full_path = os.path.join(self._root_path, file_path)
        self.file_selected.emit(full_path)
        self.close()
    
    def eventFilter(self, obj, event) -> bool:
        """Handle keyboard events."""
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                self._results_list.setCurrentRow(
                    min(self._results_list.currentRow() + 1, self._results_list.count() - 1)
                )
                return True
            elif event.key() == Qt.Key.Key_Up:
                self._results_list.setCurrentRow(
                    max(self._results_list.currentRow() - 1, 0)
                )
                return True
            elif event.key() == Qt.Key.Key_Return:
                if self._results_list.currentItem():
                    self._on_item_selected(self._results_list.currentItem())
                return True
            elif event.key() == Qt.Key.Key_Escape:
                self.close()
                return True
        return super().eventFilter(obj, event)


def show_quick_open(parent: Optional[QWidget] = None, root_path: str = "") -> QuickOpenDialog:
    """Show the quick open dialog."""
    dialog = QuickOpenDialog(parent, root_path)
    dialog.exec()
    return dialog