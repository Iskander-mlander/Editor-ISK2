"""
LSP Hover Module
================
Handles LSP hover information responses.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal


class HoverKind(Enum):
    """Types of hover content."""
    MARKDOWN = auto()
    PLAINTEXT = auto()


@dataclass
class HoverContents:
    """Represents hover content."""
    value: str
    kind: HoverKind
    
    @classmethod
    def from_json(cls, data: Any) -> Optional['HoverContents']:
        """Parse hover contents from JSON."""
        if data is None:
            return None
        
        # Handle string content
        if isinstance(data, str):
            return cls(value=data, kind=HoverKind.PLAINTEXT)
        
        # Handle MarkedString (can be string or object)
        if isinstance(data, dict):
            kind_str = data.get("kind", "plaintext")
            kind = HoverKind.MARKDOWN if kind_str == "markdown" else HoverKind.PLAINTEXT
            value = data.get("value", "")
            return cls(value=value, kind=kind)
        
        return None
    
    @classmethod
    def from_marked_string(cls, data: Any) -> Optional['HoverContents']:
        """Parse MarkedString from JSON."""
        # MarkedString can be:
        # - string
        # - { language: string, value: string }
        if isinstance(data, str):
            return cls(value=data, kind=HoverKind.PLAINTEXT)
        
        if isinstance(data, dict):
            language = data.get("language", "plaintext")
            value = data.get("value", "")
            kind = HoverKind.MARKDOWN if language == "markdown" else HoverKind.PLAINTEXT
            return cls(value=value, kind=kind)
        
        return None


@dataclass 
class Hover:
    """Represents a hover response."""
    contents: Optional[HoverContents] = None
    range: Optional[Dict[str, Any]] = None
    
    @property
    def has_content(self) -> bool:
        """Check if hover has content."""
        return self.contents is not None and bool(self.contents.value)
    
    @property
    def content(self) -> str:
        """Get the hover content string."""
        if self.contents:
            return self.contents.value
        return ""
    
    @classmethod
    def from_json(cls, data: Optional[Dict[str, Any]]) -> Optional['Hover']:
        """Parse hover from JSON."""
        if data is None:
            return None
        
        contents_data = data.get("contents")
        
        # Handle array of MarkedStrings
        if isinstance(contents_data, list) and contents_data:
            # Join multiple MarkedStrings
            parts = []
            for item in contents_data:
                contents = HoverContents.from_marked_string(item)
                if contents:
                    parts.append(contents.value)
            contents_value = "\n\n".join(parts)
            contents = HoverContents(value=contents_value, kind=HoverKind.MARKDOWN)
        else:
            contents = HoverContents.from_json(contents_data)
        
        return cls(
            contents=contents,
            range=data.get("range")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.contents:
            result["contents"] = self.contents.value
        if self.range:
            result["range"] = self.range
        return result


@dataclass
class SignatureInformation:
    """Represents function signature information."""
    label: str
    documentation: str = ""
    parameters: List['ParameterInformation'] = field(default_factory=list)
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional['SignatureInformation']:
        """Parse signature information from JSON."""
        if not data:
            return None
        
        label = data.get("label", "")
        if isinstance(label, list):
            # Can be [start, end] for highlighting
            label = str(label)
        
        documentation = data.get("documentation", "")
        if isinstance(documentation, dict):
            documentation = documentation.get("value", "")
        
        params_data = data.get("parameters", [])
        params = [ParameterInformation.from_json(p) for p in params_data if p]
        
        return cls(
            label=label,
            documentation=documentation,
            parameters=params
        )


@dataclass
class ParameterInformation:
    """Represents parameter information."""
    label: str
    documentation: str = ""
    
    @classmethod
    def from_json(cls, data: Optional[Dict[str, Any]]) -> Optional['ParameterInformation']:
        """Parse parameter information from JSON."""
        if not data:
            return None
        
        label = data.get("label", "")
        if isinstance(label, list):
            label = str(label)
        
        documentation = data.get("documentation", "")
        if isinstance(documentation, dict):
            documentation = documentation.get("value", "")
        
        return cls(label=label, documentation=documentation)


@dataclass
class SignatureHelp:
    """Represents signature help response."""
    signatures: List[SignatureInformation] = field(default_factory=list)
    active_signature: int = 0
    active_parameter: int = 0
    
    @classmethod
    def from_json(cls, data: Optional[Dict[str, Any]]) -> Optional['SignatureHelp']:
        """Parse signature help from JSON."""
        if not data:
            return None
        
        sigs_data = data.get("signatures", [])
        signatures = [SignatureInformation.from_json(s) for s in sigs_data if s]
        
        return cls(
            signatures=signatures,
            active_signature=data.get("activeSignature", 0),
            active_parameter=data.get("activeParameter", 0)
        )
    
    @property
    def current_signature(self) -> Optional[SignatureInformation]:
        """Get the current active signature."""
        if 0 <= self.active_signature < len(self.signatures):
            return self.signatures[self.active_signature]
        return None
    
    def format_signature(self, index: int) -> str:
        """Format a signature for display."""
        if 0 <= index < len(self.signatures):
            sig = self.signatures[index]
            return f"{sig.label}({', '.join(p.label for p in sig.parameters)})"
        return ""


class HoverSignals(QObject):
    """Signals for hover events."""
    hover_ready = pyqtSignal(str)  # content
    hover_cleared = pyqtSignal()
    signature_ready = pyqtSignal(str)  # formatted signature
    signature_cleared = pyqtSignal()


class LSPHover:
    """
    Handles LSP hover and signature help responses.
    """
    
    def __init__(self) -> None:
        self._signals = HoverSignals()
        self._current_hover: Optional[Hover] = None
        self._current_signature: Optional[SignatureHelp] = None
    
    @property
    def signals(self) -> HoverSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def current_hover(self) -> Optional[Hover]:
        """Get current hover information."""
        return self._current_hover
    
    @property
    def current_signature(self) -> Optional[SignatureHelp]:
        """Get current signature help."""
        return self._current_signature
    
    def set_hover(self, data: Optional[Dict[str, Any]]) -> None:
        """Set hover information from LSP response."""
        hover = Hover.from_json(data)
        
        if hover and hover.has_content:
            self._current_hover = hover
            self._signals.hover_ready.emit(hover.content)
        else:
            self.clear_hover()
    
    def clear_hover(self) -> None:
        """Clear hover information."""
        self._current_hover = None
        self._signals.hover_cleared.emit()
    
    def set_signature_help(self, data: Optional[Dict[str, Any]]) -> None:
        """Set signature help from LSP response."""
        signature_help = SignatureHelp.from_json(data)
        
        if signature_help and signature_help.signatures:
            self._current_signature = signature_help
            formatted = signature_help.format_signature(signature_help.active_signature)
            self._signals.signature_ready.emit(formatted)
        else:
            self.clear_signature_help()
    
    def clear_signature_help(self) -> None:
        """Clear signature help."""
        self._current_signature = None
        self._signals.signature_cleared.emit()
    
    def get_formatted_signature(self) -> str:
        """Get the formatted current signature."""
        if self._current_signature:
            return self._current_signature.format_signature(
                self._current_signature.active_signature
            )
        return ""
    
    def select_signature(self, index: int) -> bool:
        """Select a signature by index."""
        if self._current_signature:
            if 0 <= index < len(self._current_signature.signatures):
                self._current_signature.active_signature = index
                formatted = self._current_signature.format_signature(index)
                self._signals.signature_ready.emit(formatted)
                return True
        return False
    
    def select_parameter(self, index: int) -> bool:
        """Select a parameter by index."""
        if self._current_signature:
            self._current_signature.active_parameter = index
            return True
        return False
    
    @property
    def has_hover(self) -> bool:
        """Check if there is hover content."""
        return self._current_hover is not None and self._current_hover.has_content
    
    @property
    def has_signature(self) -> bool:
        """Check if there is signature help."""
        return self._current_signature is not None and bool(self._current_signature.signatures)