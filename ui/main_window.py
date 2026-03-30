"""
Main Window Module
==================
Main application window with signal-based component communication.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

from PyQt6.QtCore import pyqtSignal, Qt, QSize, QTimer, QObject
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QToolBar, QStatusBar, QMenuBar, QMenu, QDockWidget, QSplitter, QStackedWidget, QLabel, QToolButton

from core.editor import CodeEditor, SyntaxHighlighter, CompletionProvider, BracketMatcher
from core.lsp import LSPClient, LSPCompletions, LSPDiagnostics, LSPHover
from core.linting import LintingManager
from core.editor.auto_save import AutoSaveManager
from core.editor.project_manager import ProjectManager
from core.utils import Config, ConfigManager, icon_manager
from core.utils.file_type_detector import get_detector
from core.utils.emmet import EmmetEngine
from features.refactoring import CodeFormatter
from plugins import PluginManager
from ui.widgets import (FileExplorer, Terminal, DiagnosticsPanel, GitPanel, NavigationBar, CommandPalette, AIPanelWidget, WelcomeScreen, SymbolOutlinePanel, TaskListPanel, SnippetsPanel)
from ui.widgets.split_editor import SplitEditorManager


class MainWindowSignals(QObject):
    """Signals for main window events."""
    file_opened = pyqtSignal(str)
    file_saved = pyqtSignal(str)
    file_closed = pyqtSignal(str)
    editor_changed = pyqtSignal(int)  # tab index
    theme_changed = pyqtSignal(str)
    config_changed = pyqtSignal(str, object)


@dataclass
class EditorTab:
    """Represents an open editor tab."""
    file_path: Optional[str]
    editor: CodeEditor
    highlighter: SyntaxHighlighter
    is_modified: bool = False
    language: str = "python"


class MainWindow(QMainWindow):
    """
    Main application window.
    Uses signals for dependency injection between components.
    """
    
    # Signals
    file_opened = pyqtSignal(str)
    file_saved = pyqtSignal(str)
    file_closed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._signals = MainWindowSignals()
        
        # Core components (using signals for DI)
        self._config: Optional[Config] = None
        self._config_manager: ConfigManager = ConfigManager()
        
        # Editor components
        self._lsp_client: Optional[LSPClient] = None
        self._lsp_completions: Optional[LSPCompletions] = None
        self._lsp_diagnostics: Optional[LSPDiagnostics] = None
        self._lsp_hover: Optional[LSPHover] = None
        
        # Linting
        self._linting_manager: Optional[LintingManager] = None
        
        # Plugin Manager
        self._plugin_manager: Optional[PluginManager] = None
        
        # Snippet manager
        self._snippet_manager: Optional[Any] = None
        
        # UI components
        self._tab_widget: Optional[QTabWidget] = None
        self._file_explorer: Optional[FileExplorer] = None
        self._terminal: Optional[Terminal] = None
        self._diagnostics_panel: Optional[DiagnosticsPanel] = None
        self._ai_panel: Optional[AIPanelWidget] = None
        self._git_panel: Optional[GitPanel] = None
        self._navigation_bar: Optional[NavigationBar] = None
        self._command_palette: Optional[CommandPalette] = None
        
        # Dock widgets for toggling
        self._explorer_dock: Optional[QDockWidget] = None
        self._terminal_dock: Optional[QDockWidget] = None
        self._diagnostics_dock: Optional[QDockWidget] = None
        self._ai_panel_dock: Optional[QDockWidget] = None
        self._git_dock: Optional[QDockWidget] = None
        
        # State
        self._open_tabs: List[EditorTab] = []
        self._current_tab_index: int = -1
        
        # Initialize components (loads config)
        self._init_components()
        
        # Setup UI (creates menus, etc.)
        self._setup_ui()
        
        # Apply saved theme after UI is set up (editors may already exist)
        if self._config and self._config.theme.name:
            self._apply_saved_theme()
        
        # Apply saved UI font size
        self._apply_saved_font_size()
        
        # Load saved explorer path
        self._load_explorer_path()
        
        # Connect signals
        self._connect_signals()
        
        # Show welcome screen if no tabs open
        if not self._open_tabs:
            self._welcome_screen.show()
            self._tab_widget.hide()
        else:
            self._tab_widget.show()
        
        # Translate UI after menus are created
        self._translate_ui(self._config.app.language if self._config else "es")
    
    @property
    def signals(self) -> MainWindowSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def config(self) -> Optional[Config]:
        """Get the configuration."""
        return self._config
    
    @property
    def lsp_client(self) -> Optional[LSPClient]:
        """Get the LSP client."""
        return self._lsp_client
    
    @property
    def current_editor(self) -> Optional[CodeEditor]:
        """Get the current editor."""
        if 0 <= self._current_tab_index < len(self._open_tabs):
            return self._open_tabs[self._current_tab_index].editor
        return None
    
    def _get_current_editor_file(self) -> Optional[str]:
        """Get the file path of the current editor tab."""
        if 0 <= self._current_tab_index < len(self._open_tabs):
            return self._open_tabs[self._current_tab_index].file_path
        return None
    
    def _init_components(self) -> None:
        """Initialize core components."""
        # Load configuration
        self._config = self._config_manager.load()
        
        # Initialize translations based on saved language
        self._load_translations(self._config.app.language)
        
        # Initialize LSP components
        self._lsp_client = LSPClient()
        self._lsp_completions = LSPCompletions()
        self._lsp_diagnostics = LSPDiagnostics()
        self._lsp_hover = LSPHover()
        
        # Initialize Linting
        self._linting_manager = LintingManager()
        
        # Initialize Auto-Save
        self._auto_save_manager = AutoSaveManager(self)
        
        # Initialize Emmet Engine
        self._emmet_engine = EmmetEngine()
        
        # Initialize Project Manager
        self._project_manager = ProjectManager(self)
        
        # Initialize Plugin Manager
        self._plugin_manager = PluginManager()
        self._plugin_manager.add_plugin_path(Path("plugins"))
        
        # Discover and load plugins
        discovered = self._plugin_manager.discover_plugins()
        for plugin_id in discovered:
            self._plugin_manager.load_plugin(plugin_id)
        
        # Initialize Welcome Screen
        self._welcome_screen = WelcomeScreen(self)
        self._welcome_screen.file_opened.connect(self._open_file)
        self._welcome_screen.new_file_requested.connect(self._on_new_file)
        self._welcome_screen.open_folder_requested.connect(self._on_open_folder)
        
        # Initialize Code Formatter
        self._code_formatter = CodeFormatter()
        
        # Initialize Split Editor Manager
        self._split_manager: Optional[SplitEditorManager] = None
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Editor ISK - 2.0")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create navigation bar
        self._navigation_bar = NavigationBar()
        main_layout.addWidget(self._navigation_bar)
        
        # Create tab widget for editors
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self._tab_widget)
        
        # Add welcome screen (shown when no tabs are open)
        main_layout.addWidget(self._welcome_screen)
        self._welcome_screen.hide()
        
        # Create status bar
        self._create_status_bar()
        
        # Create menus
        self._create_menus()
        
        # Create toolbars
        self._create_toolbars()
        
        # Create dock widgets
        self._create_dock_widgets()
        
        # Load UI state from previous session
        self._load_ui_state()
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Cursor position (Line:Column)
        self._cursor_position_label = QLabel("Ln 1, Col 1")
        self._cursor_position_label.setMinimumWidth(100)
        status_bar.addWidget(self._cursor_position_label)
        
        # Encoding
        self._encoding_label = QLabel("UTF-8")
        self._encoding_label.setMinimumWidth(60)
        status_bar.addWidget(self._encoding_label)
        
        # Line endings
        self._line_ending_label = QLabel("LF")
        self._line_ending_label.setMinimumWidth(40)
        status_bar.addWidget(self._line_ending_label)
        
        # File type/language
        self._language_label = QLabel("Plain Text")
        self._language_label.setMinimumWidth(80)
        status_bar.addWidget(self._language_label)
        
        # Tab size
        self._tab_size_label = QLabel("Spaces: 4")
        self._tab_size_label.setMinimumWidth(80)
        status_bar.addWidget(self._tab_size_label)
        
        # Spacer
        status_bar.addWidget(QWidget())
        
        # Modified indicator
        self._modified_label = QLabel("")
        self._modified_label.setMinimumWidth(20)
        status_bar.addWidget(self._modified_label)
    
    def _create_menus(self) -> None:
        """Create the menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        from core.utils import icon_manager
        file_menu = menu_bar.addMenu("&File")
        
        new_action = QAction(icon_manager.get_icon("new", 16), "&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction(icon_manager.get_icon("open", 16), "&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)
        
        # Recent files submenu
        self._recent_files_menu = file_menu.addMenu(icon_manager.get_icon("clock", 16), "Recent &Files")
        self._update_recent_files_menu()
        
        save_action = QAction(icon_manager.get_icon("save", 16), "&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction(icon_manager.get_icon("save_as", 16), "Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_action = QAction(icon_manager.get_icon("close", 16), "&Close", self)
        close_action.setShortcut(QKeySequence.StandardKey.Close)
        close_action.triggered.connect(self._on_close_file)
        file_menu.addAction(close_action)
        
        close_all_action = QAction(icon_manager.get_icon("close_all", 16), "Close &All", self)
        close_all_action.setShortcut(QKeySequence("Ctrl+Shift+W"))
        close_all_action.triggered.connect(self._on_close_all)
        file_menu.addAction(close_all_action)
        
        file_menu.addSeparator()
        
        open_folder_action = QAction(icon_manager.get_icon("open_folder", 16), "Open F&older...", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_folder_action.triggered.connect(self._on_open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        open_project_action = QAction(icon_manager.get_icon("project", 16), "&Open Project...", self)
        open_project_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        open_project_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(icon_manager.get_icon("exit", 16), "E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        undo_action = QAction(icon_manager.get_icon("undo", 16), "&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction(icon_manager.get_icon("redo", 16), "&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction(icon_manager.get_icon("cut", 16), "Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self._on_cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction(icon_manager.get_icon("copy", 16), "&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._on_copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction(icon_manager.get_icon("paste", 16), "&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._on_paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction(icon_manager.get_icon("find", 16), "&Find...", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self._on_find)
        edit_menu.addAction(find_action)
        
        replace_action = QAction(icon_manager.get_icon("replace", 16), "&Replace...", self)
        replace_action.setShortcut(QKeySequence.StandardKey.Replace)
        replace_action.triggered.connect(self._on_replace)
        edit_menu.addAction(replace_action)
        
        find_in_files_action = QAction(icon_manager.get_icon("find_in_files", 16), "Find in &Files...", self)
        find_in_files_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        find_in_files_action.triggered.connect(self._on_find_in_files)
        edit_menu.addAction(find_in_files_action)
        
        goto_line_action = QAction(icon_manager.get_icon("goto_line", 16), "&Go to Line...", self)
        goto_line_action.setShortcut(QKeySequence("Ctrl+G"))
        goto_line_action.triggered.connect(self._on_goto_line)
        edit_menu.addAction(goto_line_action)
        
        goto_symbol_action = QAction(icon_manager.get_icon("goto_symbol", 16), "Go to &Symbol...", self)
        goto_symbol_action.setShortcut(QKeySequence("Ctrl+R"))
        goto_symbol_action.triggered.connect(self._on_goto_symbol)
        edit_menu.addAction(goto_symbol_action)
        
        quick_open_action = QAction(icon_manager.get_icon("quick_open", 16), "&Quick Open...", self)
        quick_open_action.setShortcut(QKeySequence("Ctrl+P"))
        quick_open_action.triggered.connect(self._on_quick_open)
        edit_menu.addAction(quick_open_action)
        
        edit_menu.addSeparator()
        
        select_all_action = QAction(icon_manager.get_icon("select_all", 16), "Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self._on_select_all)
        edit_menu.addAction(select_all_action)
        
        edit_menu.addSeparator()
        
        move_line_up_action = QAction(icon_manager.get_icon("move_up", 16), "Move Line &Up", self)
        move_line_up_action.setShortcut(QKeySequence("Alt+Up"))
        move_line_up_action.triggered.connect(self._on_move_line_up)
        edit_menu.addAction(move_line_up_action)
        
        move_line_down_action = QAction(icon_manager.get_icon("move_down", 16), "Move Line &Down", self)
        move_line_down_action.setShortcut(QKeySequence("Alt+Down"))
        move_line_down_action.triggered.connect(self._on_move_line_down)
        edit_menu.addAction(move_line_down_action)
        
        copy_line_up_action = QAction(icon_manager.get_icon("copy", 16), "Copy Line &Up", self)
        copy_line_up_action.setShortcut(QKeySequence("Shift+Alt+Up"))
        copy_line_up_action.triggered.connect(self._on_copy_line_up)
        edit_menu.addAction(copy_line_up_action)
        
        copy_line_down_action = QAction(icon_manager.get_icon("copy", 16), "Copy Line &Down", self)
        copy_line_down_action.setShortcut(QKeySequence("Shift+Alt+Down"))
        copy_line_down_action.triggered.connect(self._on_copy_line_down)
        edit_menu.addAction(copy_line_down_action)
        
        delete_line_action = QAction(icon_manager.get_icon("delete_line", 16), "&Delete Line", self)
        delete_line_action.setShortcut(QKeySequence("Ctrl+Shift+K"))
        delete_line_action.triggered.connect(self._on_delete_line)
        edit_menu.addAction(delete_line_action)
        
        edit_menu.addSeparator()
        
        toggle_comment_action = QAction(icon_manager.get_icon("comment", 16), "Toggle &Comment", self)
        toggle_comment_action.setShortcut(QKeySequence("Ctrl+/"))
        toggle_comment_action.triggered.connect(self._on_toggle_comment)
        edit_menu.addAction(toggle_comment_action)
        
        indent_action = QAction(icon_manager.get_icon("indent", 16), "&Indent", self)
        indent_action.setShortcut(QKeySequence("Ctrl+]"))
        indent_action.triggered.connect(self._on_indent)
        edit_menu.addAction(indent_action)
        
        unindent_action = QAction(icon_manager.get_icon("unindent", 16), "&Unindent", self)
        unindent_action.setShortcut(QKeySequence("Ctrl+["))
        unindent_action.triggered.connect(self._on_unindent)
        edit_menu.addAction(unindent_action)
        
        edit_menu.addSeparator()
        
        expand_emmet_action = QAction(icon_manager.get_icon("emmet", 16), "&Expand Emmet Abbreviation", self)
        expand_emmet_action.setShortcut(QKeySequence("Ctrl+E"))
        expand_emmet_action.triggered.connect(self._on_expand_emmet)
        edit_menu.addAction(expand_emmet_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        self._toggle_explorer_action = QAction(icon_manager.get_icon("explorer", 16), "&File Explorer", self)
        self._toggle_explorer_action.setCheckable(True)
        self._toggle_explorer_action.setChecked(True)
        self._toggle_explorer_action.triggered.connect(self._on_toggle_explorer)
        view_menu.addAction(self._toggle_explorer_action)
        
        self._toggle_terminal_action = QAction(icon_manager.get_icon("terminal", 16), "&Terminal", self)
        self._toggle_terminal_action.setCheckable(True)
        self._toggle_terminal_action.setChecked(True)
        self._toggle_terminal_action.triggered.connect(self._on_toggle_terminal)
        view_menu.addAction(self._toggle_terminal_action)
        
        self._toggle_diagnostics_action = QAction(icon_manager.get_icon("problems", 16), "&Problems", self)
        self._toggle_diagnostics_action.setCheckable(True)
        self._toggle_diagnostics_action.setChecked(True)
        self._toggle_diagnostics_action.triggered.connect(self._on_toggle_diagnostics)
        view_menu.addAction(self._toggle_diagnostics_action)
        
        self._toggle_ai_panel_action = QAction(icon_manager.get_icon("ai", 16), "&AI Panel", self)
        self._toggle_ai_panel_action.setCheckable(True)
        self._toggle_ai_panel_action.setChecked(False)
        self._toggle_ai_panel_action.triggered.connect(self._on_toggle_ai_panel)
        view_menu.addAction(self._toggle_ai_panel_action)
        
        self._toggle_git_action = QAction(icon_manager.get_icon("git", 16), "&Git Panel", self)
        self._toggle_git_action.setCheckable(True)
        self._toggle_git_action.setChecked(True)
        self._toggle_git_action.triggered.connect(self._on_toggle_git)
        view_menu.addAction(self._toggle_git_action)
        
        view_menu.addSeparator()
        
        self._toggle_minimap_action = QAction(icon_manager.get_icon("minimap", 16), "&Minimap", self)
        self._toggle_minimap_action.setCheckable(True)
        self._toggle_minimap_action.setChecked(True)
        self._toggle_minimap_action.triggered.connect(self._on_toggle_minimap)
        view_menu.addAction(self._toggle_minimap_action)
        
        self._toggle_navbar_action = QAction(icon_manager.get_icon("navbar", 16), "&Navigation Bar", self)
        self._toggle_navbar_action.setCheckable(True)
        self._toggle_navbar_action.setChecked(True)
        self._toggle_navbar_action.triggered.connect(self._on_toggle_navbar)
        view_menu.addAction(self._toggle_navbar_action)
        
        self._toggle_outline_action = QAction(icon_manager.get_icon("outline", 16), "&Outline", self)
        self._toggle_outline_action.setCheckable(True)
        self._toggle_outline_action.setChecked(True)
        self._toggle_outline_action.triggered.connect(self._on_toggle_outline)
        view_menu.addAction(self._toggle_outline_action)
        
        self._toggle_tasks_action = QAction(icon_manager.get_icon("check", 16), "&Tasks", self)
        self._toggle_tasks_action.setCheckable(True)
        self._toggle_tasks_action.setChecked(True)
        self._toggle_tasks_action.triggered.connect(self._on_toggle_tasks)
        view_menu.addAction(self._toggle_tasks_action)
        
        self._toggle_snippets_action = QAction(icon_manager.get_icon("code", 16), "&Snippets", self)
        self._toggle_snippets_action.setCheckable(True)
        self._toggle_snippets_action.setChecked(True)
        self._toggle_snippets_action.triggered.connect(self._on_toggle_snippets)
        view_menu.addAction(self._toggle_snippets_action)
        
        view_menu.addSeparator()
        
        fold_all_action = QAction(icon_manager.get_icon("fold", 16), "&Fold All", self)
        fold_all_action.setShortcut(QKeySequence("Ctrl+Shift+["))
        fold_all_action.triggered.connect(self._on_fold_all)
        view_menu.addAction(fold_all_action)
        
        unfold_all_action = QAction(icon_manager.get_icon("unfold", 16), "&Unfold All", self)
        unfold_all_action.setShortcut(QKeySequence("Ctrl+Shift+]"))
        unfold_all_action.triggered.connect(self._on_unfold_all)
        view_menu.addAction(unfold_all_action)
        
        view_menu.addSeparator()
        
        zoom_in_action = QAction(icon_manager.get_icon("zoom_in", 16), "Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._on_zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction(icon_manager.get_icon("zoom_out", 16), "Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._on_zoom_out)
        view_menu.addAction(zoom_out_action)
        
        zoom_reset_action = QAction(icon_manager.get_icon("zoom_reset", 16), "&Reset Zoom", self)
        zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_action.triggered.connect(self._on_zoom_reset)
        view_menu.addAction(zoom_reset_action)
        
        view_menu.addSeparator()
        
        diff_viewer_action = QAction(icon_manager.get_icon("compare", 16), "&Compare Files...", self)
        diff_viewer_action.setShortcut(QKeySequence("Ctrl+K, Ctrl+D"))
        diff_viewer_action.triggered.connect(self._on_show_diff_viewer)
        view_menu.addAction(diff_viewer_action)
        
        # Run menu
        run_menu = menu_bar.addMenu("&Run")
        
        run_action = QAction(icon_manager.get_icon("run_file", 16), "&Run File", self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.triggered.connect(self._on_run_file)
        run_menu.addAction(run_action)
        
        stop_action = QAction(icon_manager.get_icon("stop_execution", 16), "&Stop Execution", self)
        stop_action.setShortcut(QKeySequence("Shift+F5"))
        stop_action.triggered.connect(self._on_stop_execution)
        run_menu.addAction(stop_action)
        
        # Git menu
        git_menu = menu_bar.addMenu("&Git")
        
        git_refresh_action = QAction(icon_manager.get_icon("git_refresh", 16), "&Refresh", self)
        git_refresh_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        git_refresh_action.triggered.connect(self._on_git_refresh)
        git_menu.addAction(git_refresh_action)
        
        git_menu.addSeparator()
        
        git_commit_action = QAction(icon_manager.get_icon("git_commit", 16), "&Commit...", self)
        git_commit_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        git_commit_action.triggered.connect(self._on_git_commit)
        git_menu.addAction(git_commit_action)
        
        git_pull_action = QAction(icon_manager.get_icon("git_pull", 16), "&Pull", self)
        git_pull_action.triggered.connect(self._on_git_pull)
        git_menu.addAction(git_pull_action)
        
        git_push_action = QAction(icon_manager.get_icon("git_push", 16), "&Push", self)
        git_push_action.triggered.connect(self._on_git_push)
        git_menu.addAction(git_push_action)
        
        git_menu.addSeparator()
        
        git_branch_action = QAction(icon_manager.get_icon("git_branch", 16), "&Branch...", self)
        git_branch_action.triggered.connect(self._on_git_branch)
        git_menu.addAction(git_branch_action)
        
        git_menu.addSeparator()
        
        toggle_git = QAction(icon_manager.get_icon("git", 16), "&Git Panel", self)
        toggle_git.setCheckable(True)
        toggle_git.setChecked(True)
        toggle_git.triggered.connect(self._on_toggle_git)
        git_menu.addAction(toggle_git)
        self._toggle_git_action = toggle_git
        
        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        
        command_palette_action = QAction(icon_manager.get_icon("command_palette", 16), "&Command Palette...", self)
        command_palette_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        command_palette_action.triggered.connect(self._on_show_command_palette)
        tools_menu.addAction(command_palette_action)
        
        quick_command_action = QAction(icon_manager.get_icon("quick_command", 16), "&Quick Command...", self)
        quick_command_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        quick_command_action.triggered.connect(self._on_show_quick_command)
        tools_menu.addAction(quick_command_action)
        
        tools_menu.addSeparator()
        
        lint_settings_action = QAction(icon_manager.get_icon("linter", 16), "&Linter Settings...", self)
        lint_settings_action.triggered.connect(self._on_lint_settings)
        tools_menu.addAction(lint_settings_action)
        
        plugin_manager_action = QAction(icon_manager.get_icon("plugin", 16), "&Plugin Manager...", self)
        plugin_manager_action.triggered.connect(self._on_plugin_manager)
        tools_menu.addAction(plugin_manager_action)
        
        keyboard_shortcuts_action = QAction(icon_manager.get_icon("keyboard", 16), "&Keyboard Shortcuts...", self)
        keyboard_shortcuts_action.setShortcut(QKeySequence("Ctrl+K, Ctrl+S"))
        keyboard_shortcuts_action.triggered.connect(self._on_keyboard_shortcuts)
        tools_menu.addAction(keyboard_shortcuts_action)
        
        tools_menu.addSeparator()
        
        format_code_action = QAction(icon_manager.get_icon("format", 16), "&Format Code", self)
        format_code_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        format_code_action.triggered.connect(self._on_format_code)
        tools_menu.addAction(format_code_action)
        
        # Preferences menu
        prefs_menu = menu_bar.addMenu("&Preferences")
        
        # Themes submenu
        themes_submenu = QMenu("&Themes", self)
        themes_submenu.setIcon(icon_manager.get_icon("themes", 16))
        for theme_name in self._config.get_available_themes() if self._config else ["Default Dark"]:
            theme_action = QAction(theme_name, self)
            theme_action.triggered.connect(lambda checked, t=theme_name: self._on_change_theme(t))
            themes_submenu.addAction(theme_action)
        prefs_menu.addMenu(themes_submenu)
        
        # Snippets - Direct access to manage snippets
        manage_snippets_action = QAction(icon_manager.get_icon("snippets", 16), "&Manage Snippets...", self)
        manage_snippets_action.triggered.connect(self._on_manage_snippets)
        prefs_menu.addAction(manage_snippets_action)
        
        # AI Settings - Direct access
        ai_settings_action = QAction(icon_manager.get_icon("ai_settings", 16), "&AI Settings...", self)
        ai_settings_action.triggered.connect(self._on_ai_settings)
        prefs_menu.addAction(ai_settings_action)
        
        prefs_menu.addSeparator()
        
        # Editor Settings
        editor_settings_action = QAction(icon_manager.get_icon("editor_settings", 16), "&Editor Settings...", self)
        editor_settings_action.triggered.connect(self._on_editor_settings)
        prefs_menu.addAction(editor_settings_action)
        
        vim_mode_action = QAction(icon_manager.get_icon("vim_mode", 16), "&Vim Mode", self)
        vim_mode_action.setCheckable(True)
        vim_mode_action.setChecked(False)
        vim_mode_action.triggered.connect(self._on_toggle_vim_mode)
        prefs_menu.addAction(vim_mode_action)
        self._vim_mode_action = vim_mode_action
        
        prefs_menu.addSeparator()
        
        # Language submenu
        language_submenu = QMenu("&Language", self)
        language_submenu.setIcon(icon_manager.get_icon("language", 16))
        
        self._language_actions = {}
        for lang_code, lang_name in [("es", "Español"), ("en", "English")]:
            action = QAction(lang_name, self)
            action.setCheckable(True)
            action.setChecked(self._config.app.language == lang_code if self._config else lang_code == "es")
            action.triggered.connect(lambda checked, c=lang_code: self._on_change_language(c))
            language_submenu.addAction(action)
            self._language_actions[lang_code] = action
        
        prefs_menu.addMenu(language_submenu)
        
        prefs_menu.addSeparator()
        
        # UI Font Size submenu
        font_size_submenu = QMenu("&Font Size", self)
        font_size_submenu.setIcon(icon_manager.get_icon("font", 16))
        
        increase_font_action = QAction(icon_manager.get_icon("zoom_in", 16), "Increase", self)
        increase_font_action.setShortcut(QKeySequence("Ctrl+Plus"))
        increase_font_action.triggered.connect(self._on_increase_font_size)
        font_size_submenu.addAction(increase_font_action)
        
        decrease_font_action = QAction(icon_manager.get_icon("zoom_out", 16), "Decrease", self)
        decrease_font_action.setShortcut(QKeySequence("Ctrl+Minus"))
        decrease_font_action.triggered.connect(self._on_decrease_font_size)
        font_size_submenu.addAction(decrease_font_action)
        
        reset_font_action = QAction(icon_manager.get_icon("zoom_reset", 16), "Reset to Default", self)
        reset_font_action.triggered.connect(self._on_reset_font_size)
        font_size_submenu.addAction(reset_font_action)
        
        prefs_menu.addMenu(font_size_submenu)
        
        # View menu additions - add after toggle_outline
        toggle_line_numbers = QAction(icon_manager.get_icon("format", 16), "&Line Numbers", self)
        toggle_line_numbers.setCheckable(True)
        toggle_line_numbers.setChecked(True)
        toggle_line_numbers.triggered.connect(self._on_toggle_line_numbers)
        view_menu.addAction(toggle_line_numbers)
        self._toggle_line_numbers_action = toggle_line_numbers
        
        toggle_word_wrap = QAction(icon_manager.get_icon("text", 16), "&Word Wrap", self)
        toggle_word_wrap.setCheckable(True)
        toggle_word_wrap.setChecked(False)
        toggle_word_wrap.triggered.connect(self._on_toggle_word_wrap)
        view_menu.addAction(toggle_word_wrap)
        self._toggle_word_wrap_action = toggle_word_wrap
        
        view_menu.addSeparator()
        
        split_horizontal = QAction(icon_manager.get_icon("split_horizontal", 16), "Split &Horizontal", self)
        split_horizontal.setShortcut(QKeySequence("Ctrl+\\"))
        split_horizontal.triggered.connect(self._on_split_horizontal)
        view_menu.addAction(split_horizontal)
        
        split_vertical = QAction(icon_manager.get_icon("split_vertical", 16), "Split &Vertical", self)
        split_vertical.setShortcut(QKeySequence("Ctrl+Shift+\\"))
        split_vertical.triggered.connect(self._on_split_vertical)
        view_menu.addAction(split_vertical)
        
        close_split = QAction(icon_manager.get_icon("close_split", 16), "&Close Split", self)
        close_split.setShortcut(QKeySequence("Ctrl+Shift+W"))
        close_split.triggered.connect(self._on_close_split)
        view_menu.addAction(close_split)
        
        focus_next = QAction(icon_manager.get_icon("next_split", 16), "Focus &Next Split", self)
        focus_next.setShortcut(QKeySequence("Ctrl+Alt+Right"))
        focus_next.triggered.connect(self._on_focus_next_split)
        view_menu.addAction(focus_next)
        
        focus_prev = QAction(icon_manager.get_icon("prev_split", 16), "Focus &Previous Split", self)
        focus_prev.setShortcut(QKeySequence("Ctrl+Alt+Left"))
        focus_prev.triggered.connect(self._on_focus_previous_split)
        view_menu.addAction(focus_prev)
        
        # Help menu (last position)
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction(icon_manager.get_icon("about", 16), "&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _create_toolbars(self) -> None:
        """Create toolbars with IDE-style groups."""
        from core.utils.icon_manager import IconManager
        icon_manager_instance = IconManager()
        
        def create_toolbar_action(icon_name: str, tooltip: str, callback) -> QAction:
            action = QAction(icon_manager_instance.get_icon(icon_name, 20), "", self)
            action.setToolTip(tooltip)
            action.triggered.connect(callback)
            return action
        
        # File toolbar
        file_toolbar = QToolBar("Archivo")
        file_toolbar.setObjectName("FileToolbar")
        file_toolbar.setIconSize(QSize(18, 18))
        file_toolbar.setMovable(True)
        file_toolbar.setFloatable(True)
        file_toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        
        self._action_new = create_toolbar_action("new", "Nuevo archivo (Ctrl+N)", self._on_new_file)
        self._action_open = create_toolbar_action("open", "Abrir archivo (Ctrl+O)", self._on_open_file)
        self._action_open_folder = create_toolbar_action("open_folder", "Abrir carpeta", self._on_open_folder)
        self._action_save = create_toolbar_action("save", "Guardar (Ctrl+S)", self._on_save_file)
        self._action_save_as = create_toolbar_action("save_as", "Guardar como...", self._on_save_as)
        self._action_save_all = create_toolbar_action("save_all", "Guardar todo", self._on_save_all)
        self._action_close = create_toolbar_action("close", "Cerrar archivo", lambda: self._close_tab(self._current_tab_index) if self._current_tab_index >= 0 else None)
        
        file_toolbar.addAction(self._action_new)
        file_toolbar.addAction(self._action_open)
        file_toolbar.addAction(self._action_open_folder)
        file_toolbar.addSeparator()
        file_toolbar.addAction(self._action_save)
        file_toolbar.addAction(self._action_save_as)
        file_toolbar.addAction(self._action_save_all)
        file_toolbar.addSeparator()
        file_toolbar.addAction(self._action_close)
        
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, file_toolbar)
        self._file_toolbar = file_toolbar
        
        # Edit toolbar
        edit_toolbar = QToolBar("Editar")
        edit_toolbar.setObjectName("EditToolbar")
        edit_toolbar.setIconSize(QSize(18, 18))
        edit_toolbar.setMovable(True)
        edit_toolbar.setFloatable(True)
        edit_toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        
        self._action_undo = create_toolbar_action("undo", "Deshacer (Ctrl+Z)", self._on_undo)
        self._action_redo = create_toolbar_action("redo", "Rehacer (Ctrl+Y)", self._on_redo)
        self._action_cut = create_toolbar_action("cut", "Cortar (Ctrl+X)", self._on_cut)
        self._action_copy = create_toolbar_action("copy", "Copiar (Ctrl+C)", self._on_copy)
        self._action_paste = create_toolbar_action("paste", "Pegar (Ctrl+V)", self._on_paste)
        self._action_find = create_toolbar_action("find", "Buscar (Ctrl+F)", self._on_find)
        self._action_replace = create_toolbar_action("replace", "Reemplazar (Ctrl+H)", self._on_replace)
        
        edit_toolbar.addAction(self._action_undo)
        edit_toolbar.addAction(self._action_redo)
        edit_toolbar.addSeparator()
        edit_toolbar.addAction(self._action_cut)
        edit_toolbar.addAction(self._action_copy)
        edit_toolbar.addAction(self._action_paste)
        edit_toolbar.addSeparator()
        edit_toolbar.addAction(self._action_find)
        edit_toolbar.addAction(self._action_replace)
        
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, edit_toolbar)
        self._edit_toolbar = edit_toolbar
        
        # Search toolbar
        search_toolbar = QToolBar("Buscar")
        search_toolbar.setObjectName("SearchToolbar")
        search_toolbar.setIconSize(QSize(18, 18))
        search_toolbar.setMovable(True)
        search_toolbar.setFloatable(True)
        search_toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        
        self._action_find_in_files = create_toolbar_action("find_in_files", "Buscar en archivos", self._on_find_in_files)
        self._action_goto_line = create_toolbar_action("goto_line", "Ir a línea (Ctrl+G)", self._on_goto_line)
        self._action_goto_symbol = create_toolbar_action("goto_symbol", "Ir a símbolo", self._on_goto_symbol)
        
        search_toolbar.addAction(self._action_find_in_files)
        search_toolbar.addAction(self._action_goto_line)
        search_toolbar.addAction(self._action_goto_symbol)
        
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, search_toolbar)
        self._search_toolbar = search_toolbar
        
        # View toolbar
        view_toolbar = QToolBar("Ver")
        view_toolbar.setObjectName("ViewToolbar")
        view_toolbar.setIconSize(QSize(18, 18))
        view_toolbar.setMovable(True)
        view_toolbar.setFloatable(True)
        view_toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        
        self._action_toggle_sidebar = create_toolbar_action("toggle_sidebar", "Mostrar/ocultar barra lateral", self._on_toggle_sidebar)
        self._action_toggle_explorer = create_toolbar_action("explorer", "Explorador de archivos", self._on_toggle_explorer)
        self._action_toggle_terminal = create_toolbar_action("terminal", "Terminal", self._on_toggle_terminal)
        self._action_toggle_problems = create_toolbar_action("problems", "Problemas", self._on_toggle_diagnostics)
        self._action_toggle_minimap = create_toolbar_action("minimap", "Minimapa", self._on_toggle_minimap)
        self._action_toggle_word_wrap = create_toolbar_action("word_wrap", "Ajuste de línea", self._on_toggle_word_wrap)
        self._action_fullscreen = create_toolbar_action("fullscreen", "Pantalla completa (F11)", self._on_toggle_fullscreen)
        
        view_toolbar.addAction(self._action_toggle_sidebar)
        view_toolbar.addAction(self._action_toggle_explorer)
        view_toolbar.addAction(self._action_toggle_terminal)
        view_toolbar.addAction(self._action_toggle_problems)
        view_toolbar.addSeparator()
        view_toolbar.addAction(self._action_toggle_minimap)
        view_toolbar.addAction(self._action_toggle_word_wrap)
        view_toolbar.addSeparator()
        view_toolbar.addAction(self._action_fullscreen)
        
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, view_toolbar)
        self._view_toolbar = view_toolbar
        
        # Run toolbar
        run_toolbar = QToolBar("Ejecutar")
        run_toolbar.setObjectName("RunToolbar")
        run_toolbar.setIconSize(QSize(18, 18))
        run_toolbar.setMovable(True)
        run_toolbar.setFloatable(True)
        run_toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        
        self._action_run = create_toolbar_action("run", "Ejecutar (F5)", self._on_run_file)
        self._action_run_debug = create_toolbar_action("debug", "Depurar (F6)", self._on_debug_file)
        self._action_stop = create_toolbar_action("stop", "Detener (Shift+F5)", self._on_stop_execution)
        self._action_build = create_toolbar_action("build", "Compilar", self._on_build_project)
        
        run_toolbar.addAction(self._action_run)
        run_toolbar.addAction(self._action_run_debug)
        run_toolbar.addAction(self._action_stop)
        run_toolbar.addSeparator()
        run_toolbar.addAction(self._action_build)
        
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, run_toolbar)
        self._run_toolbar = run_toolbar
        
        # Code toolbar
        code_toolbar = QToolBar("Código")
        code_toolbar.setObjectName("CodeToolbar")
        code_toolbar.setIconSize(QSize(18, 18))
        code_toolbar.setMovable(True)
        code_toolbar.setFloatable(True)
        code_toolbar.setAllowedAreas(Qt.ToolBarArea.AllToolBarAreas)
        
        self._action_toggle_comment = create_toolbar_action("toggle_comment", "Comentar/descomentar línea", self._on_toggle_comment)
        self._action_indent = create_toolbar_action("indent_selection", "Aumentar sangría", self._on_indent_selection)
        self._action_outdent = create_toolbar_action("outdent_selection", "Reducir sangría", self._on_outdent_selection)
        self._action_format_code = create_toolbar_action("format_code", "Formatear código", self._on_format_code)
        self._action_duplicate_line = create_toolbar_action("duplicate", "Duplicar línea", self._on_duplicate_line)
        self._action_move_line_up = create_toolbar_action("move_line_up", "Mover línea arriba", self._on_move_line_up)
        self._action_move_line_down = create_toolbar_action("move_line_down", "Mover línea abajo", self._on_move_line_down)
        self._action_delete_line = create_toolbar_action("delete_line", "Eliminar línea", self._on_delete_line)
        
        code_toolbar.addAction(self._action_toggle_comment)
        code_toolbar.addAction(self._action_indent)
        code_toolbar.addAction(self._action_outdent)
        code_toolbar.addAction(self._action_format_code)
        code_toolbar.addSeparator()
        code_toolbar.addAction(self._action_duplicate_line)
        code_toolbar.addAction(self._action_move_line_up)
        code_toolbar.addAction(self._action_move_line_down)
        code_toolbar.addAction(self._action_delete_line)
        
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, code_toolbar)
        self._code_toolbar = code_toolbar
        
        # Store all toolbars for customization
        self._toolbars = {
            'file': file_toolbar,
            'edit': edit_toolbar,
            'search': search_toolbar,
            'view': view_toolbar,
            'run': run_toolbar,
            'code': code_toolbar,
        }
    
    def _create_dock_widgets(self) -> None:
        """Create dock widgets."""
        from core.utils import icon_manager
        
        # File explorer - allow moving
        self._file_explorer = FileExplorer()
        explorer_dock = QDockWidget("Explorer", self)
        explorer_dock.setObjectName("ExplorerDock")
        explorer_dock.setWidget(self._file_explorer)
        explorer_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._apply_dock_border(explorer_dock)
        explorer_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, explorer_dock)
        self._explorer_dock = explorer_dock
        explorer_dock.visibilityChanged.connect(lambda v: self._toggle_explorer_action.setChecked(v))
        
        # Add close button to explorer dock
        explorer_dock.setTitleBarWidget(self._create_dock_title_bar(
            "Explorer", "folder", explorer_dock
        ))
        
        # Terminal - allow moving
        self._terminal = Terminal()
        
        # Set callback to get current file from main window
        self._terminal.set_get_current_file_callback(self._get_current_editor_file)
        
        terminal_dock = QDockWidget("Terminal", self)
        terminal_dock.setObjectName("TerminalDock")
        terminal_dock.setWidget(self._terminal)
        terminal_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._apply_dock_border(terminal_dock)
        terminal_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, terminal_dock)
        self._terminal_dock = terminal_dock
        terminal_dock.visibilityChanged.connect(lambda v: self._toggle_terminal_action.setChecked(v))
        
        # Add close button to terminal dock
        terminal_dock.setTitleBarWidget(self._create_dock_title_bar(
            "Terminal", "terminal", terminal_dock
        ))
        
        # Diagnostics panel - allow moving
        self._diagnostics_panel = DiagnosticsPanel()
        diagnostics_dock = QDockWidget("Problems", self)
        diagnostics_dock.setObjectName("ProblemsDock")
        diagnostics_dock.setWidget(self._diagnostics_panel)
        diagnostics_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._apply_dock_border(diagnostics_dock)
        diagnostics_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, diagnostics_dock)
        self._diagnostics_dock = diagnostics_dock
        diagnostics_dock.visibilityChanged.connect(lambda v: self._toggle_diagnostics_action.setChecked(v))
        
        # Add close button to diagnostics dock
        diagnostics_dock.setTitleBarWidget(self._create_dock_title_bar(
            "Problems", "problems", diagnostics_dock
        ))
        
        # Git panel - allow moving
        self._git_panel = GitPanel()
        git_dock = QDockWidget("Git", self)
        git_dock.setObjectName("GitDock")
        git_dock.setWidget(self._git_panel)
        git_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._apply_dock_border(git_dock)
        git_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, git_dock)
        self._git_dock = git_dock
        git_dock.visibilityChanged.connect(lambda v: self._toggle_git_action.setChecked(v))
        
        # Add close button to git dock
        git_dock.setTitleBarWidget(self._create_dock_title_bar(
            "Git", "git", git_dock
        ))
        
        # Symbol outline panel - allow moving
        self._symbol_outline = SymbolOutlinePanel()
        outline_dock = QDockWidget("Outline", self)
        outline_dock.setObjectName("OutlineDock")
        outline_dock.setWidget(self._symbol_outline)
        outline_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._apply_dock_border(outline_dock)
        outline_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, outline_dock)
        self._outline_dock = outline_dock
        outline_dock.visibilityChanged.connect(lambda v: self._toggle_outline_action.setChecked(v))
        
        # Connect symbol selection to go to line
        self._symbol_outline.symbol_selected.connect(self._on_symbol_selected)
        
        # Add close button to outline dock
        outline_dock.setTitleBarWidget(self._create_dock_title_bar(
            "Outline", "function", outline_dock
        ))
        
        # Task list panel
        self._task_list_panel = TaskListPanel()
        task_dock = QDockWidget("Tasks", self)
        task_dock.setObjectName("TasksDock")
        task_dock.setWidget(self._task_list_panel)
        task_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._apply_dock_border(task_dock)
        task_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, task_dock)
        self._task_dock = task_dock
        task_dock.visibilityChanged.connect(lambda v: self._toggle_tasks_action.setChecked(v))
        
        # Connect task click to open file
        self._task_list_panel.task_clicked.connect(self._on_task_clicked)
        
        task_dock.setTitleBarWidget(self._create_dock_title_bar(
            "Tasks", "check", task_dock
        ))
        
        # Snippets panel
        self._snippets_panel = SnippetsPanel()
        snippets_dock = QDockWidget("Snippets", self)
        snippets_dock.setObjectName("SnippetsDock")
        snippets_dock.setWidget(self._snippets_panel)
        snippets_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self._apply_dock_border(snippets_dock)
        snippets_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, snippets_dock)
        self._snippets_dock = snippets_dock
        snippets_dock.visibilityChanged.connect(lambda v: self._toggle_snippets_action.setChecked(v))
        
        # Connect snippet selection to insert
        self._snippets_panel.snippet_selected.connect(self._on_snippet_insert)
        
        snippets_dock.setTitleBarWidget(self._create_dock_title_bar(
            "Snippets", "code", snippets_dock
        ))
    
    def _apply_dock_border(self, dock: QDockWidget) -> None:
        """Apply a border style to a dock widget."""
        border_style = """
            QDockWidget {
                border: 1px solid #444444;
            }
            QDockWidget::title {
                border-bottom: 1px solid #444444;
            }
        """
        dock.setStyleSheet(border_style)
    
    def _create_dock_title_bar(self, title: str, icon_name: str, dock: QDockWidget) -> QWidget:
        """Create a custom title bar for dock widgets with icon and close button."""
        from core.utils import icon_manager
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Get theme colors
        bg_color = "#2d2d2d"
        fg_color = "#d4d4d4"
        border_color = "#007acc"
        
        if self._config and self._config.theme.name:
            from core.editor import SyntaxHighlighter
            temp = SyntaxHighlighter()
            temp.set_theme_by_name(self._config.theme.name)
            theme = temp.theme
            bg_color = theme.background.name()
            fg_color = theme.normal.name()
        
        default_style = f"""
            QWidget {{
                background-color: {bg_color};
                color: {fg_color};
                border: none;
            }}
            QLabel {{
                background-color: transparent;
                color: {fg_color};
                font-weight: bold;
            }}
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 3px;
            }}
            QToolButton:hover {{
                background-color: {fg_color};
                color: {bg_color};
            }}
        """
        
        hover_style = f"""
            QWidget {{
                background-color: {bg_color};
                color: {fg_color};
                border: 2px solid {border_color};
            }}
            QLabel {{
                background-color: transparent;
                color: {fg_color};
                font-weight: bold;
            }}
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 3px;
            }}
            QToolButton:hover {{
                background-color: {fg_color};
                color: {bg_color};
            }}
        """
        
        widget.setStyleSheet(default_style)
        
        def on_enter(event):
            widget.setStyleSheet(hover_style)
            widget.update()
        
        def on_leave(event):
            widget.setStyleSheet(default_style)
            widget.update()
        
        widget.enterEvent = on_enter
        widget.leaveEvent = on_leave
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(icon_manager.get_icon(icon_name, 16).pixmap(16, 16))
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        
        # Spacer
        layout.addStretch()
        
        # Close button
        close_btn = QToolButton()
        close_btn.setIcon(icon_manager.get_icon("close", 16))
        close_btn.setToolTip("Close")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(dock.hide)
        layout.addWidget(close_btn)
        
        return widget
    
    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Connect config signals
        if self._config:
            self._config.signals.editor_config_changed.connect(self._on_editor_config_changed)
        
        # Connect LSP signals
        if self._lsp_client:
            self._lsp_client.signals.diagnostics_received.connect(
                self._on_diagnostics_received
            )
            self._lsp_client.signals.completion_received.connect(
                self._on_completion_received
            )
            self._lsp_client.signals.hover_received.connect(
                self._on_hover_received
            )
        
        # Connect file explorer
        if self._file_explorer:
            self._file_explorer.file_selected.connect(self._on_file_selected)
            self._file_explorer.directory_changed.connect(self._on_directory_changed)
        
        # Connect terminal execution errors to diagnostics
        if self._terminal:
            self._terminal.execution_error.connect(self._on_terminal_error)
            self._terminal.execution_finished.connect(self._on_terminal_finished)
            self._terminal.output_received.connect(self._on_terminal_output)
    
    def _on_directory_changed(self, path: str) -> None:
        """Handle directory change from file explorer."""
        if self._git_panel:
            self._git_panel.open_repository(path)
        if self._task_list_panel:
            self._task_list_panel.set_root_path(path)
    
    # Event handlers
    
    def _on_new_file(self) -> None:
        """Create a new file."""
        self._welcome_screen.hide()
        self._tab_widget.show()
        self._create_new_tab(None)
    
    def _on_open_file(self) -> None:
        """Open a file."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Python Files (*.py);;All Files (*)"
        )
        
        if file_path:
            self._open_file(file_path)
    
    def _on_save_file(self) -> None:
        """Save the current file."""
        if self._current_tab_index >= 0:
            tab = self._open_tabs[self._current_tab_index]
            if tab.file_path:
                self._save_file(tab.file_path)
            else:
                self._on_save_as()
    
    def _on_save_as(self) -> None:
        """Save the current file with a new name."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            "",
            "Python Files (*.py);;All Files (*)"
        )
        
        if file_path:
            self._save_file(file_path)
    
    def _on_close_file(self) -> None:
        """Close the current file."""
        if self._current_tab_index >= 0:
            self._close_tab(self._current_tab_index)
    
    def _on_close_all(self) -> None:
        """Close all open files."""
        while self._open_tabs:
            self._close_tab(0)
    
    def _on_open_folder(self) -> None:
        """Open a folder."""
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder and self._file_explorer:
            self._file_explorer.set_root_path(folder)
    
    def _on_open_project(self) -> None:
        """Open a project."""
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Open Project")
        if folder:
            project = self._project_manager.open_project(folder)
            if project and self._file_explorer:
                self._file_explorer.set_root_path(folder)
    
    def _on_tab_close_requested(self, index: int) -> None:
        """Handle tab close request."""
        self._close_tab(index)
    
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        self._current_tab_index = index
        self._signals.editor_changed.emit(index)
        self._update_status_bar()
        
        # Update terminal with active file
        if self._terminal:
            if index >= 0 and index < len(self._open_tabs):
                file_path = self._open_tabs[index].file_path
                self._terminal.set_active_file(file_path)
            else:
                self._terminal.set_active_file(None)
        
        # Update symbol outline when tab changes
        if index >= 0:
            self._update_symbol_outline()
        
        # Update task list with current file's directory
        if index >= 0 and index < len(self._open_tabs) and hasattr(self, '_task_list_panel'):
            file_path = self._open_tabs[index].file_path
            if file_path:
                self._task_list_panel.set_current_file(file_path)
        
        # Show/hide welcome screen and tab widget based on open tabs
        if index < 0:
            self._welcome_screen.show()
            self._tab_widget.hide()
        else:
            self._welcome_screen.hide()
            self._tab_widget.show()
    
    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection from explorer."""
        self._open_file(file_path)
    
    def _update_recent_files_menu(self) -> None:
        """Update the recent files menu with current list."""
        self._recent_files_menu.clear()
        
        if self._config:
            recent_files = self._config.get_recent_files()
            if not recent_files:
                # Add placeholder when no recent files
                no_recent = QAction("No Recent Files", self)
                no_recent.setEnabled(False)
                self._recent_files_menu.addAction(no_recent)
            else:
                for file_path in recent_files:
                    from pathlib import Path
                    filename = Path(file_path).name
                    action = QAction(filename, self)
                    action.setToolTip(file_path)
                    action.triggered.connect(lambda checked, p=file_path: self._open_file(p))
                    self._recent_files_menu.addAction(action)
                
                # Add separator and clear option
                self._recent_files_menu.addSeparator()
                clear_action = QAction(icon_manager.get_icon("trash", 16), "Clear Recent Files", self)
                clear_action.triggered.connect(self._clear_recent_files)
                self._recent_files_menu.addAction(clear_action)
    
    def _clear_recent_files(self) -> None:
        """Clear the recent files list."""
        if self._config:
            self._config.clear_recent_files()
            self._update_recent_files_menu()
            from core.utils.config import ConfigManager
            ConfigManager().save(self._config)
    
    def _on_diagnostics_received(self, uri: str, diagnostics: List[Dict]) -> None:
        """Handle diagnostics received from LSP."""
        if self._lsp_diagnostics:
            self._lsp_diagnostics.set_diagnostics(uri, diagnostics)
            if self._diagnostics_panel:
                self._diagnostics_panel.set_diagnostics(diagnostics)
    
    def _on_completion_received(self, items: List[Dict]) -> None:
        """Handle completion received from LSP."""
        if self._lsp_completions:
            self._lsp_completions.set_completions({"items": items})
    
    def _on_hover_received(self, hover_data: Dict) -> None:
        """Handle hover received from LSP."""
        if self._lsp_hover:
            self._lsp_hover.set_hover(hover_data)
    
    def _on_terminal_error(self, error_msg: str) -> None:
        """Handle terminal execution error."""
        # Add error to diagnostics panel
        if self._diagnostics_panel:
            self._diagnostics_panel.set_diagnostics([{
                "message": f"Runtime Error: {error_msg}",
                "severity": 1,  # Error
                "source": "Terminal"
            }])
    
    def _on_terminal_output(self, output: str) -> None:
        """Handle terminal output - display in diagnostics panel."""
        if not output:
            return
        
        # Add output to diagnostics panel as info
        lines = output.strip().split('\n')
        diagnostics = []
        
        for line in lines[:50]:  # Limit to 50 lines
            if line.strip():
                diagnostics.append({
                    "message": line,
                    "severity": 3,  # Info
                    "source": "Terminal"
                })
        
        if diagnostics and self._diagnostics_panel:
            self._diagnostics_panel.set_diagnostics(diagnostics)
    
    def _on_terminal_finished(self, exit_code: int) -> None:
        """Handle terminal execution finished."""
        # Update diagnostics panel on non-zero exit
        if exit_code != 0 and self._diagnostics_panel:
            self._diagnostics_panel.set_diagnostics([{
                "message": f"Execution finished with exit code {exit_code}",
                "severity": 2,  # Warning
                "source": "Terminal"
            }])
    
    def _run_linting(self, file_path: str) -> None:
        """Run linting on a file."""
        if self._linting_manager:
            from core.linting import LintResult
            results: List[LintResult] = self._linting_manager.lint_file(file_path)
            
            if self._diagnostics_panel:
                diagnostics = []
                for result in results:
                    diagnostics.append({
                        "message": result.message,
                        "severity": 1 if result.severity == "error" else 2,
                        "source": result.linter,
                        "range": {
                            "start": {
                                "line": result.line - 1,
                                "character": result.column
                            }
                        }
                    })
                self._diagnostics_panel.set_diagnostics(diagnostics)
    
    def _on_about(self) -> None:
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        import os
        
        # Try to load about info from sobre.info file
        about_text = "Editor ISK 2.0\n\nA professional Python code editor with AI assistance."
        
        # Get the path to sobre.info (relative to main.py)
        sobre_info_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sobre.info")
        
        if os.path.exists(sobre_info_path):
            try:
                with open(sobre_info_path, 'r', encoding='utf-8') as f:
                    about_text = f.read()
            except Exception:
                pass  # Use default text if file can't be read
        
        QMessageBox.about(
            self,
            "About Editor ISK",
            about_text
        )
    
    def _apply_theme_to_all_editors(self, theme_name: str, bg_hex: str, fg_hex: str) -> None:
        """Apply theme to all open editor tabs."""
        for tab in self._open_tabs:
            tab.highlighter.set_theme_by_name(theme_name)
            tab.editor.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: {bg_hex};
                    color: {fg_hex};
                }}
            """)
    
    def _apply_saved_theme(self) -> None:
        """Apply the saved theme from config to all editors and UI."""
        if not self._config:
            return
            
        saved_theme = self._config.theme.name
        if not saved_theme:
            return
        
        # Validate that the saved theme exists in available themes
        available = self._config.get_available_themes()
        if saved_theme not in available:
            # Fall back to default theme if saved theme doesn't exist
            saved_theme = "Default Dark"
            self._config.set_theme(name=saved_theme)
            
        from core.editor import SyntaxHighlighter
        
        temp_highlighter = SyntaxHighlighter()
        temp_highlighter.set_theme_by_name(saved_theme)
        theme = temp_highlighter.theme
        bg_color = theme.background
        fg_color = theme.normal
        bg_hex = bg_color.name()
        fg_hex = fg_color.name()
        
        # Apply to open editors
        self._apply_theme_to_all_editors(saved_theme, bg_hex, fg_hex)
        
        # Apply theme to welcome screen
        if hasattr(self, '_welcome_screen') and self._welcome_screen:
            self._welcome_screen.set_theme(bg_hex, fg_hex)
        
        # Apply theme to main window - use _get_ui_stylesheet to preserve font size
        font_size = self._config.app.font_size if self._config else 10
        self.setStyleSheet(self._get_ui_stylesheet(font_size))
        
        # Recreate dock title bars with new theme
        self._recreate_dock_title_bars()
    
    def _recreate_dock_title_bars(self) -> None:
        """Recreate all dock widget title bars with current theme."""
        if not self._config:
            return
            
        # Update explorer dock
        if hasattr(self, '_explorer_dock') and self._explorer_dock:
            self._explorer_dock.setTitleBarWidget(self._create_dock_title_bar(
                "Explorer", "folder", self._explorer_dock
            ))
        
        # Update terminal dock
        if hasattr(self, '_terminal_dock') and self._terminal_dock:
            self._terminal_dock.setTitleBarWidget(self._create_dock_title_bar(
                "Terminal", "terminal", self._terminal_dock
            ))
        
        # Update diagnostics dock
        if hasattr(self, '_diagnostics_dock') and self._diagnostics_dock:
            self._diagnostics_dock.setTitleBarWidget(self._create_dock_title_bar(
                "Problems", "problems", self._diagnostics_dock
            ))
        
        # Update git dock
        if hasattr(self, '_git_dock') and self._git_dock:
            self._git_dock.setTitleBarWidget(self._create_dock_title_bar(
                "Git", "git", self._git_dock
            ))
        
        # Update outline dock
        if hasattr(self, '_outline_dock') and self._outline_dock:
            self._outline_dock.setTitleBarWidget(self._create_dock_title_bar(
                "Outline", "function", self._outline_dock
            ))
        
        # Update tasks dock
        if hasattr(self, '_task_dock') and self._task_dock:
            self._task_dock.setTitleBarWidget(self._create_dock_title_bar(
                "Tasks", "check", self._task_dock
            ))
        
        # Update snippets dock
        if hasattr(self, '_snippets_dock') and self._snippets_dock:
            self._snippets_dock.setTitleBarWidget(self._create_dock_title_bar(
                "Snippets", "code", self._snippets_dock
            ))
    
    def _on_change_theme(self, theme_name: str) -> None:
        """Change the editor theme."""
        if self._config:
            self._config.switch_theme(theme_name)
            from core.utils.config import ConfigManager
            ConfigManager().save(self._config)
        
        # Apply the saved theme (which now includes welcome screen and main window)
        self._apply_saved_theme()
    
    def _on_increase_font_size(self) -> None:
        """Increase UI font size."""
        if self._config:
            new_size = min(self._config.app.font_size + 1, 24)
            self._config.app.font_size = new_size
            from core.utils.config import ConfigManager
            ConfigManager().save(self._config)
            self._apply_ui_font_size()
    
    def _on_decrease_font_size(self) -> None:
        """Decrease UI font size."""
        if self._config:
            new_size = max(self._config.app.font_size - 1, 6)
            self._config.app.font_size = new_size
            from core.utils.config import ConfigManager
            ConfigManager().save(self._config)
            self._apply_ui_font_size()
    
    def _on_reset_font_size(self) -> None:
        """Reset UI font size to default."""
        if self._config:
            self._config.app.font_size = 10  # Default
            from core.utils.config import ConfigManager
            ConfigManager().save(self._config)
            self._apply_ui_font_size()
    
    def _apply_ui_font_size(self) -> None:
        """Apply UI font size to all UI elements."""
        if not self._config:
            return
            
        font_size = self._config.app.font_size
        
        # Apply font to main window
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)
        
        # Apply to all children
        for widget in self.findChildren(QWidget):
            widget_font = widget.font()
            widget_font.setPointSize(font_size)
            widget.setFont(widget_font)
        
        # Apply to menus
        self.setStyleSheet(self._get_ui_stylesheet(font_size))
    
    def _get_ui_stylesheet(self, font_size: int) -> str:
        """Get the UI stylesheet with the specified font size."""
        # Get current theme colors
        bg_hex = "#1e1e1e"
        fg_hex = "#d4d4d4"
        
        if self._config and self._config.theme.name:
            from core.editor import SyntaxHighlighter
            temp = SyntaxHighlighter()
            temp.set_theme_by_name(self._config.theme.name)
            theme = temp.theme
            bg_hex = theme.background.name()
            fg_hex = theme.normal.name()
        
        # Calculate button padding based on font size
        padding_vertical = max(4, font_size // 3)
        padding_horizontal = max(8, font_size)
        
        return f"""
            QWidget {{
                font-size: {font_size}pt;
            }}
            QMainWindow {{
                background-color: {bg_hex};
                color: {fg_hex};
            }}
            QMenuBar {{
                background-color: {bg_hex};
                color: {fg_hex};
                font-size: {font_size}pt;
                padding: {padding_vertical}px {padding_horizontal}px;
            }}
            QMenuBar::item:selected {{
                background-color: {fg_hex};
                color: {bg_hex};
            }}
            QMenu {{
                background-color: {bg_hex};
                color: {fg_hex};
                font-size: {font_size}pt;
                padding: {padding_vertical}px {padding_horizontal}px;
            }}
            QMenu::item:selected {{
                background-color: {fg_hex};
                color: {bg_hex};
            }}
            QToolBar {{
                background-color: {bg_hex};
                color: {fg_hex};
                padding: {padding_vertical}px {padding_horizontal}px;
            }}
            QStatusBar {{
                background-color: {bg_hex};
                color: {fg_hex};
                font-size: {font_size}pt;
            }}
            QDockWidget {{
                background-color: {bg_hex};
                color: {fg_hex};
                font-size: {font_size}pt;
            }}
            QDockWidget::title {{
                padding: {padding_vertical}px {padding_horizontal}px;
                font-size: {font_size}pt;
            }}
            QTabWidget::pane {{
                border: 1px solid {fg_hex};
                background-color: {bg_hex};
            }}
            QTabBar::tab {{
                background-color: {bg_hex};
                color: {fg_hex};
                padding: {padding_vertical}px {padding_horizontal}px;
                font-size: {font_size}pt;
            }}
            QTabBar::tab:selected {{
                background-color: {fg_hex};
                color: {bg_hex};
            }}
            QPushButton {{
                background-color: {bg_hex};
                color: {fg_hex};
                border: 1px solid {fg_hex};
                padding: {padding_vertical}px {padding_horizontal}px;
                border-radius: 4px;
                font-size: {font_size}pt;
                min-height: {font_size + 12}px;
            }}
            QPushButton:hover {{
                background-color: {fg_hex};
                color: {bg_hex};
            }}
            QPushButton:pressed {{
                background-color: {fg_hex};
                color: {bg_hex};
            }}
            QLabel {{
                font-size: {font_size}pt;
            }}
            QLineEdit, QTextEdit, QPlainTextEdit {{
                font-size: {font_size}pt;
                padding: {padding_vertical}px;
            }}
            QListWidget, QTreeWidget, QTableWidget {{
                font-size: {font_size}pt;
                background-color: {bg_hex};
                color: {fg_hex};
            }}
            QListWidget::item, QTreeWidget::item {{
                padding: {padding_vertical}px;
            }}
            QScrollBar {{
                width: {font_size + 4}px;
                height: {font_size + 4}px;
            }}
            QToolTip {{
                font-size: {font_size}pt;
                padding: 4px;
            }}
        """
    
    def _apply_saved_font_size(self) -> None:
        """Apply the saved UI font size at startup."""
        if not self._config:
            return
            
        font_size = self._config.app.font_size
        if font_size:
            self._apply_ui_font_size()
    
    def _ensure_panels_visible(self) -> None:
        """Ensure all dock panels are visible."""
        if hasattr(self, '_explorer_dock') and self._explorer_dock:
            self._explorer_dock.setVisible(True)
        if hasattr(self, '_terminal_dock') and self._terminal_dock:
            self._terminal_dock.setVisible(True)
        if hasattr(self, '_diagnostics_dock') and self._diagnostics_dock:
            self._diagnostics_dock.setVisible(True)
        if hasattr(self, '_git_dock') and self._git_dock:
            self._git_dock.setVisible(True)
        if hasattr(self, '_outline_dock') and self._outline_dock:
            self._outline_dock.setVisible(True)
        if hasattr(self, '_task_dock') and self._task_dock:
            self._task_dock.setVisible(True)
        if hasattr(self, '_snippets_dock') and self._snippets_dock:
            self._snippets_dock.setVisible(True)
    
    def _load_explorer_path(self) -> None:
        """Load and apply the saved explorer path."""
        if not self._config or not hasattr(self, '_file_explorer'):
            return
        
        saved_path = self._config.app.explorer_path
        if saved_path and Path(saved_path).exists():
            self._file_explorer.set_root_path(saved_path)
        else:
            # Default to home directory if no saved path
            default_path = str(Path.home())
            self._file_explorer.set_root_path(default_path)
            self._config.app.explorer_path = default_path
            from core.utils.config import ConfigManager
            ConfigManager().save(self._config)
    
    def _update_explorer_path(self, file_path: str) -> None:
        """Update the explorer path when a file is opened."""
        if not self._config or not hasattr(self, '_file_explorer'):
            return
        
        folder = str(Path(file_path).parent)
        self._file_explorer.set_root_path(folder)
        self._config.app.explorer_path = folder
        from core.utils.config import ConfigManager
        ConfigManager().save(self._config)
    
    def _on_create_snippet(self) -> None:
        """Create a new snippet."""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        
        # Get snippet details
        name, ok = QInputDialog.getText(self, "New Snippet", "Snippet name:")
        if not ok or not name:
            return
        
        trigger, ok = QInputDialog.getText(self, "New Snippet", "Trigger word:")
        if not ok or not trigger:
            return
        
        content, ok = QInputDialog.getMultiLineText(self, "New Snippet", "Content:")
        if not ok or not content:
            return
        
        # Create snippet
        from features.snippets import SnippetManager, Snippet
        snippet = Snippet(
            id=name.lower().replace(" ", "_"),
            name=name,
            trigger=trigger,
            content=content,
            language="python"
        )
        
        # Add to manager
        if not self._snippet_manager:
            self._snippet_manager = SnippetManager()
        
        if self._snippet_manager.add_snippet(snippet):
            QMessageBox.information(self, "Snippets", f"Snippet '{name}' created successfully!")
        else:
            QMessageBox.warning(self, "Snippets", f"Snippet '{name}' already exists.")
    
    def _on_reload_snippets(self) -> None:
        """Reload snippets from files."""
        from PyQt6.QtWidgets import QMessageBox
        
        # Create manager and reload
        from features.snippets import SnippetManager
        self._snippet_manager = SnippetManager()
        count = self._snippet_manager.reload()
        
        QMessageBox.information(self, "Snippets", f"Reloaded {count} snippets.")
    
    def _on_manage_snippets(self) -> None:
        """Open snippet manager."""
        from features.snippets import SnippetManager
        from ui.widgets import SnippetManagerDialog
        
        # Get or create snippet manager
        if not self._snippet_manager:
            self._snippet_manager = SnippetManager()
            # Load snippets from project resources directory
            snippet_dir = Path(__file__).parent.parent / "resources" / "snippets"
            self._snippet_manager.load_from_directory(str(snippet_dir))
        
        # Show dialog
        dialog = SnippetManagerDialog(self, self._snippet_manager)
        dialog.set_snippet_manager(self._snippet_manager)
        dialog.exec()
    
    def _on_ai_settings(self) -> None:
        """Open AI settings dialog."""
        from ui.widgets import AISettingsDialog
        
        dialog = AISettingsDialog(self)
        dialog.exec()
    
    def _on_editor_settings(self) -> None:
        """Open editor settings."""
        from ui.widgets.settings import SettingsDialog
        
        lang = self._config.app.language if self._config else "es"
        dialog = SettingsDialog(self, lang, self._config)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()
    
    def _on_settings_changed(self, settings: dict) -> None:
        """Handle settings changes."""
        # Apply font settings
        if 'editor' in settings:
            editor_settings = settings['editor']
            
            # Apply to current editor
            if self.current_editor:
                if 'font_family' in editor_settings:
                    font = self.current_editor.font()
                    font.setFamily(editor_settings['font_family'])
                    self.current_editor.setFont(font)
                
                if 'font_size' in editor_settings:
                    font = self.current_editor.font()
                    font.setPointSize(editor_settings['font_size'])
                    self.current_editor.setFont(font)
        
        # Apply theme
        if 'appearance' in settings:
            appearance = settings['appearance']
            if 'theme' in appearance:
                self._on_change_theme(appearance['theme'])
        
        # Save config
        if self._config:
            from core.utils.config import ConfigManager
            ConfigManager().save(self._config)
    
    def _on_editor_config_changed(self, key: str, value: Any) -> None:
        """Handle editor config changes from signals (e.g., Ctrl+wheel zoom)."""
        if key == 'font_size':
            self._apply_editor_font_size(value)
    
    def _apply_editor_font_size(self, font_size: int) -> None:
        """Apply font size to all open editors."""
        for tab in self._open_tabs:
            if tab.editor:
                font = tab.editor.font()
                font.setPointSize(font_size)
                tab.editor.setFont(font)
    
    def _on_change_language(self, lang_code: str) -> None:
        """Change the application language."""
        if self._config:
            self._config.app.language = lang_code
            from core.utils.config import ConfigManager
            ConfigManager().save(self._config)
        
        # Update checkmarks in language menu
        for code, action in self._language_actions.items():
            action.setChecked(code == lang_code)
        
        # Reload translations
        self._load_translations(lang_code)
        
        # Translate UI in real-time
        self._translate_ui(lang_code)
    
    def _translate_ui(self, lang_code: str) -> None:
        """Translate UI elements in real-time."""
        from resources.translations import I18n
        from pathlib import Path
        
        # Use the existing I18n instance if it has translations, otherwise create new one
        if not hasattr(self, '_i18n') or self._i18n is None:
            translations_path = Path(__file__).parent.parent / "resources" / "translations"
            self._i18n = I18n()
            
            lang_map = {
                "es": "Español.json",
                "en": "English.json",
            }
            filename = lang_map.get(lang_code, f"{lang_code}.json")
            lang_file = translations_path / filename
            
            if lang_file.exists():
                self._i18n.load_translation(lang_code, lang_file)
                self._i18n.set_locale(lang_code)
        
        # If locale changed, reload translations
        if self._i18n._current_locale != lang_code:
            translations_path = Path(__file__).parent.parent / "resources" / "translations"
            lang_map = {
                "es": "Español.json",
                "en": "English.json",
            }
            filename = lang_map.get(lang_code, f"{lang_code}.json")
            lang_file = translations_path / filename
            
            if lang_file.exists():
                self._i18n.load_translation(lang_code, lang_file)
                self._i18n.set_locale(lang_code)
        
        # Get translation function
        def t(key: str, default: str = "") -> str:
            return self._i18n.translate(key, default)
        
        # Translate menu bar
        menubar = self.menuBar()
        
        # Find and translate menus
        for action in menubar.actions():
            menu = action.menu()
            if menu is None:
                continue
            
            # Translate menu title
            title = menu.title()
            if "&" in title:
                key = title.replace("&", "").lower()
            else:
                key = title.lower()
            
            # Map menu titles to translation keys
            menu_keys = {
                "&File": "menu.file",
                "&Edit": "menu.edit",
                "&View": "menu.view",
                "&Search": "menu.search",
                "&Run": "menu.run",
                "&Tools": "menu.tools",
                "&Preferences": "menu.preferences",
                "&Help": "menu.help",
                "&Git": "menu.git",
            }
            
            # Check if menu has stored translation key
            menu_key = menu.property("trans_key")
            
            if not menu_key and title in menu_keys:
                menu_key = menu_keys[title]
                menu.setProperty("trans_key", menu_key)
            
            if menu_key:
                translated = t(menu_key, title)
                menu.setTitle(translated)
            
            # Translate menu actions
            for menu_action in menu.actions():
                # First check if action has stored translation key
                trans_key = menu_action.data()
                
                if not trans_key:
                    # Try to find and store the translation key
                    text = menu_action.text()
                    if not text:
                        continue
                    
                    action_keys = {
                        "&New": "menu.new_file",
                        "Open &Folder": "menu.open_folder",
                        "&Save": "menu.save",
                        "Save &as...": "menu.save_as",
                        "&Close": "menu.close",
                        "&Exit": "menu.exit",
                        "&Undo": "menu.undo",
                        "&Redo": "menu.redo",
                        "&Cut": "menu.cut",
                        "&Copy": "menu.copy",
                        "&Paste": "menu.paste",
                        "Select &All": "menu.select_all",
                        "&Find...": "menu.find",
                        "&Replace...": "menu.replace",
                        "&Comment": "menu.toggle_comment",
                        "&Format Code": "menu.format_code",
                        "&Command Palette...": "menu.command_palette",
                        "Quick &Command...": "menu.quick_command",
                        "&Linter Settings...": "menu.linter_settings",
                        "&Plugin Manager...": "menu.plugin_manager",
                        "&Keyboard Shortcuts...": "menu.keyboard_shortcuts",
                        "&Language": "menu.language",
                        "&Themes": "menu.themes",
                        "&Manage Snippets...": "menu.manage_snippets",
                        "&AI Settings...": "menu.ai_settings",
                        "&Editor Settings...": "menu.editor_settings",
                        "&Vim Mode": "menu.vim_mode",
                        "&Line Numbers": "menu.line_numbers",
                        "&Word Wrap": "menu.word_wrap",
                        "&Minimap": "menu.minimap",
                        "&Navigation Bar": "menu.navbar",
                        "&Fold All": "menu.fold_all",
                        "&Unfold All": "menu.unfold_all",
                        "Zoom &In": "menu.zoom_in",
                        "Zoom &Out": "menu.zoom_out",
                        "&Reset Zoom": "menu.reset_zoom",
                        "&File Explorer": "menu.file_explorer",
                        "&Terminal": "menu.terminal",
                        "&Problems": "menu.problems",
                        "&Git Panel": "menu.git_panel",
                        "&AI Panel": "menu.ai_panel",
                        "&Compare Files": "menu.compare_files",
                        "&Outline": "menu.outline",
                        "&Tasks": "menu.tasks",
                        "&Snippets": "menu.snippets",
                        "Split &Horizontal": "menu.split_horizontal",
                        "Split &Vertical": "menu.split_vertical",
                        "&Close Split": "menu.close_split",
                        "Focus &Next Split": "menu.next_split",
                        "Focus &Previous Split": "menu.prev_split",
                        "&About": "menu.about",
                        "&Refresh": "menu.refresh",
                        "&Commit": "menu.commit",
                        "&Pull": "menu.pull",
                        "&Push": "menu.push",
                        "&Branch": "menu.branch",
                        "Go to &Line...": "menu.goto_line",
                        "Go to &Symbol...": "menu.goto_symbol",
                        "Find in &Files...": "menu.find_in_files",
                        "&Quick Open...": "menu.quick_open",
                        "&Run File": "menu.run_file",
                        "&Stop Execution": "menu.stop",
                        "Diff &Viewer": "menu.diff_viewer",
                        "Close &All": "menu.close_all",
                        "Open F&older...": "menu.open_folder",
                        "&Open Project...": "menu.open_project",
                        "Recent &Files": "menu.recent_files",
                        "Cu&t": "menu.cut",
                        "E&xit": "menu.exit",
                        "Save &As...": "menu.save_as",
                        "Increase": "menu.increase_font",
                        "Decrease": "menu.decrease_font",
                        "Reset to Default": "menu.reset_font",
                        "Move Line &Up": "menu.move_up",
                        "Move Line &Down": "menu.move_down",
                        "Copy Line &Up": "menu.copy",
                        "Copy Line &Down": "menu.copy",
                        "&Delete Line": "menu.delete_line",
                        "&Expand Emmet Abbreviation": "menu.expand_emmet",
                        "&Font Size": "menu.font_size",
                        "Clear Recent Files": "menu.clear_recent_files",
                        "No Recent Files": "menu.no_recent_files",
                    }
                    
                    for eng_key, key in action_keys.items():
                        if eng_key in text:
                            trans_key = key
                            menu_action.setData(key)
                            break
                
                # Translate using stored key
                if trans_key:
                    translated = t(trans_key, menu_action.text())
                    menu_action.setText(translated)
        
        # Translate status bar if exists
        if hasattr(self, '_status_bar'):
            self._translate_status_bar(t)
        
        # Translate dock widget titles
        self._translate_dock_titles(t)
        
        # Translate dialogs and panels
        self._translate_panels(t)
    
    def _translate_status_bar(self, t) -> None:
        """Translate status bar elements."""
        if hasattr(self, '_language_label') and self._language_label:
            self._language_label.setText(t("editor.language", "Lenguaje"))
        
        if hasattr(self, '_encoding_label') and self._encoding_label:
            self._encoding_label.setText(t("editor.encoding", "Codificación"))
        
        if hasattr(self, '_line_col_label') and self._line_col_label:
            pass  # This one updates dynamically
    
    def _translate_dock_titles(self, t) -> None:
        """Translate dock widget titles."""
        # File Explorer
        if hasattr(self, '_explorer_dock') and self._explorer_dock:
            title = t("explorer.title", "Explorador")
            self._explorer_dock.setWindowTitle(title)
            # Recreate title bar with translated title
            self._explorer_dock.setTitleBarWidget(self._create_dock_title_bar(
                title, "folder", self._explorer_dock
            ))
        
        # Terminal
        if hasattr(self, '_terminal_dock') and self._terminal_dock:
            title = t("terminal.title", "Terminal")
            self._terminal_dock.setWindowTitle(title)
            self._terminal_dock.setTitleBarWidget(self._create_dock_title_bar(
                title, "terminal", self._terminal_dock
            ))
        
        # Diagnostics
        if hasattr(self, '_diagnostics_dock') and self._diagnostics_dock:
            title = t("problems.title", "Problemas")
            self._diagnostics_dock.setWindowTitle(title)
            self._diagnostics_dock.setTitleBarWidget(self._create_dock_title_bar(
                title, "problems", self._diagnostics_dock
            ))
        
        # Git
        if hasattr(self, '_git_dock') and self._git_dock:
            title = t("git.title", "Git")
            self._git_dock.setWindowTitle(title)
            self._git_dock.setTitleBarWidget(self._create_dock_title_bar(
                title, "git", self._git_dock
            ))
        
        # AI Panel
        if hasattr(self, '_ai_panel_dock') and self._ai_panel_dock:
            title = t("ai.title", "Asistente IA")
            self._ai_panel_dock.setWindowTitle(title)
            self._ai_panel_dock.setTitleBarWidget(self._create_dock_title_bar(
                title, "ai", self._ai_panel_dock
            ))
        
        # Outline
        if hasattr(self, '_outline_dock') and self._outline_dock:
            title = t("outline.title", "Esquema")
            self._outline_dock.setWindowTitle(title)
            self._outline_dock.setTitleBarWidget(self._create_dock_title_bar(
                title, "function", self._outline_dock
            ))
        
        # Task List
        if hasattr(self, '_task_dock') and self._task_dock:
            title = t("tasks.title", "Tareas")
            self._task_dock.setWindowTitle(title)
            self._task_dock.setTitleBarWidget(self._create_dock_title_bar(
                title, "check", self._task_dock
            ))
        
        # Snippets
        if hasattr(self, '_snippets_dock') and self._snippets_dock:
            title = t("snippets.title", "Fragmentos")
            self._snippets_dock.setWindowTitle(title)
            self._snippets_dock.setTitleBarWidget(self._create_dock_title_bar(
                title, "code", self._snippets_dock
            ))
    
    def _translate_panels(self, t) -> None:
        """Translate panel elements."""
        # Snippets panel
        if hasattr(self, '_snippets_panel') and self._snippets_panel:
            self._snippets_panel.set_language(self._config.app.language)
        
        # File explorer title
        if hasattr(self, '_file_explorer') and self._file_explorer:
            # The file explorer has internal labels that might need translation
            pass
        
        # Terminal - set language for UI elements
        if hasattr(self, '_terminal') and self._terminal:
            self._terminal.set_language(self._config.app.language)
        
        # Welcome screen - set language for UI elements
        if hasattr(self, '_welcome_screen') and self._welcome_screen:
            self._welcome_screen.set_language(self._config.app.language)
            self._welcome_screen.set_recent_files(self._config.get_recent_files())
    
    def _load_translations(self, lang_code: str) -> None:
        """Load translations for the selected language."""
        from resources.translations import I18n
        from pathlib import Path
        
        translations_path = Path(__file__).parent.parent / "resources" / "translations"
        i18n = I18n(self)
        
        # Load the selected language - map lang_code to filename
        lang_map = {
            "es": "Español.json",
            "en": "English.json",
        }
        filename = lang_map.get(lang_code, f"{lang_code}.json")
        lang_file = translations_path / filename
        
        if lang_file.exists():
            i18n.load_translation(lang_code, lang_file)
            i18n.set_locale(lang_code)
        
        # Store for use throughout the app
        self._i18n = i18n
    
    def _on_toggle_vim_mode(self, enabled: bool) -> None:
        """Toggle Vim mode."""
        from core.editor.vim_mode import get_vim_engine
        
        vim_engine = get_vim_engine()
        vim_engine.set_enabled(enabled)
        
        if self.current_editor:
            vim_engine.set_editor(self.current_editor)
        
        # Update status bar
        if enabled:
            self._vim_status_label = vim_engine.get_status_text()
        else:
            self._vim_status_label = ""
    
    def _on_run_file(self) -> None:
        """Run the current file."""
        if self._current_tab_index >= 0:
            tab = self._open_tabs[self._current_tab_index]
            if tab.file_path and self._terminal:
                self._terminal.run_file(tab.file_path)
    
    def _on_stop_execution(self) -> None:
        """Stop the current execution."""
        if self._terminal:
            self._terminal.stop_execution()
    
    def _on_debug_file(self) -> None:
        """Debug the current file."""
        if self._current_tab_index >= 0:
            tab = self._open_tabs[self._current_tab_index]
            if tab.file_path and self._terminal:
                self._terminal.run_file(tab.file_path, debug=True)
    
    def _on_build_project(self) -> None:
        """Build the current project."""
        if hasattr(self, '_project_manager') and self._project_manager:
            project = self._project_manager.get_current_project()
            if project and self._terminal:
                self._terminal.run_command(f'cd "{project.root_path}" && make')
    
    def _on_save_all(self) -> None:
        """Save all open files."""
        for i in range(len(self._open_tabs)):
            tab = self._open_tabs[i]
            if tab.is_modified:
                self._save_file_at_index(i)
    
    def _on_toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        if hasattr(self, '_explorer_dock') and self._explorer_dock:
            if self._explorer_dock.isVisible():
                self._explorer_dock.hide()
            else:
                self._explorer_dock.show()
    
    def _on_indent_selection(self) -> None:
        """Indent the current selection."""
        if self.current_editor:
            self.current_editor.indent_selection()
    
    def _on_outdent_selection(self) -> None:
        """Outdent the current selection."""
        if self.current_editor:
            self.current_editor.outdent_selection()
    
    def _on_duplicate_line(self) -> None:
        """Duplicate the current line."""
        if self.current_editor:
            cursor = self.current_editor.textCursor()
            cursor.beginEditBlock()
            cursor.select(cursor.SelectionType.LineUnderCursor)
            line_text = cursor.selectedText()
            cursor.clearSelection()
            cursor.movePosition(cursor.MoveOperation.EndOfLine)
            cursor.insertText('\n' + line_text)
            cursor.endEditBlock()
    
    def _on_git_refresh(self) -> None:
        """Refresh Git panel."""
        if self._git_panel:
            self._git_panel.refresh()
    
    def _on_git_commit(self) -> None:
        """Open commit dialog."""
        if self._git_panel:
            self._git_panel.show_commit_dialog()
    
    def _on_git_pull(self) -> None:
        """Git pull."""
        if self._git_panel:
            self._git_panel.pull()
    
    def _on_git_push(self) -> None:
        """Git push."""
        if self._git_panel:
            self._git_panel.push()
    
    def _on_git_branch(self) -> None:
        """Open branch dialog."""
        if self._git_panel:
            self._git_panel.show_branch_dialog()
    
    def _on_show_command_palette(self) -> None:
        """Show command palette."""
        if self._command_palette:
            self._command_palette.show()
    
    def _on_show_quick_command(self) -> None:
        """Show quick command panel."""
        from ui.widgets.quick_command_panel import QuickCommandPanel
        
        dialog = QuickCommandPanel(self)
        dialog.command_selected.connect(self._on_execute_quick_command)
        dialog.exec()
    
    def _on_execute_quick_command(self, command: str) -> None:
        """Execute a quick command in terminal."""
        if hasattr(self, '_terminal') and self._terminal:
            # Send command to terminal
            # The terminal needs to have a method to execute commands
            pass
        
        # Show in terminal panel if available
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Quick Command",
            f"Command: {command}\n\nSend this command to the terminal?"
        )
    
    def _on_lint_settings(self) -> None:
        """Show linter settings."""
        from PyQt6.QtWidgets import QMessageBox
        available = self._linting_manager.get_available_linters() if self._linting_manager else []
        available_str = [str(l) for l in available]
        QMessageBox.information(
            self, "Linter Settings",
            f"Available linters: {', '.join(available_str) if available_str else 'None'}\n\n"
            "Linting runs automatically when files are saved."
        )
    
    def _on_plugin_manager(self) -> None:
        """Show plugin manager."""
        from PyQt6.QtWidgets import QMessageBox
        if self._plugin_manager:
            plugins = list(self._plugin_manager.plugins.keys())
            QMessageBox.information(
                self, "Plugin Manager",
                f"Loaded plugins: {', '.join(plugins) if plugins else 'None'}"
            )
    
    def _on_keyboard_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        from ui.widgets import KeyboardShortcutsDialog
        dialog = KeyboardShortcutsDialog(self)
        dialog.exec()
    
    def _on_format_code(self) -> None:
        """Format code in current editor."""
        from PyQt6.QtWidgets import QMessageBox
        
        editor = self.current_editor
        if not editor:
            QMessageBox.warning(self, "Format Code", "No editor available.")
            return
        
        tab = self._open_tabs[self._current_tab_index]
        if not tab.file_path:
            QMessageBox.warning(self, "Format Code", "Save the file first to format it.")
            return
        
        try:
            if self._code_formatter.format_file(tab.file_path, "black"):
                # Reload the file to show formatted content
                self._open_tabs[self._current_tab_index].is_modified = False
                self._load_file_content(tab.file_path)
                QMessageBox.information(self, "Format Code", "Code formatted successfully!")
            else:
                QMessageBox.warning(self, "Format Code", "Failed to format code. Is Black installed?")
        except ImportError:
            QMessageBox.warning(self, "Format Code", "Black is not installed. Run: pip install black")
        except Exception as e:
            QMessageBox.warning(self, "Format Code", f"Error: {str(e)}")
    
    def _on_toggle_explorer(self) -> None:
        """Toggle file explorer visibility."""
        if hasattr(self, '_explorer_dock'):
            visible = not self._explorer_dock.isVisible()
            self._explorer_dock.setVisible(visible)
            self._toggle_explorer_action.setChecked(visible)
    
    def _on_toggle_terminal(self) -> None:
        """Toggle terminal visibility."""
        if hasattr(self, '_terminal_dock'):
            visible = not self._terminal_dock.isVisible()
            self._terminal_dock.setVisible(visible)
            self._toggle_terminal_action.setChecked(visible)
    
    def _on_toggle_diagnostics(self) -> None:
        """Toggle diagnostics panel visibility."""
        if hasattr(self, '_diagnostics_dock'):
            visible = not self._diagnostics_dock.isVisible()
            self._diagnostics_dock.setVisible(visible)
            self._toggle_diagnostics_action.setChecked(visible)
    
    def _on_toggle_ai_panel(self) -> None:
        """Toggle AI panel visibility."""
        if self._ai_panel_dock is None:
            self._create_ai_panel()
        
        visible = not self._ai_panel_dock.isVisible()
        self._ai_panel_dock.setVisible(visible)
        self._toggle_ai_panel_action.setChecked(visible)
    
    def _on_toggle_git(self) -> None:
        """Toggle Git panel visibility."""
        if hasattr(self, '_git_dock'):
            visible = not self._git_dock.isVisible()
            self._git_dock.setVisible(visible)
            self._toggle_git_action.setChecked(visible)
    
    def _on_toggle_minimap(self) -> None:
        """Toggle minimap visibility."""
        editor = self.current_editor
        if editor and hasattr(editor, 'set_minimap_visible'):
            current = editor.minimap_visible
            editor.set_minimap_visible(not current)
    
    def _on_toggle_navbar(self) -> None:
        """Toggle navigation bar visibility."""
        if self._navigation_bar:
            visible = not self._navigation_bar.isVisible()
            self._navigation_bar.setVisible(visible)
    
    def _on_toggle_outline(self) -> None:
        """Toggle outline panel visibility."""
        if hasattr(self, '_outline_dock'):
            visible = not self._outline_dock.isVisible()
            self._outline_dock.setVisible(visible)
            self._toggle_outline_action.setChecked(visible)
    
    def _on_toggle_tasks(self) -> None:
        """Toggle tasks panel visibility."""
        if hasattr(self, '_task_dock'):
            visible = not self._task_dock.isVisible()
            self._task_dock.setVisible(visible)
            self._toggle_tasks_action.setChecked(visible)
    
    def _on_toggle_snippets(self) -> None:
        """Toggle snippets panel visibility."""
        if hasattr(self, '_snippets_dock'):
            visible = not self._snippets_dock.isVisible()
            self._snippets_dock.setVisible(visible)
            self._toggle_snippets_action.setChecked(visible)
    
    def _on_toggle_line_numbers(self) -> None:
        """Toggle line number visibility."""
        editor = self.current_editor
        if editor and hasattr(editor, 'setLineNumberAreaVisible'):
            visible = not self._toggle_line_numbers_action.isChecked()
            editor.setLineNumberAreaVisible(visible)
    
    def _on_toggle_word_wrap(self) -> None:
        """Toggle word wrap."""
        editor = self.current_editor
        if editor:
            if hasattr(editor, 'setLineWrapMode'):
                mode = editor.lineWrapMode()
                if mode == editor.LineWrapMode.NoWrap:
                    editor.setLineWrapMode(editor.LineWrapMode.WidgetWidth)
                else:
                    editor.setLineWrapMode(editor.LineWrapMode.NoWrap)
    
    def _on_toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def _on_split_horizontal(self) -> None:
        """Split editor horizontally."""
        if hasattr(self, '_split_manager') and self._split_manager:
            self._split_manager.split_horizontal()
    
    def _on_split_vertical(self) -> None:
        """Split editor vertically."""
        if hasattr(self, '_split_manager') and self._split_manager:
            self._split_manager.split_vertical()
    
    def _on_close_split(self) -> None:
        """Close the active split."""
        if hasattr(self, '_split_manager') and self._split_manager:
            self._split_manager.close_active_split()
    
    def _on_focus_next_split(self) -> None:
        """Focus next split."""
        if hasattr(self, '_split_manager') and self._split_manager:
            self._split_manager.focus_next_split()
    
    def _on_focus_previous_split(self) -> None:
        """Focus previous split."""
        if hasattr(self, '_split_manager') and self._split_manager:
            self._split_manager.focus_previous_split()
    
    def _on_zoom_in(self) -> None:
        """Zoom in editor."""
        editor = self.current_editor
        if editor:
            from PyQt6.QtWidgets import QApplication
            factor = QApplication.font().pointSizeF()
            if factor < 32:
                editor.setStyleSheet(f"font-size: {int(factor + 2)}pt;")
    
    def _on_zoom_out(self) -> None:
        """Zoom out editor."""
        editor = self.current_editor
        if editor:
            from PyQt6.QtWidgets import QApplication
            factor = QApplication.font().pointSizeF()
            if factor > 6:
                editor.setStyleSheet(f"font-size: {int(factor - 2)}pt;")
    
    def _on_zoom_reset(self) -> None:
        """Reset zoom."""
        editor = self.current_editor
        if editor:
            editor.setStyleSheet("")
    
    def _on_show_diff_viewer(self) -> None:
        """Show diff viewer dialog."""
        from ui.widgets import DiffViewer
        from PyQt6.QtWidgets import QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Compare Files")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        diff_viewer = DiffViewer(dialog)
        layout.addWidget(diff_viewer)
        
        dialog.exec()
    
    def _on_fold_all(self) -> None:
        """Fold all code blocks."""
        editor = self.current_editor
        if editor and hasattr(editor, 'fold_all'):
            editor.fold_all()
    
    def _on_unfold_all(self) -> None:
        """Unfold all code blocks."""
        editor = self.current_editor
        if editor and hasattr(editor, 'unfold_all'):
            editor.unfold_all()
    
    def _create_ai_panel(self) -> None:
        """Create the AI panel dock widget."""
        self._ai_panel = AIPanelWidget(self)
        self._ai_panel_dock = QDockWidget("AI Panel", self)
        self._ai_panel_dock.setObjectName("AIPanelDock")
        self._ai_panel_dock.setWidget(self._ai_panel)
        self._ai_panel_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
        self._ai_panel_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        # Set minimum width to match other panels
        self._ai_panel_dock.setMinimumWidth(200)
        # Initially hidden - will be shown by _load_ui_state if needed
        self._ai_panel_dock.hide()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._ai_panel_dock)
        
        # Sync menu checkbox when dock visibility changes (e.g., via close button)
        self._ai_panel_dock.visibilityChanged.connect(
            lambda visible: self._toggle_ai_panel_action.setChecked(visible)
        )
        
        # Add close button to AI dock
        self._ai_panel_dock.setTitleBarWidget(self._create_dock_title_bar(
            "AI Panel", "ai", self._ai_panel_dock
        ))
    
    # Edit operations
    
    def _on_undo(self) -> None:
        """Handle undo action."""
        editor = self.current_editor
        if editor:
            editor.undo()
    
    def _on_redo(self) -> None:
        """Handle redo action."""
        editor = self.current_editor
        if editor:
            editor.redo()
    
    def _on_cut(self) -> None:
        """Handle cut action."""
        editor = self.current_editor
        if editor:
            editor.cut()
    
    def _on_copy(self) -> None:
        """Handle copy action."""
        editor = self.current_editor
        if editor:
            editor.copy()
    
    def _on_paste(self) -> None:
        """Handle paste action."""
        editor = self.current_editor
        if editor:
            editor.paste()
    
    def _on_find(self) -> None:
        """Handle find action - show find/replace panel."""
        # Create or show the find/replace panel
        if not hasattr(self, '_find_replace_panel') or self._find_replace_panel is None:
            from ui.widgets import FindReplacePanel
            
            self._find_replace_panel = FindReplacePanel(self)
            self._find_replace_panel.set_document(self.current_editor.document() if self.current_editor else None)
            self._find_replace_panel.set_editor(self.current_editor)
            self._find_replace_panel.setWindowFlags(
                Qt.WindowType.Tool | 
                Qt.WindowType.WindowStaysOnTopHint
            )
            self._find_replace_panel.setWindowTitle("Find / Replace")
            self._find_replace_panel.close_requested.connect(self._on_find_replace_close)
            
            # Connect signals to move cursor
            self._find_replace_panel.find_in_document.connect(self._move_cursor_to_match)
            
            # Position near the editor
            if self.current_editor:
                pos = self.current_editor.mapToGlobal(self.current_editor.rect().topRight())
                self._find_replace_panel.move(pos.x() - self._find_replace_panel.width(), pos.y())
        
        self._find_replace_panel.show()
        self._find_replace_panel.activateWindow()
        self._find_replace_panel._search_input.setFocus()
    
    def _on_find_replace_close(self) -> None:
        """Handle find/replace panel close."""
        if hasattr(self, '_find_replace_panel') and self._find_replace_panel:
            self._find_replace_panel.hide()
    
    def _on_goto_line(self) -> None:
        """Handle go to line action."""
        from PyQt6.QtWidgets import QInputDialog, QWidget
        
        editor = self.current_editor
        if not editor:
            return
        
        # Get total line count
        total_lines = editor.document().blockCount()
        
        line, ok = QInputDialog.getInt(
            self,
            "Go to Line",
            f"Line number (1-{total_lines}):",
            1, 1, total_lines
        )
        
        if ok and line > 0:
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            
            for _ in range(line - 1):
                cursor.movePosition(cursor.MoveOperation.Down)
            
            cursor.select(cursor.LineUnderCursor)
            cursor.clearSelection()
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            
            editor.setTextCursor(cursor)
            editor.setFocus()
            editor.ensureCursorVisible()
    
    def _on_goto_symbol(self) -> None:
        """Handle go to symbol action."""
        editor = self.current_editor
        if not editor or not hasattr(self, '_symbol_outline'):
            return
        
        symbols = []
        if hasattr(self._symbol_outline, '_symbols'):
            symbols = [
                {"name": s.name, "line": s.line, "type": s.symbol_type}
                for s in self._symbol_outline._symbols
            ]
        
        if not symbols:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Go to Symbol", "No symbols found in current file.")
            return
        
        from ui.widgets.go_to_symbol import GoToSymbolDialog
        
        dialog = GoToSymbolDialog(symbols, self)
        dialog.symbol_selected.connect(self._go_to_line_from_symbol)
        dialog.exec()
    
    def _go_to_line_from_symbol(self, line: int) -> None:
        """Go to line from symbol selection."""
        editor = self.current_editor
        if not editor:
            return
        
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        
        for _ in range(line - 1):
            cursor.movePosition(cursor.MoveOperation.Down)
        
        cursor.movePosition(cursor.MoveOperation.StartOfLine)
        editor.setTextCursor(cursor)
        editor.setFocus()
        editor.ensureCursorVisible()
    
    def _on_quick_open(self) -> None:
        """Handle quick open action."""
        from ui.widgets import QuickOpenDialog
        
        root = ""
        if self._file_explorer:
            root = self._file_explorer.root_path or os.getcwd()
        
        dialog = QuickOpenDialog(self, root)
        dialog.file_selected.connect(self._open_file)
        dialog.exec()
    
    def _move_cursor_to_match(self, search_text: str, flags: int) -> None:
        """Move cursor to the search match."""
        if not self.current_editor:
            return
        
        cursor = self.current_editor.document().find(search_text, self.current_editor.textCursor(), flags)
        if not cursor.isNull():
            self.current_editor.setTextCursor(cursor)
            self.current_editor.setFocus()
    
    def _on_replace(self) -> None:
        """Handle replace action - show find/replace panel."""
        # Just call find, which will show the panel with replace section
        self._on_find()
    
    def _on_find_in_files(self) -> None:
        """Handle find in files action - show search in files dialog."""
        from ui.widgets import SearchResultsPanel
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog
        from pathlib import Path
        import re
        import os
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Find in Files")
        dialog.setMinimumSize(500, 200)
        layout = QVBoxLayout(dialog)
        
        # Search input
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Text to find...")
        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)
        
        # Directory input
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Directory:"))
        dir_input = QLineEdit()
        dir_input.setPlaceholderText("Select directory...")
        dir_input.setText(os.getcwd())
        dir_layout.addWidget(dir_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: dir_input.setText(QFileDialog.getExistingDirectory(dialog, "Select Directory")))
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        search_btn = QPushButton("Search")
        close_btn = QPushButton("Close")
        button_layout.addWidget(search_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        # Results panel (will be created when search runs)
        results_panel = SearchResultsPanel(self)
        
        def do_search():
            search_text = search_input.text()
            directory = dir_input.text()
            
            if not search_text or not directory:
                return
            
            results = []
            
            try:
                pattern = re.compile(search_text, re.IGNORECASE)
                
                for root, dirs, files in os.walk(directory):
                    # Skip common directories
                    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
                    
                    for file in files:
                        if file.endswith(('.py', '.txt', '.js', '.ts', '.html', '.css', '.json', '.md', '.yml', '.yaml', '.sh')):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    for line_num, line in enumerate(f, 1):
                                        match = pattern.search(line)
                                        if match:
                                            from ui.widgets.search_results import SearchResult
                                            results.append(SearchResult(
                                                file_path=file_path,
                                                line_number=line_num,
                                                line_content=line.rstrip(),
                                                match_start=match.start(),
                                                match_end=match.end()
                                            ))
                            except Exception:
                                pass
            except re.error:
                pass
            
            results_panel.set_results(results)
        
        search_btn.clicked.connect(do_search)
        close_btn.clicked.connect(dialog.close)
        
        # Show results panel below
        layout.addWidget(results_panel)
        
        dialog.exec()
    
    def _on_select_all(self) -> None:
        """Handle select all action."""
        editor = self.current_editor
        if editor:
            editor.selectAll()
    
    def _on_move_line_up(self) -> None:
        """Move current line up."""
        editor = self.current_editor
        if editor:
            cursor = editor.textCursor()
            if cursor.blockNumber() > 0:
                cursor.beginEditBlock()
                block = cursor.block()
                text = block.text()
                cursor.removeSelectedText()
                cursor.deleteChar()
                cursor.movePosition(cursor.MoveOperation.Up)
                cursor.insertText(text + "\n")
                cursor.endEditBlock()
    
    def _on_move_line_down(self) -> None:
        """Move current line down."""
        editor = self.current_editor
        if editor:
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Down)
            if cursor.atEnd():
                cursor.insertText("\n")
            else:
                cursor = editor.textCursor()
                block = cursor.block()
                text = block.text()
                cursor.beginEditBlock()
                cursor.removeSelectedText()
                cursor.deleteChar()
                cursor.movePosition(cursor.MoveOperation.Up)
                cursor.insertText(text + "\n")
                cursor.endEditBlock()
    
    def _on_copy_line_up(self) -> None:
        """Copy current line up."""
        editor = self.current_editor
        if editor:
            cursor = editor.textCursor()
            block = cursor.block()
            text = block.text()
            cursor.beginEditBlock()
            cursor.movePosition(cursor.MoveOperation.StartOfBlock)
            cursor.insertText(text + "\n")
            cursor.endEditBlock()
    
    def _on_copy_line_down(self) -> None:
        """Copy current line down."""
        editor = self.current_editor
        if editor:
            cursor = editor.textCursor()
            block = cursor.block()
            text = block.text()
            cursor.beginEditBlock()
            cursor.movePosition(cursor.MoveOperation.EndOfBlock)
            cursor.insertText("\n" + text)
            cursor.endEditBlock()
    
    def _on_delete_line(self) -> None:
        """Delete current line."""
        editor = self.current_editor
        if editor:
            cursor = editor.textCursor()
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
    
    def _on_toggle_comment(self) -> None:
        """Toggle comment on current line or selection."""
        editor = self.current_editor
        if not editor:
            return
        
        cursor = editor.textCursor()
        
        # Get file extension to determine comment style
        tab = self._open_tabs[self._current_tab_index] if self._current_tab_index >= 0 else None
        comment_char = "#"
        if tab and tab.file_path:
            ext = Path(tab.file_path).suffix.lower()
            comment_map = {
                ".js": "//", ".ts": "//", ".jsx": "//", ".tsx": "//",
                ".c": "//", ".cpp": "//", ".h": "//", ".hpp": "//",
                ".java": "//", ".go": "//", ".rs": "//", ".swift": "//",
                ".css": "/*", ".scss": "//", ".less": "//",
                ".html": "<!--", ".xml": "<!--", ".svg": "<!--",
                ".sh": "#", ".bash": "#", ".zsh": "#",
                ".py": "#", ".rb": "#", ".yml": "#", ".yaml": "#",
                ".json": "//", ".sql": "--", ".lua": "--",
            }
            comment_char = comment_map.get(ext, "#")
        
        # Toggle based on selection or line
        if cursor.hasSelection():
            text = cursor.selectedText()
            lines = text.split('\n')
            new_lines = []
            all_commented = all(line.strip().startswith(comment_char) for line in lines if line.strip())
            
            for line in lines:
                if all_commented:
                    # Remove comment
                    if line.strip().startswith(comment_char):
                        new_lines.append(line.replace(comment_char, "", 1))
                    else:
                        new_lines.append(line)
                else:
                    # Add comment
                    new_lines.append(comment_char + " " + line)
            
            cursor.insertText('\n'.join(new_lines))
        else:
            # Single line
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            text = cursor.selectedText()
            if text.strip().startswith(comment_char):
                # Remove comment
                new_text = text.replace(comment_char, "", 1).replace("  ", " ", 1)
            else:
                # Add comment
                new_text = comment_char + " " + text
            cursor.insertText(new_text)
    
    def _on_indent(self) -> None:
        """Indent selected text."""
        editor = self.current_editor
        if editor:
            cursor = editor.textCursor()
            cursor.beginEditBlock()
            cursor.insertText("    ")
            cursor.endEditBlock()
    
    def _on_unindent(self) -> None:
        """Unindent selected text."""
        editor = self.current_editor
        if editor:
            cursor = editor.textCursor()
            cursor.beginEditBlock()
            cursor.deleteChar()
            cursor.endEditBlock()
    
    def _on_expand_emmet(self) -> None:
        """Expand Emmet abbreviation at cursor."""
        editor = self.current_editor
        if not editor:
            return
        
        cursor = editor.textCursor()
        cursor.select(cursor.LineUnderCursor)
        abbreviation = cursor.selectedText().strip()
        
        if not abbreviation:
            return
        
        expanded = self._emmet_engine.expand(abbreviation)
        
        if expanded:
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(expanded)
            cursor.endEditBlock()
    
    # File operations
    
    def _create_new_tab(self, file_path: Optional[str]) -> None:
        """Create a new editor tab."""
        # Create editor
        editor = CodeEditor()
        highlighter = SyntaxHighlighter(editor.document())
        
        # Apply saved font to new editor
        if self._config:
            font = editor.font()
            font.setFamily(self._config.editor.font_family)
            font.setPointSize(self._config.editor.font_size)
            editor.setFont(font)
        
        # Apply saved theme to new editor
        if self._config and self._config.theme.name:
            saved_theme = self._config.theme.name
            from core.editor import SyntaxHighlighter as SH
            temp_highlighter = SH()
            temp_highlighter.set_theme_by_name(saved_theme)
            theme = temp_highlighter.theme
            bg_hex = theme.background.name()
            fg_hex = theme.normal.name()
            
            highlighter.set_theme_by_name(saved_theme)
            editor.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: {bg_hex};
                    color: {fg_hex};
                }}
            """)
        
        # Create tab
        tab = EditorTab(
            file_path=file_path,
            editor=editor,
            highlighter=highlighter,
            is_modified=False
        )
        
        # Add to tab widget
        index = self._tab_widget.addTab(editor, "Untitled")
        self._open_tabs.append(tab)
        self._tab_widget.setCurrentIndex(index)
        
        # Connect editor signals
        editor.textChanged.connect(self._on_editor_text_changed)
        editor.font_size_changed.connect(self._apply_editor_font_size)
        
        self._signals.file_opened.emit(file_path or "")
    
    def _open_file(self, file_path: str) -> None:
        """Open a file in a new tab."""
        # Hide welcome screen and show tab widget
        self._welcome_screen.hide()
        self._tab_widget.show()
        
        # Update explorer path to file's directory
        self._update_explorer_path(file_path)
        
        # Check if already open
        for i, tab in enumerate(self._open_tabs):
            if tab.file_path == file_path:
                self._tab_widget.setCurrentIndex(i)
                return
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return
        
        # Create new tab
        self._create_new_tab(file_path)
        
        # Detect file type
        detector = get_detector()
        language = detector.detect(file_path, content)
        
        # Set content
        if self._current_tab_index >= 0:
            tab = self._open_tabs[self._current_tab_index]
            tab.editor.setPlainText(content)
            tab.is_modified = False
            tab.language = language
            
            # Update tab title
            name = Path(file_path).name
            self._tab_widget.setTabText(self._current_tab_index, name)
            
            # Update highlighter
            tab.highlighter.language = language
            
            # Notify LSP
            if self._lsp_client:
                self._lsp_client.did_open(
                    self._path_to_uri(file_path),
                    language,
                    content
                )
            
            # Add to recent files
            if self._config:
                self._config.add_recent_file(file_path)
                self._update_recent_files_menu()
                from core.utils.config import ConfigManager
                ConfigManager().save(self._config)
    
    def _save_file(self, file_path: str) -> bool:
        """Save the current file."""
        if self._current_tab_index < 0:
            return False
        
        tab = self._open_tabs[self._current_tab_index]
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tab.editor.toPlainText())
            
            tab.is_modified = False
            tab.file_path = file_path
            
            # Update tab title
            name = Path(file_path).name
            self._tab_widget.setTabText(self._current_tab_index, name)
            
            # Notify LSP
            if self._lsp_client:
                self._lsp_client.did_save(
                    self._path_to_uri(file_path),
                    tab.editor.toPlainText()
                )
            
            # Run linting on save
            self._run_linting(file_path)
            
            self._signals.file_saved.emit(file_path)
            return True
            
        except Exception:
            return False
    
    def _close_tab(self, index: int) -> None:
        """Close a tab."""
        if index < 0 or index >= len(self._open_tabs):
            return
        
        tab = self._open_tabs[index]
        
        # Notify LSP
        if self._lsp_client and tab.file_path:
            self._lsp_client.did_close(self._path_to_uri(tab.file_path))
        
        # Remove tab
        self._tab_widget.removeTab(index)
        self._open_tabs.pop(index)
        
        if tab.file_path:
            self._signals.file_closed.emit(tab.file_path)
    
    def _on_editor_text_changed(self) -> None:
        """Handle editor text change."""
        if self._current_tab_index >= 0:
            tab = self._open_tabs[self._current_tab_index]
            tab.is_modified = True
            
            # Track for auto-save
            if tab.file_path:
                content = tab.editor.toPlainText()
                self._auto_save_manager.track_file(tab.file_path, content, tab.is_modified)
            
            # Update tab title
            title = "Untitled"
            if tab.file_path:
                title = Path(tab.file_path).name
            if tab.is_modified:
                title += " *"
            
            self._tab_widget.setTabText(self._current_tab_index, title)
            
            # Update modified indicator
            self._update_status_bar()
            
            # Update symbol outline
            self._update_symbol_outline()
    
    def _update_symbol_outline(self) -> None:
        """Update symbol outline for current file."""
        editor = self.current_editor
        if not editor or not self._symbol_outline:
            return
        
        if self._current_tab_index >= 0:
            tab = self._open_tabs[self._current_tab_index]
            file_path = tab.file_path or "Untitled"
            content = editor.toPlainText()
            language = tab.language
            self._symbol_outline.set_content(file_path, content, language)
    
    def _on_symbol_selected(self, symbol_name: str, line: int) -> None:
        """Handle symbol selection - go to line."""
        editor = self.current_editor
        if not editor:
            return
        
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        
        for _ in range(line - 1):
            cursor.movePosition(cursor.MoveOperation.Down)
        
        editor.setTextCursor(cursor)
        editor.setFocus()
        editor.ensureCursorVisible()
    
    def _on_task_clicked(self, file_path: str, line: int) -> None:
        """Handle task click - open file and go to line."""
        self._open_file(file_path)
        
        # After opening, go to line
        editor = self.current_editor
        if editor:
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            
            for _ in range(line - 1):
                cursor.movePosition(cursor.MoveOperation.Down)
            
            editor.setTextCursor(cursor)
            editor.setFocus()
            editor.ensureCursorVisible()
    
    def _on_snippet_insert(self, name: str, content: str) -> None:
        """Handle snippet insertion."""
        editor = self.current_editor
        if not editor:
            return
        
        cursor = editor.textCursor()
        cursor.insertText(content)
        editor.setFocus()
    
    def _update_status_bar(self) -> None:
        """Update the status bar with current editor info."""
        editor = self.current_editor
        if not editor:
            self._cursor_position_label.setText("Ln 1, Col 1")
            self._language_label.setText("Plain Text")
            self._modified_label.setText("")
            self._tab_size_label.setText("Spaces: 4")
            return
        
        cursor = editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self._cursor_position_label.setText(f"Ln {line}, Col {col}")
        
        # Update language
        if self._current_tab_index >= 0:
            tab = self._open_tabs[self._current_tab_index]
            self._language_label.setText(tab.language.capitalize())
        
        # Update modified
        if self._current_tab_index >= 0:
            tab = self._open_tabs[self._current_tab_index]
            self._modified_label.setText("●" if tab.is_modified else "")
        
        # Update tab size
        tab_distance = editor.tabStopDistance()
        char_width = editor.fontMetrics().horizontalAdvance(' ')
        spaces = int(tab_distance / char_width) if char_width > 0 else 4
        self._tab_size_label.setText(f"Spaces: {spaces}")
    
    def _path_to_uri(self, path: str) -> str:
        """Convert file path to URI."""
        import urllib.parse
        return f"file://{urllib.parse.quote(path)}"
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        # Stop LSP client
        if self._lsp_client:
            self._lsp_client.stop()
        
        # Save UI state before closing
        self._save_ui_state()
        
        # Save configuration
        if self._config:
            self._config_manager.save(self._config)
        
        event.accept()
    
    def _save_ui_state(self) -> None:
        """Save UI state (window geometry, panel positions, splitter sizes)."""
        from config.state import State
        
        # Save window geometry
        window_geometry = self.saveGeometry()
        window_state = self.saveState()
        
        # Save panel positions and visibility
        panel_positions = {}
        panel_states = {}
        
        if self._explorer_dock:
            panel_positions["explorer"] = self._get_dock_area_name(self._explorer_dock)
            panel_states["explorer"] = self._explorer_dock.isVisible()
        if self._terminal_dock:
            panel_positions["terminal"] = self._get_dock_area_name(self._terminal_dock)
            panel_states["terminal"] = self._terminal_dock.isVisible()
        if self._diagnostics_dock:
            panel_positions["diagnostics"] = self._get_dock_area_name(self._diagnostics_dock)
            panel_states["diagnostics"] = self._diagnostics_dock.isVisible()
        if self._git_dock:
            panel_positions["git"] = self._get_dock_area_name(self._git_dock)
            panel_states["git"] = self._git_dock.isVisible()
        if self._ai_panel_dock:
            panel_positions["ai_panel"] = self._get_dock_area_name(self._ai_panel_dock)
            panel_states["ai_panel"] = self._ai_panel_dock.isVisible()
        
        # Save to config/state
        state = self._config_manager.load_state() if hasattr(self._config_manager, 'load_state') else None
        if not state:
            from config.state import State
            state = State()
        
        state.window_geometry = window_geometry
        state.window_state = window_state
        state.panel_positions = panel_positions
        state.panel_states = panel_states
        
        # Save state
        self._save_state(state)
    
    def _load_ui_state(self) -> None:
        """Load UI state (window geometry, panel positions, splitter sizes)."""
        from config.state import State
        
        state = self._load_state()
        if not state:
            return
        
        # Restore window geometry
        if state.window_geometry:
            self.restoreGeometry(state.window_geometry)
        
        # Restore window state (dock positions)
        if state.window_state:
            try:
                self.restoreState(state.window_state)
            except Exception:
                pass  # If state restore fails, use default layout
        
        # Restore panel visibility
        if hasattr(state, 'panel_states'):
            if self._explorer_dock and "explorer" in state.panel_states:
                self._explorer_dock.setVisible(state.panel_states["explorer"])
            if self._terminal_dock and "terminal" in state.panel_states:
                self._terminal_dock.setVisible(state.panel_states["terminal"])
            if self._diagnostics_dock and "diagnostics" in state.panel_states:
                self._diagnostics_dock.setVisible(state.panel_states["diagnostics"])
            if self._git_dock and "git" in state.panel_states:
                self._git_dock.setVisible(state.panel_states["git"])
            if "ai_panel" in state.panel_states:
                # Create AI panel if needed and restore visibility
                if self._ai_panel_dock is None:
                    self._create_ai_panel()
                self._ai_panel_dock.setVisible(state.panel_states["ai_panel"])
                self._toggle_ai_panel_action.setChecked(state.panel_states["ai_panel"])
    
    def _get_dock_area_name(self, dock: QDockWidget) -> str:
        """Get the dock area name as a string."""
        area = self.dockWidgetArea(dock)
        if area == Qt.DockWidgetArea.LeftDockWidgetArea:
            return "Left"
        elif area == Qt.DockWidgetArea.RightDockWidgetArea:
            return "Right"
        elif area == Qt.DockWidgetArea.TopDockWidgetArea:
            return "Top"
        elif area == Qt.DockWidgetArea.BottomDockWidgetArea:
            return "Bottom"
        return "Left"
    
    def _save_state(self, state) -> None:
        """Save state to file."""
        import json
        import os
        
        state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "ui_state.json")
        
        # Convert state to dict
        data = state.to_dict() if hasattr(state, 'to_dict') else {}
        
        # Handle bytes fields for JSON
        if data.get('window_geometry'):
            import base64
            data['window_geometry'] = base64.b64encode(data['window_geometry']).decode('utf-8')
        if data.get('window_state'):
            import base64
            data['window_state'] = base64.b64encode(data['window_state']).decode('utf-8')
        
        try:
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def _load_state(self):
        """Load state from file."""
        import json
        import os
        
        state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "ui_state.json")
        
        if not os.path.exists(state_file):
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle bytes fields
            if data.get('window_geometry'):
                import base64
                data['window_geometry'] = base64.b64decode(data['window_geometry'])
            if data.get('window_state'):
                import base64
                data['window_state'] = base64.b64decode(data['window_state'])
            
            from config.state import State
            return State.from_dict(data)
        except Exception:
            return None
