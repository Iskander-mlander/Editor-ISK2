"""
Snippets Feature
================
Code snippet management.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import re
import json
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class TabStop:
    """Represents a tab stop (placeholder) in a snippet."""
    id: int  # Identificador del placeholder (0=final, 1,2,3=orden navegación)
    position: int  # Posición en el texto del snippet
    default: str  # Valor por defecto (lo que está después de `:` en `${1:default}`)
    text: str  # Valor actual (inicialmente igual a default)
    end_position: int  # Posición final del placeholder en el texto


@dataclass
class Snippet:
    """Represents a code snippet."""
    id: str
    name: str
    trigger: str
    content: str
    language: str = "python"
    description: str = ""
    scope: str = ""  # global, file, project
    
    def parse(self) -> List[TabStop]:
        """Parse the snippet content to extract all placeholders.
        
        Returns a list of TabStop objects sorted by ID for navigation.
        The order is: [1, 2, 3, ..., 0] where 0 indicates the end.
        """
        tabstops = []
        # Regex: ${N:default} or ${N}
        pattern = r'\$\{(\d+)(?::([^}]*))?\}'
        
        for match in re.finditer(pattern, self.content):
            tab_id = int(match.group(1))
            default_value = match.group(2) if match.group(2) else ""
            
            tabstop = TabStop(
                id=tab_id,
                position=match.start(),
                default=default_value,
                text=default_value,
                end_position=match.end()
            )
            tabstops.append(tabstop)
        
        # Sort by ID for navigation: [1, 2, 3, ..., 0]
        # Items with ID > 0 sorted ascending, then ID == 0 at the end
        tabstops.sort(key=lambda x: (x.id == 0, x.id if x.id != 0 else float('inf')))
        
        return tabstops


class SnippetManagerSignals(QObject):
    """Signals for snippet manager events."""
    snippet_added = pyqtSignal(str)
    snippet_removed = pyqtSignal(str)
    snippet_updated = pyqtSignal(str)


class SnippetManager(QObject):
    """
    Manages code snippets.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = SnippetManagerSignals()
        self._snippets: Dict[str, Snippet] = {}
        
        # Add default snippets
        self._add_default_snippets()
    
    def _add_default_snippets(self) -> None:
        """Add default snippets."""
        defaults = [
            Snippet(
                id="if_main",
                name="if __name__ == '__main__'",
                trigger="ifmain",
                content="if __name__ == '__main__':\n    ",
                language="python",
                description="Main guard"
            ),
            Snippet(
                id="class",
                name="Class",
                trigger="class",
                content="class ${1:ClassName}:\n    def __init__(self):\n        pass",
                language="python",
                description="Class template"
            ),
            Snippet(
                id="def",
                name="Function",
                trigger="def",
                content="def ${1:function_name}(${2:args}):\n    ${3:pass}",
                language="python",
                description="Function template"
            ),
            Snippet(
                id="for",
                name="For loop",
                trigger="for",
                content="for ${1:item} in ${2:items}:\n    ${3:pass}",
                language="python",
                description="For loop"
            ),
            Snippet(
                id="while",
                name="While loop",
                trigger="while",
                content="while ${1:condition}:\n    ${2:pass}",
                language="python",
                description="While loop"
            ),
            Snippet(
                id="try",
                name="Try except",
                trigger="try",
                content="try:\n    ${1:pass}\nexcept ${2:Exception} as ${3:e}:\n    ${4:pass}",
                language="python",
                description="Try except block"
            ),
        ]
        
        for snippet in defaults:
            self._snippets[snippet.id] = snippet
    
    @property
    def signals(self) -> SnippetManagerSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def snippets(self) -> Dict[str, Snippet]:
        """Get all snippets."""
        return self._snippets
    
    def add_snippet(self, snippet: Snippet) -> bool:
        """Add a snippet."""
        if snippet.id in self._snippets:
            return False
        
        self._snippets[snippet.id] = snippet
        self._signals.snippet_added.emit(snippet.id)
        return True
    
    def remove_snippet(self, snippet_id: str) -> bool:
        """Remove a snippet."""
        if snippet_id not in self._snippets:
            return False
        
        del self._snippets[snippet_id]
        self._signals.snippet_removed.emit(snippet_id)
        return True
    
    def update_snippet(self, snippet: Snippet) -> bool:
        """Update a snippet."""
        if snippet.id not in self._snippets:
            return False
        
        self._snippets[snippet.id] = snippet
        self._signals.snippet_updated.emit(snippet.id)
        return True
    
    def get_snippet(self, snippet_id: str) -> Optional[Snippet]:
        """Get a snippet by ID."""
        return self._snippets.get(snippet_id)
    
    def find_by_trigger(self, trigger: str) -> Optional[Snippet]:
        """Find a snippet by trigger."""
        for snippet in self._snippets.values():
            if snippet.trigger == trigger:
                return snippet
        return None
    
    def get_snippets_by_language(self, language: str) -> List[Snippet]:
        """Get snippets by language."""
        return [s for s in self._snippets.values() if s.language == language]
    
    def expand_snippet(self, trigger: str) -> Optional[str]:
        """Expand a snippet by trigger."""
        snippet = self.find_by_trigger(trigger)
        if snippet:
            return snippet.content
        return None
    
    def load_from_directory(self, directory: str) -> int:
        """Load snippets from a directory of .snippet files.
        
        Returns the number of snippets loaded.
        """
        loaded = 0
        snippet_dir = Path(directory)
        
        if not snippet_dir.exists():
            return 0
        
        # Walk through all .snippet files
        for snippet_file in snippet_dir.rglob("*.snippet"):
            try:
                with open(snippet_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Parse the snippet
                snippet_id = snippet_file.stem
                name = data.get("name", snippet_id)
                trigger = data.get("trigger", "")
                description = data.get("description", "")
                language = data.get("scope", data.get("language", "python"))
                
                # Handle body as array or string
                body = data.get("body", "")
                if isinstance(body, list):
                    content = "\n".join(body)
                else:
                    content = str(body)
                
                # Create snippet
                snippet = Snippet(
                    id=snippet_id,
                    name=name,
                    trigger=trigger,
                    content=content,
                    language=language,
                    description=description
                )
                
                # Add or update
                self._snippets[snippet_id] = snippet
                loaded += 1
                
            except Exception as e:
                print(f"Failed to load snippet {snippet_file}: {e}")
        
        if loaded > 0:
            self._signals.snippet_added.emit("loaded_from_files")
        
        return loaded
    
    def reload(self) -> int:
        """Reload snippets from default directory. Returns count."""
        # Clear existing (except default ones would need tracking)
        self._snippets.clear()
        self._add_default_snippets()
        
        # Load from local snippets directory
        snippets_path = Path(__file__).parent.parent / "resources" / "snippets"
        if not snippets_path.exists():
            # Fallback to Editor-1.3-dev2
            snippets_path = Path("../Editor-1.3-dev2/snippets").resolve()
        
        count = self.load_from_directory(str(snippets_path))
        
        self._signals.snippet_updated.emit("reloaded")
        
        return count + len(self._snippets)  # Include defaults


class SnippetSessionSignals(QObject):
    """Signals for snippet session events."""
    session_started = pyqtSignal()
    session_ended = pyqtSignal()
    tabstop_changed = pyqtSignal(int)  # Emits the new tabstop ID


class SnippetSession(QObject):
    """
    Manages an active snippet editing session with navigation and synchronization.
    
    Handles navigation through placeholders in order [1, 2, 3, ..., 0]
    and synchronizes duplicate placeholders (same ID) in the document.
    """
    
    def __init__(self, snippet: Snippet, start_position: int = 0, parent: Optional[QObject] = None) -> None:
        """
        Initialize a snippet session.
        
        Args:
            snippet: The Snippet object to edit
            start_position: Position in the document where the snippet was inserted
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self._signals = SnippetSessionSignals()
        self._snippet = snippet
        self._start_document_position = start_position
        
        # Parse the snippet to get tabstops
        self._tabstops: List[TabStop] = snippet.parse()
        
        # Navigation state
        self._current_index = 0
        self._is_active = len(self._tabstops) > 0
        
        # Build positions_by_id: maps ID to list of (start, end) positions in snippet content
        self._positions_by_id: Dict[int, List[Tuple[int, int]]] = {}
        for ts in self._tabstops:
            if ts.id not in self._positions_by_id:
                self._positions_by_id[ts.id] = []
            self._positions_by_id[ts.id].append((ts.position, ts.end_position))
        
        if self._is_active:
            self._signals.session_started.emit()
    
    @property
    def signals(self) -> SnippetSessionSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def is_active(self) -> bool:
        """Check if the session is still active."""
        return self._is_active
    
    @property
    def current_index(self) -> int:
        """Get the current navigation index."""
        return self._current_index
    
    @property
    def start_document_position(self) -> int:
        """Get the position in the document where the snippet starts."""
        return self._start_document_position
    
    @property
    def tabstops(self) -> List[TabStop]:
        """Get all tabstops in navigation order."""
        return self._tabstops
    
    @property
    def current_tabstop(self) -> Optional[TabStop]:
        """Get the current tabstop, if any."""
        if 0 <= self._current_index < len(self._tabstops):
            return self._tabstops[self._current_index]
        return None
    
    def next(self) -> Optional[TabStop]:
        """
        Advance to the next placeholder in the sequence.
        
        Navigation order: [1, 2, 3, ..., 0]
        
        Returns:
            The next TabStop, or None when reaching ${0} (end of session)
        """
        if not self._is_active:
            return None
        
        self._current_index += 1
        
        if self._current_index >= len(self._tabstops):
            # Reached the end (${0})
            self._is_active = False
            self._signals.session_ended.emit()
            return None
        
        current_ts = self._tabstops[self._current_index]
        
        # Check if we reached ${0} (end marker)
        if current_ts.id == 0:
            self._is_active = False
            self._signals.session_ended.emit()
            return None
        
        self._signals.tabstop_changed.emit(current_ts.id)
        return current_ts
    
    def previous(self) -> Optional[TabStop]:
        """
        Go back to the previous placeholder.
        
        Returns:
            The previous TabStop, or None if at the beginning
        """
        if not self._is_active or self._current_index <= 0:
            return None
        
        self._current_index -= 1
        current_ts = self._tabstops[self._current_index]
        self._signals.tabstop_changed.emit(current_ts.id)
        return current_ts
    
    def go_to_tabstop(self, tabstop_id: int) -> Optional[TabStop]:
        """
        Navigate directly to a specific placeholder by ID.
        
        Args:
            tabstop_id: The ID of the tabstop to go to
            
        Returns:
            The TabStop with that ID, or None if not found
        """
        # Find the index of the tabstop with this ID
        for i, ts in enumerate(self._tabstops):
            if ts.id == tabstop_id:
                self._current_index = i
                self._is_active = True
                self._signals.tabstop_changed.emit(tabstop_id)
                return ts
        
        return None
    
    def update_tabstop(self, tabstop_id: int, new_text: str, editor) -> List[Tuple[int, int]]:
        """
        Update the text of a placeholder and synchronize all duplicates.
        
        When a placeholder with a specific ID appears multiple times in the snippet,
        this method updates ALL occurrences in the document.
        
        Args:
            tabstop_id: The ID of the placeholder to update
            new_text: The new text value
            editor: The QPlainTextEdit editor instance (required for document updates)
            
        Returns:
            List of (start, end) positions in document coordinates that were updated
        """
        if tabstop_id not in self._positions_by_id:
            return []
        
        # Update local tabstop text
        for ts in self._tabstops:
            if ts.id == tabstop_id:
                ts.text = new_text
                break
        
        # Calculate positions in the document and update them
        # We need to update from end to start to avoid position shifting issues
        updated_positions: List[Tuple[int, int]] = []
        
        # Get positions sorted by document position (descending for reverse update)
        positions = sorted(
            [
                (self._start_document_position + start, self._start_document_position + end)
                for start, end in self._positions_by_id[tabstop_id]
            ],
            key=lambda x: x[0],
            reverse=True
        )
        
        # Update in reverse order to avoid position shifting
        for doc_start, doc_end in positions:
            # Update in the document
            cursor = editor.textCursor()
            cursor.setPosition(doc_start)
            cursor.setPosition(doc_end, cursor.MoveMode.KeepAnchor)
            cursor.insertText(new_text)
            
            updated_positions.append((doc_start, doc_start + len(new_text)))
        
        # Reverse to return in document order
        updated_positions.reverse()
        
        return updated_positions
    
    def get_tabstop_positions_in_document(self, tabstop_id: int) -> List[Tuple[int, int]]:
        """
        Get the positions of all occurrences of a tabstop in the document.
        
        Args:
            tabstop_id: The ID to look up
            
        Returns:
            List of (start, end) positions in document coordinates
        """
        if tabstop_id not in self._positions_by_id:
            return []
        
        return [
            (self._start_document_position + start, self._start_document_position + end)
            for start, end in self._positions_by_id[tabstop_id]
        ]
    
    def reset(self) -> None:
        """Reset the session to the beginning."""
        self._current_index = 0
        self._is_active = len(self._tabstops) > 0
        
        # Reset all tabstop texts to defaults
        for ts in self._tabstops:
            ts.text = ts.default
        
        if self._is_active:
            self._signals.session_started.emit()
    
    def end(self) -> None:
        """End the session manually."""
        self._is_active = False
        self._signals.session_ended.emit()