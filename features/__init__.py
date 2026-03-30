"""
Features Package
================
Internal features (plugins) for the editor.
"""

# AI Assistant
from .ai_assistant import AIAssistant, AIChatMessage

# Debugging
from .debugging import Debugger, DebugSession

# Git
from .git import GitClient, GitFileStatus, GitCommit, GitBranch

# Snippets
from .snippets import Snippet, SnippetManager, TabStop, SnippetSession

# Refactoring
from .refactoring import CodeFormatter, CodeActions

__all__ = [
    "AIAssistant",
    "AIChatMessage",
    "Debugger",
    "DebugSession",
    "GitClient",
    "GitFileStatus",
    "GitCommit",
    "GitBranch",
    "Snippet",
    "SnippetManager",
    "TabStop",
    "SnippetSession",
    "CodeFormatter",
    "CodeActions",
]