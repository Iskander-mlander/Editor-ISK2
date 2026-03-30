"""
Widgets Package
===============
UI widget components.
"""

# Import directly without relative paths
from ui.widgets.file_explorer import FileExplorer
from ui.widgets.terminal import Terminal, DiagnosticsPanel
from ui.widgets.diagnostics_panel import DiagnosticsPanel
from ui.widgets.git_panel import GitPanel
from ui.widgets.navigation_bar import NavigationBar
from ui.widgets.command_palette import CommandPalette
from ui.widgets.find_replace import FindReplacePanel, FindReplaceDialog, show_find_replace
from ui.widgets.snippet_manager import SnippetManagerWidget, SnippetManagerDialog
from ui.widgets.ai_settings import AISettingsWidget, AISettingsDialog
from ui.widgets.ai_panel import AIPanelWidget
from ui.widgets.keyboard_shortcuts import KeyboardShortcutsDialog, show_shortcuts_dialog
from ui.widgets.settings import SettingsDialog
from ui.widgets.welcome_screen import WelcomeScreen, show_welcome_screen
from ui.widgets.search_results import SearchResultsPanel, show_search_results
from ui.widgets.symbol_outline import SymbolOutlinePanel, show_symbol_outline
from ui.widgets.quick_open import QuickOpenDialog, show_quick_open
from ui.widgets.task_list import TaskListPanel, show_task_list
from ui.widgets.diff_viewer import DiffViewer, show_diff_viewer
from ui.widgets.snippets_panel import SnippetsPanel, show_snippets_panel

__all__ = [
    "FileExplorer",
    "Terminal",
    "DiagnosticsPanel",
    "GitPanel",
    "NavigationBar",
    "CommandPalette",
    "FindReplacePanel",
    "FindReplaceDialog",
    "show_find_replace",
    "SnippetManagerWidget",
    "SnippetManagerDialog",
    "AISettingsWidget",
    "AISettingsDialog",
    "AIPanelWidget",
]