"""
LSP Completions Module
=====================
Handles LSP completion responses and formatting.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal


class CompletionItemKind(Enum):
    """LSP CompletionItem kinds."""
    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18
    FOLDER = 19
    CONSTANT = 20
    ENUM_MEMBER = 21
    STRUCT = 22
    EVENT = 23
    OPERATOR = 24
    TYPE_PARAMETER = 25


@dataclass
class LSPCompletionItem:
    """Represents an LSP completion item."""
    label: str
    kind: Optional[CompletionItemKind] = None
    detail: str = ""
    documentation: str = ""
    insert_text: str = ""
    filter_text: str = ""
    sort_text: str = ""
    text_edit: Optional[Dict[str, Any]] = None
    additional_text_edit: Optional[Dict[str, Any]] = None
    commit_characters: List[str] = field(default_factory=list)
    command: Optional[Dict[str, Any]] = None
    
    def to_local_item(self) -> 'LocalCompletionItem':
        """Convert to local completion item format."""
        from core.editor.completion_provider import CompletionItem, CompletionKind
        
        # Map LSP kind to local kind
        kind_map = {
            CompletionItemKind.TEXT: CompletionKind.TEXT,
            CompletionItemKind.METHOD: CompletionKind.METHOD,
            CompletionItemKind.FUNCTION: CompletionKind.FUNCTION,
            CompletionItemKind.CONSTRUCTOR: CompletionKind.CONSTRUCTOR,
            CompletionItemKind.FIELD: CompletionKind.FIELD,
            CompletionItemKind.VARIABLE: CompletionKind.VARIABLE,
            CompletionItemKind.CLASS: CompletionKind.CLASS,
            CompletionItemKind.INTERFACE: CompletionKind.INTERFACE,
            CompletionItemKind.MODULE: CompletionKind.MODULE,
            CompletionItemKind.PROPERTY: CompletionKind.PROPERTY,
            CompletionItemKind.KEYWORD: CompletionKind.KEYWORD,
            CompletionItemKind.SNIPPET: CompletionKind.SNIPPET,
            CompletionItemKind.FILE: CompletionKind.FILE,
            CompletionItemKind.CONSTANT: CompletionKind.VALUE,
            CompletionItemKind.ENUM: CompletionKind.ENUM,
            CompletionItemKind.TYPE_PARAMETER: CompletionKind.CLASS,
        }
        
        return CompletionItem(
            label=self.label,
            kind=kind_map.get(self.kind, CompletionKind.TEXT),
            detail=self.detail,
            documentation=self.documentation,
            insert_text=self.insert_text or self.label,
            filter_text=self.filter_text or self.label
        )


@dataclass 
class CompletionList:
    """Represents an LSP completion list."""
    is_incomplete: bool = False
    items: List[LSPCompletionItem] = field(default_factory=list)
    
    @classmethod
    def from_json(cls, data: Optional[Dict[str, Any]]) -> Optional['CompletionList']:
        """Parse completion list from JSON."""
        if data is None:
            return None
        
        # Handle both CompletionList and array of items
        if isinstance(data, list):
            items = [cls._parse_item(item) for item in data]
            return cls(items=items)
        
        is_incomplete = data.get("isIncomplete", False)
        items_data = data.get("items", [])
        items = [cls._parse_item(item) for item in items_data]
        
        return cls(is_incomplete=is_incomplete, items=items)
    
    @staticmethod
    def _parse_item(item: Dict[str, Any]) -> LSPCompletionItem:
        """Parse a single completion item."""
        kind_value = item.get("kind")
        kind = CompletionItemKind(kind_value) if kind_value else None
        
        return LSPCompletionItem(
            label=item.get("label", ""),
            kind=kind,
            detail=item.get("detail", ""),
            documentation=item.get("documentation", ""),
            insert_text=item.get("insertText", ""),
            filter_text=item.get("filterText", ""),
            sort_text=item.get("sortText", ""),
            text_edit=item.get("textEdit"),
            additional_text_edit=item.get("additionalTextEdits"),
            commit_characters=item.get("commitCharacters", []),
            command=item.get("command")
        )


class CompletionsSignals(QObject):
    """Signals for completions events."""
    completions_ready = pyqtSignal(list)  # list of CompletionItem
    completion_selected = pyqtSignal(str)  # insert_text
    completion_cancelled = pyqtSignal()


class LSPCompletions:
    """
    Handles LSP completion responses.
    """
    
    def __init__(self) -> None:
        self._signals = CompletionsSignals()
        self._completions: List[LSPCompletionItem] = []
        self._is_incomplete: bool = False
    
    @property
    def signals(self) -> CompletionsSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def completions(self) -> List[LSPCompletionItem]:
        """Get current completions."""
        return self._completions
    
    @property
    def is_incomplete(self) -> bool:
        """Check if completion list is incomplete."""
        return self._is_incomplete
    
    def set_completions(self, data: Optional[Dict[str, Any]]) -> None:
        """Set completions from LSP response."""
        completion_list = CompletionList.from_json(data)
        
        if completion_list:
            self._completions = completion_list.items
            self._is_incomplete = completion_list.is_incomplete
        else:
            self._completions = []
            self._is_incomplete = False
        
        # Emit local completion items
        local_items = [item.to_local_item() for item in self._completions]
        self._signals.completions_ready.emit(local_items)
    
    def clear_completions(self) -> None:
        """Clear completions."""
        self._completions = []
        self._is_incomplete = False
        self._signals.completion_cancelled.emit()
    
    def select_completion(self, index: int) -> Optional[str]:
        """Select a completion by index."""
        if 0 <= index < len(self._completions):
            item = self._completions[index]
            self._signals.completion_selected.emit(item.insert_text or item.label)
            return item.insert_text or item.label
        return None
    
    def get_item(self, index: int) -> Optional[LSPCompletionItem]:
        """Get a completion item by index."""
        if 0 <= index < len(self._completions):
            return self._completions[index]
        return None
    
    def get_local_items(self) -> List[Any]:
        """Get all completions as local items."""
        return [item.to_local_item() for item in self._completions]