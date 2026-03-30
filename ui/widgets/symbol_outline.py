"""
Symbol Outline Panel
====================
Panel to display symbols (functions, classes, etc.) in the current file.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import re

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QListWidgetItem, QPushButton, QLabel, QComboBox)
from PyQt6.QtGui import QColor, QFont, QIcon


@dataclass
class Symbol:
    """Represents a code symbol."""
    name: str
    line: int
    symbol_type: str  # "function", "class", "method", "variable", "import"
    icon: str = ""


class SymbolOutlinePanel(QWidget):
    """
    Panel to display symbols in the current file.
    """
    
    symbol_selected = pyqtSignal(str, int)  # symbol_name, line
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._symbols: List[Symbol] = []
        self._current_file: str = ""
        self._current_language: str = "python"
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Outline")
        title.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setMaximumWidth(25)
        refresh_btn.setToolTip("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filter combo
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Functions", "Classes", "Methods", "Variables", "Imports"])
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self._filter_combo)
        
        # Symbol list
        self._symbol_list = QListWidget()
        self._symbol_list.itemDoubleClicked.connect(self._on_symbol_clicked)
        layout.addWidget(self._symbol_list)
    
    def set_content(self, file_path: str, content: str, language: str = "python") -> None:
        """Parse and display symbols from content."""
        self._current_file = file_path
        self._current_language = language
        self._parse_symbols(content)
        self._update_list()
    
    def refresh(self) -> None:
        """Refresh the symbol list."""
        if self._current_file:
            # This would need to be connected to actual file reading
            pass
    
    def _parse_symbols(self, content: str) -> None:
        """Parse symbols from content based on language."""
        self._symbols = []
        
        if self._current_language == "python":
            self._parse_python_symbols(content)
        elif self._current_language in ("javascript", "typescript"):
            self._parse_js_symbols(content)
        elif self._current_language in ("java", "c", "cpp"):
            self._parse_c_family_symbols(content)
    
    def _parse_python_symbols(self, content: str) -> None:
        """Parse Python symbols."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Classes: class ClassName(...)
            if re.match(r'^class\s+\w+', stripped):
                match = re.match(r'^class\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(1),
                        line=i,
                        symbol_type="class"
                    ))
            
            # Functions: def function_name(...)
            elif re.match(r'^def\s+\w+', stripped):
                match = re.match(r'^def\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(1),
                        line=i,
                        symbol_type="function"
                    ))
            
            # Async functions
            elif re.match(r'^async\s+def\s+\w+', stripped):
                match = re.match(r'^async\s+def\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(1),
                        line=i,
                        symbol_type="function"
                    ))
            
            # Import statements
            elif stripped.startswith('import ') or stripped.startswith('from '):
                self._symbols.append(Symbol(
                    name=stripped[:60] + ("..." if len(stripped) > 60 else ""),
                    line=i,
                    symbol_type="import"
                ))
            
            # Variables (assignment at top level)
            elif re.match(r'^[a-zA-Z_]\w*\s*=', stripped) and not line.startswith(' '):
                match = re.match(r'^([a-zA-Z_]\w*)\s*=', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(1),
                        line=i,
                        symbol_type="variable"
                    ))
    
    def _parse_js_symbols(self, content: str) -> None:
        """Parse JavaScript/TypeScript symbols."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Classes
            if re.match(r'^class\s+\w+', stripped):
                match = re.match(r'^class\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(1),
                        line=i,
                        symbol_type="class"
                    ))
            
            # Functions
            elif re.match(r'^function\s+\w+', stripped):
                match = re.match(r'^function\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(1),
                        line=i,
                        symbol_type="function"
                    ))
            
            # Arrow functions: const name = (...) => ...
            elif re.match(r'^const\s+\w+\s*=\s*', stripped):
                match = re.match(r'^const\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(1),
                        line=i,
                        symbol_type="function"
                    ))
            
            # let/var declarations
            elif re.match(r'^(let|var|const)\s+\w+', stripped):
                match = re.match(r'^(let|var|const)\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(2),
                        line=i,
                        symbol_type="variable"
                    ))
            
            # Imports
            elif stripped.startswith('import '):
                self._symbols.append(Symbol(
                    name=stripped[:60] + ("..." if len(stripped) > 60 else ""),
                    line=i,
                    symbol_type="import"
                ))
    
    def _parse_c_family_symbols(self, content: str) -> None:
        """Parse C/C++/Java symbols."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Classes
            if re.match(r'^(class|struct|interface)\s+\w+', stripped):
                match = re.match(r'^(class|struct|interface)\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(2),
                        line=i,
                        symbol_type="class"
                    ))
            
            # Functions
            elif re.match(r'^\w+\s+\w+\s*\([^)]*\)\s*\{?$', stripped):
                match = re.match(r'^(\w+)\s+(\w+)', stripped)
                if match and match.group(1) not in ('if', 'for', 'while', 'switch', 'return'):
                    self._symbols.append(Symbol(
                        name=match.group(2),
                        line=i,
                        symbol_type="function"
                    ))
            
            # Variables
            elif re.match(r'^(int|char|float|double|void|bool|string|long|short)\s+\w+', stripped):
                match = re.match(r'^(int|char|float|double|void|bool|string|long|short)\s+(\w+)', stripped)
                if match:
                    self._symbols.append(Symbol(
                        name=match.group(2),
                        line=i,
                        symbol_type="variable"
                    ))
    
    def _update_list(self) -> None:
        """Update the symbol list."""
        self._symbol_list.clear()
        
        filter_type = self._filter_combo.currentText()
        
        for symbol in self._symbols:
            # Apply filter
            if filter_type != "All":
                filter_map = {
                    "Functions": "function",
                    "Classes": "class",
                    "Methods": "method",
                    "Variables": "variable",
                    "Imports": "import"
                }
                if filter_map.get(filter_type) != symbol.symbol_type:
                    continue
            
            # Create item
            icon = self._get_icon(symbol.symbol_type)
            item = QListWidgetItem(f"{icon} {symbol.name}  ({symbol.symbol_type})")
            item.setData(Qt.ItemDataRole.UserRole, symbol)
            self._symbol_list.addItem(item)
    
    def _get_icon(self, symbol_type: str) -> str:
        """Get icon for symbol type."""
        icons = {
            "class": "📘",
            "function": "📝",
            "method": "📋",
            "variable": "🔤",
            "import": "📥"
        }
        return icons.get(symbol_type, "•")
    
    def _on_filter_changed(self, text: str) -> None:
        """Handle filter change."""
        self._update_list()
    
    def _on_symbol_clicked(self, item: QListWidgetItem) -> None:
        """Handle symbol click."""
        symbol: Symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            self.symbol_selected.emit(symbol.name, symbol.line)


def show_symbol_outline(parent: Optional[QWidget] = None) -> SymbolOutlinePanel:
    """Create and return a symbol outline panel."""
    return SymbolOutlinePanel(parent)