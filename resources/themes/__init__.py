"""
Themes Module
=============
Theme management for the editor.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

from PyQt6.QtGui import QColor


@dataclass
class Theme:
    """Represents a theme."""
    name: str
    background: str
    foreground: str
    accent: str
    error: str
    warning: str
    info: str
    keyword: str
    string: str
    number: str
    comment: str
    function: str
    class_name: str
    variable: str
    
    # UI specific
    toolbar_background: str = ""
    panel_background: str = ""
    border: str = ""
    
    @classmethod
    def dark_default(cls) -> 'Theme':
        """Create default dark theme."""
        return cls(
            name="Dark Default",
            background="#1E1E1E",
            foreground="#D4D4D4",
            accent="#007ACC",
            error="#F15350",
            warning="#F5BD48",
            info="#4481D9",
            keyword="#569CD6",
            string="#CE9178",
            number="#B5CEA8",
            comment="#6A9955",
            function="#DCDCAA",
            class_name="#4EC9B0",
            variable="#9CDCFE",
            toolbar_background="#252526",
            panel_background="#252526",
            border="#3C3C3C"
        )
    
    @classmethod
    def light_default(cls) -> 'Theme':
        """Create default light theme."""
        return cls(
            name="Light Default",
            background="#FFFFFF",
            foreground="#000000",
            accent="#0066CC",
            error="#D32F2F",
            warning="#F57C00",
            info="#1976D2",
            keyword="#0000FF",
            string="#A31515",
            number="#098658",
            comment="#008000",
            function="#795E26",
            class_name="#267F99",
            variable="#001080",
            toolbar_background="#F3F3F3",
            panel_background="#F3F3F3",
            border="#E0E0E0"
        )


class ThemeManager:
    """
    Manages editor themes.
    """
    
    def __init__(self) -> None:
        self._themes: Dict[str, Theme] = {}
        self._current_theme: Optional[Theme] = None
        
        # Add default themes
        self._add_default_themes()
    
    def _add_default_themes(self) -> None:
        """Add default themes."""
        self.add_theme(Theme.dark_default())
        self.add_theme(Theme.light_default())
    
    def add_theme(self, theme: Theme) -> None:
        """Add a theme."""
        self._themes[theme.name] = theme
    
    def remove_theme(self, name: str) -> bool:
        """Remove a theme."""
        if name in self._themes:
            del self._themes[name]
            return True
        return False
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """Get a theme by name."""
        return self._themes.get(name)
    
    def set_theme(self, name: str) -> bool:
        """Set the current theme."""
        theme = self._themes.get(name)
        if theme:
            self._current_theme = theme
            return True
        return False
    
    @property
    def current_theme(self) -> Optional[Theme]:
        """Get the current theme."""
        return self._current_theme
    
    @property
    def themes(self) -> List[str]:
        """Get list of theme names."""
        return list(self._themes.keys())