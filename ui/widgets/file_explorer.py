"""
File Explorer Widget
====================
File tree view with signal-based communication.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon

from core.utils import FileUtils


class FileExplorerSignals:
    """Signals for file explorer events."""
    file_selected = pyqtSignal(str)
    directory_changed = pyqtSignal(str)
    file_created = pyqtSignal(str)
    file_deleted = pyqtSignal(str)
    file_renamed = pyqtSignal(str, str)


class FileExplorer(QWidget):
    """
    File explorer widget with tree view.
    """
    
    file_selected = pyqtSignal(str)
    directory_changed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._root_path: Optional[Path] = None
        self._file_filter: Optional[List[str]] = None
        self._show_hidden: bool = False
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Path bar
        path_layout = QHBoxLayout()
        
        self._path_input = QLineEdit()
        self._path_input.setPlaceholderText("Enter path...")
        self._path_input.returnPressed.connect(self._on_path_submitted)
        path_layout.addWidget(self._path_input)
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedWidth(30)
        refresh_btn.clicked.connect(self._refresh)
        path_layout.addWidget(refresh_btn)
        
        layout.addLayout(path_layout)
        
        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._tree)
    
    def set_root_path(self, path: str) -> None:
        """Set the root path for the explorer."""
        self._root_path = Path(path)
        self._path_input.setText(str(self._root_path))
        self._refresh()
    
    @property
    def root_path(self) -> Optional[str]:
        """Get the current root path."""
        return str(self._root_path) if self._root_path else None
    
    def set_file_filter(self, extensions: List[str]) -> None:
        """Set file extension filter."""
        self._file_filter = extensions
        self._refresh()
    
    def set_show_hidden(self, show: bool) -> None:
        """Set whether to show hidden files."""
        self._show_hidden = show
        self._refresh()
    
    def _refresh(self) -> None:
        """Refresh the file tree."""
        self._tree.clear()
        
        if not self._root_path or not self._root_path.exists():
            return
        
        self._build_tree(self._root_path, self._tree.invisibleRootItem())
    
    def _build_tree(self, path: Path, parent: QTreeWidgetItem) -> None:
        """Build the tree recursively."""
        try:
            items = FileUtils.list_directory(
                path,
                include_dirs=True,
                recursive=False,
                filter_ext=self._file_filter
            )
            
            for item_path in sorted(items):
                # Skip hidden files if not showing them
                if not self._show_hidden and item_path.name.startswith('.'):
                    continue
                
                # Create tree item
                item = QTreeWidgetItem(parent)
                item.setText(0, item_path.name)
                item.setData(0, Qt.ItemDataRole.UserRole, str(item_path))
                
                # Set icon based on type
                if item_path.is_dir():
                    item.setIcon(0, QIcon.fromTheme("folder"))
                    # Add placeholder for lazy loading
                    QTreeWidgetItem(item)
                else:
                    item.setIcon(0, QIcon.fromTheme("text-x-generic"))
                    
        except PermissionError:
            pass
    
    def _on_path_submitted(self) -> None:
        """Handle path submission."""
        path = self._path_input.text()
        if Path(path).exists():
            self.set_root_path(path)
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click."""
        pass  # Optional: show info
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double click."""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            path_obj = Path(path)
            if path_obj.is_file():
                self.file_selected.emit(path)
            elif path_obj.is_dir():
                # Expand/collapse
                if item.childCount() == 1 and not item.child(0).text(0):
                    # Placeholder - load children
                    item.takeChildren()
                    self._build_tree(path_obj, item)
                    self.directory_changed.emit(path)