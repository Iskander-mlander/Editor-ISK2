"""
Diff Viewer Widget
==================
Widget to display file differences.
"""

from typing import Optional, List, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QTextEdit, QSplitter, QFileDialog,
                            QMessageBox)
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor

from core.utils.diff import DiffComputer, DiffResult


class DiffViewer(QWidget):
    """
    Widget to display file differences.
    """
    
    file_selected = pyqtSignal(str)  # file path
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._diff_computer = DiffComputer()
        self._old_file: str = ""
        self._new_file: str = ""
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Diff Viewer")
        title.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        compare_btn = QPushButton("Select Files...")
        compare_btn.clicked.connect(self._on_select_files)
        header_layout.addWidget(compare_btn)
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setMaximumWidth(25)
        refresh_btn.clicked.connect(self._on_refresh)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # File labels
        files_layout = QHBoxLayout()
        
        self._old_label = QLabel("Original: (not selected)")
        self._old_label.setStyleSheet("color: #FF6B6B;")
        files_layout.addWidget(self._old_label)
        
        files_layout.addStretch()
        
        self._new_label = QLabel("Modified: (not selected)")
        self._new_label.setStyleSheet("color: #4ECDC4;")
        files_layout.addWidget(self._new_label)
        
        layout.addLayout(files_layout)
        
        # Splitter for side-by-side view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Old file view
        self._old_view = QTextEdit()
        self._old_view.setReadOnly(True)
        self._old_view.setFont(QFont("monospace", 10))
        splitter.addWidget(self._old_view)
        
        # New file view
        self._new_view = QTextEdit()
        self._new_view.setReadOnly(True)
        self._new_view.setFont(QFont("monospace", 10))
        splitter.addWidget(self._new_view)
        
        layout.addWidget(splitter)
        
        # Stats
        stats_layout = QHBoxLayout()
        
        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet("color: #888;")
        stats_layout.addWidget(self._stats_label)
        
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
    
    def _on_select_files(self) -> None:
        """Select files to compare."""
        old_file, _ = QFileDialog.getOpenFileName(self, "Select Original File")
        if not old_file:
            return
        
        new_file, _ = QFileDialog.getOpenFileName(self, "Select Modified File")
        if not new_file:
            return
        
        self._old_file = old_file
        self._new_file = new_file
        
        self._old_label.setText(f"Original: {old_file}")
        self._new_label.setText(f"Modified: {new_file}")
        
        self._compute_diff()
    
    def _on_refresh(self) -> None:
        """Refresh the diff view."""
        if self._old_file and self._new_file:
            self._compute_diff()
    
    def _compute_diff(self) -> None:
        """Compute and display diff."""
        if not self._old_file or not self._new_file:
            return
        
        result = self._diff_computer.compute_file_diff(self._old_file, self._new_file)
        
        # Load file contents
        try:
            with open(self._old_file, 'r', encoding='utf-8') as f:
                old_text = f.read()
        except Exception:
            old_text = ""
        
        try:
            with open(self._new_file, 'r', encoding='utf-8') as f:
                new_text = f.read()
        except Exception:
            new_text = ""
        
        # Generate side-by-side
        old_lines, new_lines = self._diff_computer.side_by_side(old_text, new_text)
        
        # Display with coloring
        self._display_diff(old_lines, new_lines)
        
        # Update stats
        self._stats_label.setText(
            f"Added: {result.total_added} lines | "
            f"Removed: {result.total_removed} lines | "
            f"Changes: {result.total_added + result.total_removed} total"
        )
    
    def _display_diff(self, old_lines: List[str], new_lines: List[str]) -> None:
        """Display diff with syntax highlighting."""
        
        # Configure colors
        added_format = QTextCharFormat()
        added_format.setBackground(QColor(46, 204, 113, 50))
        
        removed_format = QTextCharFormat()
        removed_format.setBackground(QColor(231, 76, 60, 50))
        
        # Clear and populate old view
        self._old_view.clear()
        for line in old_lines:
            cursor = self._old_view.textCursor()
            if line.startswith('-'):
                cursor.setCharFormat(removed_format)
            cursor.insertText(line + '\n')
        
        # Clear and populate new view
        self._new_view.clear()
        for line in new_lines:
            cursor = self._new_view.textCursor()
            if line.startswith('+'):
                cursor.setCharFormat(added_format)
            cursor.insertText(line + '\n')
    
    def compare_text(self, old_text: str, new_text: str) -> None:
        """Compare two text strings."""
        self._old_label.setText("Original: (text)")
        self._new_label.setText("Modified: (text)")
        
        old_lines, new_lines = self._diff_computer.side_by_side(old_text, new_text)
        self._display_diff(old_lines, new_lines)
        
        result = self._diff_computer.compute_text_diff(old_text, new_text)
        self._stats_label.setText(
            f"Added: {result.total_added} lines | "
            f"Removed: {result.total_removed} lines"
        )


def show_diff_viewer(parent: Optional[QWidget] = None) -> DiffViewer:
    """Create and return a diff viewer."""
    return DiffViewer(parent)