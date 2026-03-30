"""
Find and Replace Panel
=======================
Professional Find and Replace widget similar to Geany.
"""

from dataclasses import dataclass
from typing import Optional, List, Callable
from enum import Enum, auto

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QCheckBox, QRadioButton,
    QButtonGroup, QLabel, QGroupBox, QDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextCursor, QTextDocument


class SearchMode(Enum):
    """Search mode options."""
    NORMAL = auto()
    REGEX = auto()
    WHOLE_WORD = auto()


class SearchDirection(Enum):
    """Search direction."""
    FORWARD = auto()
    BACKWARD = auto()


@dataclass
class SearchResult:
    """Represents a search result."""
    line: int
    column: int
    length: int
    text: str


class FindReplacePanel(QWidget):
    """
    Professional Find and Replace panel.
    """
    
    # Signals
    find_next = pyqtSignal(str)
    find_previous = pyqtSignal(str)
    replace_one = pyqtSignal(str, str)
    replace_all = pyqtSignal(str, str)
    close_requested = pyqtSignal()
    
    # For external control
    find_in_document = pyqtSignal(str, int)  # text, flags
    replace_in_document = pyqtSignal(str, str, int)  # search, replace, flags
    replace_all_in_document = pyqtSignal(str, str, int)  # search, replace, flags
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._document = None
        self._results: List[SearchResult] = []
        self._current_result_index = -1
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Find section
        find_group = QGroupBox("Find")
        find_layout = QGridLayout(find_group)
        
        # Search text
        find_layout.addWidget(QLabel("Search:"), 0, 0)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Text to find...")
        self._search_input.returnPressed.connect(self._on_find_next)
        find_layout.addWidget(self._search_input, 0, 1, 1, 2)
        
        # Find buttons
        self._find_prev_btn = QPushButton("Previous")
        self._find_prev_btn.clicked.connect(self._on_find_previous)
        find_layout.addWidget(self._find_prev_btn, 0, 3)
        
        self._find_next_btn = QPushButton("Next")
        self._find_next_btn.clicked.connect(self._on_find_next)
        find_layout.addWidget(self._find_next_btn, 0, 4)
        
        # Find options
        self._case_sensitive = QCheckBox("Case sensitive")
        find_layout.addWidget(self._case_sensitive, 1, 1)
        
        self._whole_word = QCheckBox("Whole word")
        find_layout.addWidget(self._whole_word, 1, 2)
        
        self._regex = QCheckBox("Regular expression")
        find_layout.addWidget(self._regex, 1, 3)
        
        layout.addWidget(find_group)
        
        # Replace section
        replace_group = QGroupBox("Replace")
        replace_layout = QGridLayout(replace_group)
        
        # Replace text
        replace_layout.addWidget(QLabel("Replace with:"), 0, 0)
        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("Replacement text...")
        replace_layout.addWidget(self._replace_input, 0, 1, 1, 3)
        
        # Replace buttons
        self._replace_one_btn = QPushButton("Replace")
        self._replace_one_btn.clicked.connect(self._on_replace_one)
        replace_layout.addWidget(self._replace_one_btn, 1, 1)
        
        self._replace_all_btn = QPushButton("Replace All")
        self._replace_all_btn.clicked.connect(self._on_replace_all)
        replace_layout.addWidget(self._replace_all_btn, 1, 2)
        
        # Direction
        direction_group = QGroupBox("Direction")
        direction_layout = QHBoxLayout(direction_group)
        
        self._forward_btn = QRadioButton("Forward")
        self._forward_btn.setChecked(True)
        direction_layout.addWidget(self._forward_btn)
        
        self._backward_btn = QRadioButton("Backward")
        direction_layout.addWidget(self._backward_btn)
        
        self._wrap_around = QCheckBox("Wrap around")
        self._wrap_around.setChecked(True)
        direction_layout.addWidget(self._wrap_around)
        
        layout.addWidget(direction_group)
        
        # Status label
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.close_requested.emit)
        close_layout.addWidget(self._close_btn)
        layout.addLayout(close_layout)
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._search_input.textChanged.connect(self._on_search_text_changed)
    
    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text changes."""
        self._results = []
        self._current_result_index = -1
        self._status_label.setText("")
    
    def _get_search_flags(self) -> int:
        """Get search flags based on options."""
        flags = 0
        
        if self._case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        
        if self._whole_word.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
        
        if not self._forward_btn.isChecked():
            flags |= QTextDocument.FindFlag.FindBackward
        
        return flags
    
    def _on_find_next(self) -> None:
        """Handle Find Next button click."""
        self._search(direction_forward=True)
    
    def _on_find_previous(self) -> None:
        """Handle Find Previous button click."""
        self._search(direction_forward=False)
    
    def _search(self, direction_forward: bool = True) -> bool:
        """Perform search operation."""
        if not self._document or not self._search_input.text():
            return False
        
        search_text = self._search_input.text()
        
        # Determine direction
        if direction_forward:
            flags = self._get_search_flags() & ~QTextDocument.FindFlag.FindBackward
        else:
            flags = self._get_search_flags() | QTextDocument.FindFlag.FindBackward
        
        # Use the editor's cursor as starting point
        cursor = self._document.find(search_text, flags)
        
        if cursor.isNull():
            # Wrap around if enabled
            if self._wrap_around.isChecked():
                # Start from the beginning (or end for backward)
                if direction_forward:
                    # Start from beginning
                    cursor = QTextCursor(self._document)
                    cursor.movePosition(cursor.MoveOperation.Start)
                else:
                    # Start from end
                    cursor = QTextCursor(self._document)
                    cursor.movePosition(cursor.MoveOperation.End)
                
                cursor = self._document.find(search_text, cursor, flags)
            
            if cursor.isNull():
                self._status_label.setText("Pattern not found")
                return False
        
        # Emit signal to move cursor
        self.find_in_document.emit(search_text, flags)
        
        self._status_label.setText("Found")
        return True
    
    def _on_replace_one(self) -> None:
        """Handle Replace button click."""
        self._replace(direction_forward=True)
    
    def _on_replace_all(self) -> None:
        """Handle Replace All button click."""
        if not self._document or not self._search_input.text():
            return
        
        search_text = self._search_input.text()
        replace_text = self._replace_input.text()
        flags = self._get_search_flags()
        
        count = 0
        cursor = QTextCursor(self._document)
        cursor.movePosition(cursor.MoveOperation.Start)
        
        while True:
            cursor = self._document.find(search_text, cursor, flags)
            
            if cursor.isNull():
                break
            
            # Replace the text
            cursor.beginEditBlock()
            cursor.insertText(replace_text)
            cursor.endEditBlock()
            count += 1
        
        self._status_label.setText(f"Replaced {count} occurrence(s)")
    
    def _replace(self, direction_forward: bool = True) -> bool:
        """Perform single replace operation."""
        if not self._document or not self._search_input.text():
            return False
        
        search_text = self._search_input.text()
        replace_text = self._replace_input.text()
        
        # Get current cursor from document
        cursor = self._document.textCursor()
        
        # If no selection, find next first
        if not cursor.hasSelection():
            if not self._search(direction_forward):
                return False
            cursor = self._document.textCursor()
        
        # Check if current position matches search text
        selected_text = cursor.selectedText()
        
        # Simple comparison - if the selected text matches, replace it
        if self._case_sensitive.isChecked():
            matches = selected_text == search_text
        else:
            matches = selected_text.lower() == search_text.lower()
        
        if matches:
            cursor.beginEditBlock()
            cursor.insertText(replace_text)
            cursor.endEditBlock()
        
        # Find next occurrence
        return self._search(direction_forward)
    
    def set_document(self, document) -> None:
        """Set the document to search in."""
        self._document = document
    
    def set_editor(self, editor) -> None:
        """Set the editor widget for cursor operations."""
        self._editor = editor


class FindReplaceDialog(QDialog):
    """
    Standalone Find/Replace dialog.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setWindowTitle("Find / Replace")
        self.setMinimumWidth(400)
        
        self._panel = FindReplacePanel(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self._panel)
        
        self._panel.close_requested.connect(self.close)
    
    def set_document(self, document) -> None:
        """Set the document to search in."""
        self._panel.set_document(document)


# Factory function to show as floating panel
def show_find_replace(parent: QWidget, editor) -> FindReplacePanel:
    """
    Show the Find/Replace panel as a floating widget.
    
    Args:
        parent: Parent widget
        editor: Editor widget to search in
        
    Returns:
        FindReplacePanel instance
    """
    panel = FindReplacePanel(parent)
    panel.set_document(editor.document() if hasattr(editor, 'document') else None)
    panel.set_editor(editor)
    
    # Make it a floating window
    panel.setWindowFlags(
        Qt.WindowType.Tool | 
        Qt.WindowType.WindowStaysOnTopHint
    )
    panel.setWindowTitle("Find / Replace")
    
    # Position it near the parent
    if parent:
        pos = parent.mapToGlobal(parent.rect().topRight())
        panel.move(pos.x() - panel.width(), pos.y())
    
    panel.show()
    
    return panel