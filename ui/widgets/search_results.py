"""
Search Results Panel
=====================
Panel to display search results from "Find in Files" functionality.
"""

from typing import Optional, List, Dict, Any, Callable

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QListWidgetItem, QPushButton,
                            QLineEdit, QCheckBox)
from PyQt6.QtGui import QColor, QFont


@dataclass
class SearchResult:
    """Represents a search result."""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int


class SearchResultsPanel(QWidget):
    """
    Panel to display search results from Find in Files.
    """
    
    result_clicked = pyqtSignal(str, int, int, int)  # file, line, start, end
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._results: List[SearchResult] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Header
        header_layout = QHBoxLayout()
        
        self._title_label = QLabel("Search Results")
        self._title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self._title_label)
        
        header_layout.addStretch()
        
        self._count_label = QLabel("0 results")
        self._count_label.setStyleSheet("color: #888;")
        header_layout.addWidget(self._count_label)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(50)
        clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Results list
        self._results_list = QListWidget()
        self._results_list.itemDoubleClicked.connect(self._on_result_clicked)
        layout.addWidget(self._results_list)
    
    def set_results(self, results: List[SearchResult]) -> None:
        """Set search results."""
        self._results = results
        self._update_list()
    
    def add_results(self, results: List[SearchResult]) -> None:
        """Add more results."""
        self._results.extend(results)
        self._update_list()
    
    def clear(self) -> None:
        """Clear all results."""
        self._results.clear()
        self._results_list.clear()
        self._count_label.setText("0 results")
    
    def _update_list(self) -> None:
        """Update the results list."""
        self._results_list.clear()
        
        # Group by file
        by_file: Dict[str, List[SearchResult]] = {}
        for result in self._results:
            if result.file_path not in by_file:
                by_file[result.file_path] = []
            by_file[result.file_path].append(result)
        
        # Add to list
        for file_path, results in by_file.items():
            # File header
            file_item = QListWidgetItem(f"📁 {file_path} ({len(results)} matches)")
            file_item.setForeground(QColor(100, 149, 237))
            file_item.setFont(QFont("Sans-serif", 10, QFont.Weight.Bold))
            file_item.setData(Qt.ItemDataRole.UserRole, None)
            self._results_list.addItem(file_item)
            
            # Results
            for result in results:
                line_text = result.line_content.strip()
                if len(line_text) > 80:
                    line_text = line_text[:80] + "..."
                
                item = QLabel(f"  {result.line_number}: {line_text}")
                item.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
                
                list_item = QListWidgetItem()
                list_item.setData(Qt.ItemDataRole.UserRole, result)
                self._results_list.addItem(list_item)
                
                # Use custom widget for better formatting
                widget = QWidget()
                widget_layout = QHBoxLayout(widget)
                widget_layout.setContentsMargins(0, 2, 0, 2)
                
                line_label = QLabel(f"{result.line_number}:")
                line_label.setStyleSheet("color: #888; min-width: 40px;")
                widget_layout.addWidget(line_label)
                
                content_label = QLabel(line_text)
                content_label.setTextFormat(Qt.TextFormat.PlainText)
                widget_layout.addWidget(content_label)
                
                self._results_list.setItemWidget(list_item, widget)
        
        self._count_label.setText(f"{len(self._results)} results")
    
    def _on_result_clicked(self, item: QListWidgetItem) -> None:
        """Handle result click."""
        result: Optional[SearchResult] = item.data(Qt.ItemDataRole.UserRole)
        if result:
            self.result_clicked.emit(
                result.file_path,
                result.line_number,
                result.match_start,
                result.match_end
            )


def show_search_results(parent: Optional[QWidget] = None) -> SearchResultsPanel:
    """Create and return a search results panel."""
    return SearchResultsPanel(parent)