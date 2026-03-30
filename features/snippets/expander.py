"""
Snippet Expander Module
=======================
Handles automatic snippet expansion on trigger detection.
"""

import re
from dataclasses import dataclass
from typing import Optional, Dict, List, Callable

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QTextCursor


class SnippetTriggerSignals(QObject):
    """Signals for snippet trigger events."""
    trigger_detected = pyqtSignal(str)  # trigger word
    snippet_expanded = pyqtSignal(str, str)  # trigger, content
    expansion_cancelled = pyqtSignal()


@dataclass
class ExpansionCandidate:
    """Represents a potential snippet expansion."""
    trigger: str
    start_position: int
    end_position: int
    snippet_text: str


class SnippetExpander(QObject):
    """
    Manages automatic snippet expansion based on trigger detection.
    Detects when user types a trigger word and expands the snippet.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = SnippetTriggerSignals()
        self._editor: Optional[QPlainTextEdit] = None
        self._snippet_manager = None
        
        # Debounce timer for trigger detection
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._check_trigger)
        
        # Settings
        self._debounce_ms = 100
        self._min_trigger_length = 2
        self._enabled = True
        
        # Current candidate
        self._current_candidate: Optional[ExpansionCandidate] = None
    
    @property
    def signals(self) -> SnippetTriggerSignals:
        """Get trigger signals."""
        return self._signals
    
    @property
    def is_enabled(self) -> bool:
        """Check if expansion is enabled."""
        return self._enabled
    
    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        """Set expansion enabled state."""
        self._enabled = value
    
    def set_snippet_manager(self, manager) -> None:
        """Set the snippet manager."""
        self._snippet_manager = manager
    
    def set_editor(self, editor: QPlainTextEdit) -> None:
        """Set the editor to monitor."""
        if self._editor:
            self._editor.textChanged.disconnect(self._on_text_changed)
        
        self._editor = editor
        
        if editor:
            editor.textChanged.connect(self._on_text_changed)
    
    def set_debounce_time(self, ms: int) -> None:
        """Set debounce time in milliseconds."""
        self._debounce_ms = max(50, min(500, ms))
        self._debounce_timer.setInterval(self._debounce_ms)
    
    def _on_text_changed(self) -> None:
        """Handle text changes in the editor."""
        if not self._enabled or not self._snippet_manager:
            return
        
        # Restart debounce timer
        self._debounce_timer.start()
    
    def _check_trigger(self) -> None:
        """Check if current word is a trigger."""
        if not self._editor or not self._snippet_manager:
            return
        
        # Get cursor position
        cursor = self._editor.textCursor()
        text_before = cursor.block().text()[:cursor.positionInBlock()]
        
        if not text_before:
            return
        
        # Find the word before cursor (potential trigger)
        # Match word characters (alphanumeric + underscore)
        match = re.search(r'(\w+)$', text_before)
        
        if not match:
            return
        
        trigger_word = match.group(1)
        
        # Check minimum length
        if len(trigger_word) < self._min_trigger_length:
            return
        
        # Look up trigger in snippet manager
        snippet = self._snippet_manager.find_by_trigger(trigger_word)
        
        if snippet:
            # Found a match!
            self._signals.trigger_detected.emit(trigger_word)
            
            # Calculate positions
            block_start = cursor.block().position()
            trigger_start = block_start + match.start()
            trigger_end = block_start + match.end()
            
            self._current_candidate = ExpansionCandidate(
                trigger=trigger_word,
                start_position=trigger_start,
                end_position=trigger_end,
                snippet_text=snippet.content
            )
            
            # Expand the snippet
            self._expand_snippet(self._current_candidate)
    
    def _expand_snippet(self, candidate: ExpansionCandidate) -> None:
        """Expand a snippet at the given position."""
        if not self._editor:
            return
        
        cursor = self._editor.textCursor()
        
        # Select the trigger word
        cursor.setPosition(candidate.start_position)
        cursor.setPosition(candidate.end_position, QTextCursor.MoveMode.KeepAnchor)
        
        # Replace with snippet content
        cursor.insertText(candidate.snippet_text)
        
        # Emit signal
        self._signals.snippet_expanded.emit(candidate.trigger, candidate.snippet_text)
        
        # Parse and navigate to first tabstop
        self._setup_tabstop_navigation(candidate.snippet_text)
    
    def _setup_tabstop_navigation(self, content: str) -> None:
        """Setup navigation through tabstops in the snippet."""
        # Find all tabstops ${1}, ${2}, etc.
        tabstops = re.findall(r'\$\{(\d+)(?::([^}]*))?\}', content)
        
        if not tabstops:
            return
        
        # Move cursor to first tabstop (after ${1:)
        # This is a simplified implementation
        # Full implementation would create a SnippetSession
        
        # For now, select the first placeholder text
        if tabstops[0][1]:  # Has default text
            # Find the position of first tabstop and select its content
            pattern = r'\$\{1:' + re.escape(tabstops[0][1]) + r'\}'
            match = re.search(pattern, content)
            
            if match:
                # Calculate actual position in editor
                cursor = self._editor.textCursor()
                cursor.setPosition(cursor.position() - len(content) + match.start())
                cursor.setPosition(cursor.position() + len(tabstops[0][1]), QTextCursor.MoveMode.KeepAnchor)
                self._editor.setTextCursor(cursor)
    
    def expand_manually(self, trigger: str) -> bool:
        """Manually expand a snippet by trigger."""
        if not self._snippet_manager:
            return False
        
        snippet = self._snippet_manager.find_by_trigger(trigger)
        
        if snippet:
            if not self._editor:
                return False
            
            cursor = self._editor.textCursor()
            
            # Find trigger word at cursor
            text_before = cursor.block().text()[:cursor.positionInBlock()]
            match = re.search(r'(\w+)$', text_before)
            
            if match and match.group(1) == trigger:
                # Found trigger at cursor, expand it
                candidate = ExpansionCandidate(
                    trigger=trigger,
                    start_position=cursor.block().position() + match.start(),
                    end_position=cursor.block().position() + match.end(),
                    snippet_text=snippet.content
                )
                self._expand_snippet(candidate)
                return True
            
            # Trigger not at cursor, insert at cursor position
            cursor.insertText(snippet.content)
            self._signals.snippet_expanded.emit(trigger, snippet.content)
            return True
        
        return False
    
    def cancel_expansion(self) -> None:
        """Cancel the current expansion candidate."""
        self._current_candidate = None
        self._debounce_timer.stop()
        self._signals.explansion_cancelled.emit()
    
    def get_available_triggers(self) -> List[str]:
        """Get list of available trigger words."""
        if not self._snippet_manager:
            return []
        
        return [s.trigger for s in self._snippet_manager.snippets.values()]
    
    def get_trigger_suggestions(self, prefix: str) -> List[str]:
        """Get trigger suggestions that match a prefix."""
        if not self._snippet_manager:
            return []
        
        suggestions = []
        for snippet in self._snippet_manager.snippets.values():
            if snippet.trigger.startswith(prefix):
                suggestions.append(snippet.trigger)
        
        return suggestions[:10]  # Limit to 10 suggestions


class SnippetCompletionProvider(QObject):
    """
    Provides snippet suggestions as completions.
    Works with the editor's completion system.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._snippet_manager = None
        self._editor: Optional[QPlainTextEdit] = None
    
    def set_snippet_manager(self, manager) -> None:
        """Set the snippet manager."""
        self._snippet_manager = manager
    
    def set_editor(self, editor: QPlainTextEdit) -> None:
        """Set the editor."""
        self._editor = editor
    
    def get_completions(self, prefix: str) -> List[Dict[str, str]]:
        """Get completion suggestions for prefix."""
        if not self._snippet_manager:
            return []
        
        completions = []
        
        for snippet in self._snippet_manager.snippets.values():
            if snippet.trigger.startswith(prefix):
                completions.append({
                    'text': snippet.trigger,
                    'display': f"{snippet.name} ({snippet.trigger})",
                    'detail': snippet.description,
                    'snippet': snippet.content
                })
        
        return completions[:10]
    
    def is_snippet_trigger(self, text: str) -> bool:
        """Check if text is a known snippet trigger."""
        if not self._snippet_manager:
            return False
        
        return self._snippet_manager.find_by_trigger(text) is not None