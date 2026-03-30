"""
Split Editor Widget
====================
Provides split editor functionality with horizontal/vertical splits.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple

from PyQt6.QtCore import pyqtSignal, Qt, QObject
from PyQt6.QtWidgets import QSplitter, QWidget, QVBoxLayout

from core.editor import CodeEditor, SyntaxHighlighter


@dataclass
class EditorSplit:
    """Represents an editor split."""
    editor: CodeEditor
    highlighter: SyntaxHighlighter
    file_path: Optional[str] = None
    is_modified: bool = False


class SplitEditorSignals(QObject):
    """Signals for split editor events."""
    split_created = pyqtSignal(int)  # split index
    split_closed = pyqtSignal(int)
    split_focused = pyqtSignal(int)
    editor_changed = pyqtSignal(CodeEditor)


class SplitEditorManager(QWidget):
    """
    Manages multiple editor splits.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._signals = SplitEditorSignals()
        self._splits: List[EditorSplit] = []
        self._active_split: int = 0
        
        self._setup_ui()
    
    @property
    def signals(self) -> SplitEditorSignals:
        """Get split editor signals."""
        return self._signals
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self._splitter)
    
    def create_split(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                     file_path: Optional[str] = None) -> int:
        """Create a new editor split. Returns split index."""
        editor = CodeEditor()
        highlighter = SyntaxHighlighter(editor.document())
        
        split = EditorSplit(
            editor=editor,
            highlighter=highlighter,
            file_path=file_path
        )
        
        index = len(self._splits)
        self._splits.append(split)
        self._splitter.addWidget(editor)
        
        self._signals.split_created.emit(index)
        
        return index
    
    def close_split(self, index: int) -> bool:
        """Close a split at index. Returns True if successful."""
        if index < 0 or index >= len(self._splits):
            return False
        
        if len(self._splits) <= 1:
            return False
        
        split = self._splits[index]
        split.editor.hide()
        split.editor.deleteLater()
        
        del self._splits[index]
        
        if self._active_split >= len(self._splits):
            self._active_split = len(self._splits) - 1
        
        self._signals.split_closed.emit(index)
        
        return True
    
    def get_split_count(self) -> int:
        """Get the number of splits."""
        return len(self._splits)
    
    def get_active_split(self) -> int:
        """Get the active split index."""
        return self._active_split
    
    def set_active_split(self, index: int) -> None:
        """Set the active split."""
        if 0 <= index < len(self._splits):
            self._active_split = index
            self._signals.split_focused.emit(index)
    
    def get_active_editor(self) -> Optional[CodeEditor]:
        """Get the active editor."""
        if 0 <= self._active_split < len(self._splits):
            return self._splits[self._active_split].editor
        return None
    
    def get_split_editor(self, index: int) -> Optional[CodeEditor]:
        """Get editor at specific split."""
        if 0 <= index < len(self._splits):
            return self._splits[index].editor
        return None
    
    def split_horizontal(self) -> int:
        """Create a horizontal split."""
        self._splitter.setOrientation(Qt.Orientation.Horizontal)
        return self.create_split(Qt.Orientation.Horizontal)
    
    def split_vertical(self) -> int:
        """Create a vertical split."""
        self._splitter.setOrientation(Qt.Orientation.Vertical)
        return self.create_split(Qt.Orientation.Vertical)
    
    def close_active_split(self) -> bool:
        """Close the active split."""
        return self.close_split(self._active_split)
    
    def focus_next_split(self) -> None:
        """Focus the next split."""
        if self._active_split < len(self._splits) - 1:
            self.set_active_split(self._active_split + 1)
    
    def focus_previous_split(self) -> None:
        """Focus the previous split."""
        if self._active_split > 0:
            self.set_active_split(self._active_split - 1)


def create_split_manager(parent: Optional[QWidget] = None) -> SplitEditorManager:
    """Create a new split editor manager."""
    return SplitEditorManager(parent)
