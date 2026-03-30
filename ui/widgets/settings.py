"""
Settings Dialog Module
======================
Complete settings GUI for the editor.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QLineEdit, QCheckBox, QSpinBox, QComboBox, QPushButton,
    QGroupBox, QListWidget, QListWidgetItem, QScrollArea, QSlider,
    QFontComboBox, QColorDialog, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor


class SettingsManager:
    """
    Central settings manager for the application.
    """
    
    def __init__(self) -> None:
        self._settings: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {}
        self._init_defaults()
    
    def _init_defaults(self) -> None:
        """Initialize default settings."""
        self._defaults = {
            'editor': {
                'font_family': 'Consolas',
                'font_size': 12,
                'tab_size': 4,
                'use_spaces': True,
                'line_numbers': True,
                'word_wrap': False,
                'auto_indent': True,
                'bracket_matching': True,
                'auto_complete': True,
                'highlight_current_line': True,
                'show_whitespace': False,
                'show_end_of_line': False,
                'auto_save': True,
                'auto_save_interval': 300,
            },
            'appearance': {
                'theme': 'Dark Modern',
                'ui_scale': 1.0,
                'sidebar_width': 250,
                'terminal_height': 200,
            },
            'shortcuts': {},
            'lsp': {
                'enabled': True,
                'server_command': 'pylsp',
                'check_on_save': True,
                'check_on_type': False,
            },
            'ai': {
                'provider': 'Ollama',
                'model': 'llama3.2',
                'base_url': 'http://localhost:11434',
                'temperature': 0.7,
                'max_tokens': 4096,
                'system_prompt': 'Eres un asistente de programación útil.',
            },
            'files': {
                'default_language': 'Python',
                'auto_detect_language': True,
                'encoding': 'utf-8',
                'new_file_extension': '.py',
            },
            'terminal': {
                'shell': '/bin/bash',
                'python_path': 'python3',
                'cursor_style': 'block',
            }
        }
        self._settings = self._defaults.copy()
    
    def get(self, category: str, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        cat = self._settings.get(category, {})
        return cat.get(key, default)
    
    def set(self, category: str, key: str, value: Any) -> None:
        """Set a setting value."""
        if category not in self._settings:
            self._settings[category] = {}
        self._settings[category][key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()
    
    def reset(self) -> None:
        """Reset all settings to defaults."""
        self._settings = self._defaults.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export settings to dictionary."""
        return self._settings.copy()
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Import settings from dictionary."""
        self._settings.update(data)


class SettingsDialog(QDialog):
    """
    Complete settings dialog with multiple categories.
    """
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent: Optional[QWidget] = None, language: str = "es", config = None) -> None:
        super().__init__(parent)
        
        self._language = language
        self._manager = SettingsManager()
        self._config = config
        if config:
            self._load_from_config()
        self._setup_ui()
        self._load_settings()
    
    def _load_from_config(self) -> None:
        """Load settings from main config."""
        if not self._config:
            return
        self._manager.set('editor', 'font_family', self._config.editor.font_family)
        self._manager.set('editor', 'font_size', self._config.editor.font_size)
        self._manager.set('appearance', 'theme', self._config.theme.name)
    
    def _get_text(self, key: str) -> str:
        """Get translated text."""
        translations = {
            "es": {
                "settings": "Configuración",
                "editor": "Editor",
                "appearance": "Apariencia",
                "shortcuts": "Atajos",
                "language_server": "Servidor de lenguaje",
                "ai_assistant": "Asistente IA",
                "files": "Archivos",
                "terminal": "Terminal",
                "advanced": "Avanzado",
                # Editor settings
                "font_settings": "Fuente",
                "font": "Fuente",
                "tabs": "Tabulación",
                "tab_size": "Tamaño de tab",
                "use_spaces": "Usar espacios en lugar de tabs",
                "display": "Visualización",
                "line_numbers": "Números de línea",
                "show_line_numbers": "Mostrar números de línea",
                "minimap": "Minimapa",
                "show_minimap": "Mostrar minimapa",
                "highlight_line": "Línea actual",
                "highlight_current_line": "Resaltar línea actual",
                "whitespace": "Espacios",
                "show_whitespace": "Mostrar espacios en blanco",
                "eol": "Fin de línea",
                "show_eol": "Mostrar caracteres de fin de línea",
                "right_margin": "Margen derecho",
                "show_right_margin": "Mostrar margen derecho",
                "column": "Columna",
                "word_wrap": "Ajuste de línea",
                "enable_word_wrap": "Habilitar ajuste de línea",
                "behavior": "Comportamiento",
                "smart_home": "Inicio inteligente",
                "auto_indent": "Sangría automática",
                "bracket": "Paréntesis",
                "bracket_matching": "Resaltar paréntesis",
                "colorization": "Colorización",
                "bracket_colorization": "Colorización de paréntesis",
                "completion": "Autocompletado",
                "auto_complete": "Autocompletado automático",
                "line_ending": "Salto de línea",
                "encoding": "Codificación",
                "auto_save": "Guardado automático",
                "enable_auto_save": "Habilitar guardado automático",
                "interval": "Intervalo",
                "seconds": "segundos",
                # Advanced
                "toolbar_settings": "Barras de herramientas",
                "show_toolbar": "Mostrar",
                "advanced": "Avanzado",
                "performance": "Rendimiento",
                "reset_defaults": "Restablecer valores predeterminados",
            },
            "en": {
                "settings": "Settings",
                "editor": "Editor",
                "appearance": "Appearance",
                "shortcuts": "Shortcuts",
                "language_server": "Language Server",
                "ai_assistant": "AI Assistant",
                "files": "Files",
                "terminal": "Terminal",
                "advanced": "Advanced",
                # Editor settings
                "font_settings": "Font",
                "font": "Font",
                "tabs": "Indentation",
                "tab_size": "Tab size",
                "use_spaces": "Use spaces instead of tabs",
                "display": "Display",
                "line_numbers": "Line Numbers",
                "show_line_numbers": "Show line numbers",
                "minimap": "Minimap",
                "show_minimap": "Show minimap",
                "highlight_line": "Current Line",
                "highlight_current_line": "Highlight current line",
                "whitespace": "Whitespace",
                "show_whitespace": "Show whitespace characters",
                "eol": "End of Line",
                "show_eol": "Show end of line characters",
                "right_margin": "Right Margin",
                "show_right_margin": "Show right margin",
                "column": "Column",
                "word_wrap": "Word Wrap",
                "enable_word_wrap": "Enable word wrap",
                "behavior": "Behavior",
                "smart_home": "Smart home",
                "auto_indent": "Auto indent",
                "bracket": "Brackets",
                "bracket_matching": "Bracket matching",
                "colorization": "Colorization",
                "bracket_colorization": "Bracket colorization",
                "completion": "Completion",
                "auto_complete": "Auto completion",
                "line_ending": "Line Ending",
                "encoding": "Encoding",
                "auto_save": "Auto Save",
                "enable_auto_save": "Enable auto save",
                "interval": "Interval",
                "seconds": "seconds",
                # Advanced
                "toolbar_settings": "Toolbars",
                "show_toolbar": "Show",
                "performance": "Performance",
                "reset_defaults": "Reset to Defaults",
            }
        }
        return translations.get(self._language, translations["en"]).get(key, key)
    
    def _setup_ui(self) -> None:
        """Setup the settings UI."""
        self.setWindowTitle(self._get_text("settings"))
        self.setMinimumSize(800, 550)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left sidebar - categories with icons
        self._category_list = QListWidget()
        self._category_list.setObjectName("categoryList")
        self._category_list.setMaximumWidth(200)
        
        categories = [
            ("editor", "Editor"),
            ("appearance", "Apariencia"),
            ("shortcuts", "Atajos"),
            ("language_server", "Servidor LSP"),
            ("ai_assistant", "Asistente IA"),
            ("files", "Archivos"),
            ("terminal", "Terminal"),
            ("advanced", "Avanzado"),
        ]
        
        if self._language == "en":
            categories = [
                ("editor", "Editor"),
                ("appearance", "Appearance"),
                ("shortcuts", "Shortcuts"),
                ("language_server", "Language Server"),
                ("ai_assistant", "AI Assistant"),
                ("files", "Files"),
                ("terminal", "Terminal"),
                ("advanced", "Advanced"),
            ]
        
        for cat_id, cat_name in categories:
            item = QListWidgetItem(cat_name)
            item.setData(Qt.ItemDataRole.UserRole, cat_id)
            self._category_list.addItem(item)
        
        self._category_list.currentRowChanged.connect(self._on_category_changed)
        self._category_list.setCurrentRow(0)
        layout.addWidget(self._category_list)
        
        # Right side - settings panels
        self._stack = QStackedWidget()
        
        # Add panels
        self._stack.addWidget(self._create_editor_panel())
        self._stack.addWidget(self._create_appearance_panel())
        self._stack.addWidget(self._create_shortcuts_panel())
        self._stack.addWidget(self._create_lsp_panel())
        self._stack.addWidget(self._create_ai_panel())
        self._stack.addWidget(self._create_files_panel())
        self._stack.addWidget(self._create_terminal_panel())
        self._stack.addWidget(self._create_advanced_panel())
        
        layout.addWidget(self._stack)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)
    
    def _create_editor_panel(self) -> QWidget:
        """Create editor settings panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Font group
        font_group = QGroupBox(self._get_text("font_settings"))
        font_form = QFormLayout(font_group)
        
        font_layout = QHBoxLayout()
        self._font_combo = QFontComboBox()
        self._font_combo.setCurrentText("Consolas")
        font_layout.addWidget(self._font_combo)
        
        self._font_size = QSpinBox()
        self._font_size.setRange(8, 72)
        self._font_size.setValue(12)
        font_layout.addWidget(self._font_size)
        font_form.addRow(self._get_text("font") + ":", font_layout)
        
        scroll_layout.addWidget(font_group)
        
        # Tabs group
        tabs_group = QGroupBox(self._get_text("tabs"))
        tabs_form = QFormLayout(tabs_group)
        
        self._tab_size = QSpinBox()
        self._tab_size.setRange(1, 8)
        self._tab_size.setValue(4)
        tabs_form.addRow(self._get_text("tab_size") + ":", self._tab_size)
        
        self._use_spaces = QCheckBox(self._get_text("use_spaces"))
        self._use_spaces.setChecked(True)
        tabs_form.addRow("", self._use_spaces)
        
        scroll_layout.addWidget(tabs_group)
        
        # Display group
        display_group = QGroupBox(self._get_text("display"))
        display_form = QFormLayout(display_group)
        
        self._line_numbers = QCheckBox(self._get_text("show_line_numbers"))
        self._line_numbers.setChecked(True)
        display_form.addRow(self._get_text("line_numbers") + ":", self._line_numbers)
        
        self._minimap = QCheckBox(self._get_text("show_minimap"))
        self._minimap.setChecked(True)
        display_form.addRow(self._get_text("minimap") + ":", self._minimap)
        
        self._highlight_line = QCheckBox(self._get_text("highlight_current_line"))
        self._highlight_line.setChecked(True)
        display_form.addRow(self._get_text("highlight_line") + ":", self._highlight_line)
        
        self._show_whitespace = QCheckBox(self._get_text("show_whitespace"))
        display_form.addRow(self._get_text("whitespace") + ":", self._show_whitespace)
        
        self._show_end_of_line = QCheckBox(self._get_text("show_eol"))
        display_form.addRow(self._get_text("eol") + ":", self._show_end_of_line)
        
        right_margin_layout = QHBoxLayout()
        self._show_right_margin = QCheckBox(self._get_text("show_right_margin"))
        right_margin_layout.addWidget(self._show_right_margin)
        
        self._right_margin_column = QSpinBox()
        self._right_margin_column.setRange(40, 200)
        self._right_margin_column.setValue(80)
        right_margin_layout.addWidget(QLabel(self._get_text("column") + ":"))
        right_margin_layout.addWidget(self._right_margin_column)
        right_margin_layout.addStretch()
        display_form.addRow(self._get_text("right_margin") + ":", right_margin_layout)
        
        self._word_wrap = QCheckBox(self._get_text("enable_word_wrap"))
        display_form.addRow(self._get_text("word_wrap") + ":", self._word_wrap)
        
        scroll_layout.addWidget(display_group)
        
        # Behavior group
        behavior_group = QGroupBox(self._get_text("behavior"))
        behavior_form = QFormLayout(behavior_group)
        
        self._auto_indent = QCheckBox(self._get_text("auto_indent"))
        self._auto_indent.setChecked(True)
        behavior_form.addRow(self._get_text("auto_indent") + ":", self._auto_indent)
        
        self._smart_home = QCheckBox(self._get_text("smart_home"))
        self._smart_home.setChecked(True)
        behavior_form.addRow(self._get_text("smart_home") + ":", self._smart_home)
        
        self._bracket_matching = QCheckBox(self._get_text("bracket_matching"))
        self._bracket_matching.setChecked(True)
        behavior_form.addRow(self._get_text("bracket") + ":", self._bracket_matching)
        
        self._bracket_colorization = QCheckBox(self._get_text("bracket_colorization"))
        self._bracket_colorization.setChecked(True)
        behavior_form.addRow(self._get_text("colorization") + ":", self._bracket_colorization)
        
        self._auto_complete = QCheckBox(self._get_text("auto_complete"))
        self._auto_complete.setChecked(True)
        behavior_form.addRow(self._get_text("completion") + ":", self._auto_complete)
        
        scroll_layout.addWidget(behavior_group)
        
        # Files group
        files_group = QGroupBox(self._get_text("files"))
        files_form = QFormLayout(files_group)
        
        self._line_ending = QComboBox()
        self._line_ending.addItems(["LF (\\n)", "CRLF (\\r\\n)", "CR (\\r)"])
        files_form.addRow(self._get_text("line_ending") + ":", self._line_ending)
        
        self._default_encoding = QComboBox()
        self._default_encoding.addItems(["UTF-8", "UTF-16", "ISO-8859-1", "Windows-1252", "ASCII"])
        files_form.addRow(self._get_text("encoding") + ":", self._default_encoding)
        
        scroll_layout.addWidget(files_group)
        
        # Auto-save group
        save_group = QGroupBox(self._get_text("auto_save"))
        save_form = QFormLayout(save_group)
        
        self._auto_save = QCheckBox(self._get_text("enable_auto_save"))
        self._auto_save.setChecked(True)
        save_form.addRow("", self._auto_save)
        
        self._auto_save_interval = QSpinBox()
        self._auto_save_interval.setRange(10, 600)
        self._auto_save_interval.setValue(300)
        self._auto_save_interval.setSuffix(" " + self._get_text("seconds"))
        save_form.addRow(self._get_text("interval") + ":", self._auto_save_interval)
        
        scroll_layout.addWidget(save_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_appearance_panel(self) -> QWidget:
        """Create appearance settings panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Theme Selection
        theme_group = QGroupBox("Tema del Editor")
        theme_form = QFormLayout(theme_group)
        
        self._theme_combo = QComboBox()
        # Load themes from config (includes Default Dark + all .tpl files)
        from core.utils.config import ThemeConfig
        theme_config = ThemeConfig()
        self._theme_combo.addItems(theme_config.available_themes)
        theme_form.addRow("Tema:", self._theme_combo)
        
        scroll_layout.addWidget(theme_group)
        
        # Font Settings
        font_group = QGroupBox("Fuente")
        font_form = QFormLayout(font_group)
        
        font_layout = QHBoxLayout()
        self._font_combo = QFontComboBox()
        self._font_combo.setCurrentText("Consolas")
        font_layout.addWidget(self._font_combo)
        
        self._font_size = QSpinBox()
        self._font_size.setRange(8, 72)
        self._font_size.setValue(12)
        font_layout.addWidget(self._font_size)
        
        font_form.addRow("Familia y tamaño:", font_layout)
        
        self._font_smooth = QCheckBox("Suavizado de fuente")
        self._font_smooth.setChecked(True)
        font_form.addRow("Opciones:", self._font_smooth)
        
        scroll_layout.addWidget(font_group)
        
        # Interface
        interface_group = QGroupBox("Interfaz")
        interface_form = QFormLayout(interface_group)
        
        self._show_minimap = QCheckBox("Mostrar minimapa")
        self._show_minimap.setChecked(True)
        interface_form.addRow(" Minimapa:", self._show_minimap)
        
        self._show_line_numbers = QCheckBox("Mostrar números de línea")
        self._show_line_numbers.setChecked(True)
        interface_form.addRow(" Números de línea:", self._show_line_numbers)
        
        self._show_whitespace = QCheckBox("Mostrar espacios en blanco")
        self._show_whitespace.setChecked(False)
        interface_form.addRow(" Espacios:", self._show_whitespace)
        
        self._show_end_line = QCheckBox("Mostrar indicadores de fin de línea")
        self._show_end_line.setChecked(False)
        interface_form.addRow(" Fin de línea:", self._show_end_line)
        
        self._show_indent_guides = QCheckBox("Mostrar guías de indentación")
        self._show_indent_guides.setChecked(True)
        interface_form.addRow(" Guías:", self._show_indent_guides)
        
        self._highlight_current_line = QCheckBox("Resaltar línea actual")
        self._highlight_current_line.setChecked(True)
        interface_form.addRow(" Línea actual:", self._highlight_current_line)
        
        self._highlight_matching_brackets = QCheckBox("Resaltar paréntesis coincidentes")
        self._highlight_matching_brackets.setChecked(True)
        interface_form.addRow(" Paréntesis:", self._highlight_matching_brackets)
        
        scroll_layout.addWidget(interface_group)
        
        # Cursor
        cursor_group = QGroupBox("Cursor")
        cursor_form = QFormLayout(cursor_group)
        
        self._cursor_width = QSpinBox()
        self._cursor_width.setRange(1, 10)
        self._cursor_width.setValue(2)
        cursor_form.addRow("Ancho del cursor:", self._cursor_width)
        
        self._cursor_blink = QCheckBox("Parpadeo del cursor")
        self._cursor_blink.setChecked(True)
        cursor_form.addRow(" Animación:", self._cursor_blink)
        
        self._cursor_style = QComboBox()
        self._cursor_style.addItems(["Bloque", "Línea", "Subrayado"])
        cursor_form.addRow("Estilo:", self._cursor_style)
        
        scroll_layout.addWidget(cursor_group)
        
        # Scroll
        scroll_group = QGroupBox("Barras de desplazamiento")
        scroll_form = QFormLayout(scroll_group)
        
        self._scroll_past_end = QCheckBox("Permitir desplazamiento más allá del final")
        self._scroll_past_end.setChecked(True)
        scroll_form.addRow(" Vertical:", self._scroll_past_end)
        
        self._smooth_scrolling = QCheckBox("Desplazamiento suave")
        self._smooth_scrolling.setChecked(True)
        scroll_form.addRow(" Suavizado:", self._smooth_scrolling)
        
        scroll_layout.addWidget(scroll_group)
        
        # Colors (Basic)
        colors_group = QGroupBox("Colores")
        colors_form = QFormLayout(colors_group)
        
        self._bg_color_btn = QPushButton("Elegir...")
        self._bg_color_btn.setStyleSheet("background-color: #1E1E1E; padding: 4px;")
        colors_form.addRow("Fondo:", self._bg_color_btn)
        
        self._fg_color_btn = QPushButton("Elegir...")
        self._fg_color_btn.setStyleSheet("background-color: #D4D4D4; padding: 4px;")
        colors_form.addRow("Texto:", self._fg_color_btn)
        
        self._selection_color_btn = QPushButton("Elegir...")
        self._selection_color_btn.setStyleSheet("background-color: #264F78; padding: 4px;")
        colors_form.addRow("Selección:", self._selection_color_btn)
        
        self._line_highlight_btn = QPushButton("Elegir...")
        self._line_highlight_btn.setStyleSheet("background-color: #2D2D2D; padding: 4px;")
        colors_form.addRow("Línea actual:", self._line_highlight_btn)
        
        scroll_layout.addWidget(colors_group)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_shortcuts_panel(self) -> QWidget:
        """Create keyboard shortcuts panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Keyboard shortcuts can be customized in the shortcuts module.")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        group = QGroupBox("Quick Actions")
        form = QFormLayout(group)
        
        form.addRow("Find:", QLabel("Ctrl+F"))
        form.addRow("Replace:", QLabel("Ctrl+H"))
        form.addRow("Go to Line:", QLabel("Ctrl+G"))
        form.addRow("New File:", QLabel("Ctrl+N"))
        form.addRow("Open File:", QLabel("Ctrl+O"))
        form.addRow("Save:", QLabel("Ctrl+S"))
        form.addRow("Close:", QLabel("Ctrl+W"))
        form.addRow("Quit:", QLabel("Ctrl+Q"))
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
    
    def _create_lsp_panel(self) -> QWidget:
        """Create LSP settings panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Language Server Protocol")
        form = QFormLayout(group)
        
        self._lsp_enabled = QCheckBox("Enable LSP")
        self._lsp_enabled.setChecked(True)
        form.addRow("Enabled:", self._lsp_enabled)
        
        self._lsp_server = QLineEdit("pylsp")
        form.addRow("Server Command:", self._lsp_server)
        
        self._check_on_save = QCheckBox("Check on save")
        self._check_on_save.setChecked(True)
        form.addRow("Diagnostics:", self._check_on_save)
        
        self._check_on_type = QCheckBox("Check on type")
        form.addRow("", self._check_on_type)
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
    
    def _create_ai_panel(self) -> QWidget:
        """Create AI settings panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("AI Assistant")
        form = QFormLayout(group)
        
        self._ai_provider = QComboBox()
        self._ai_provider.addItems(["Ollama", "OpenAI", "LM Studio", "OAI Compatible"])
        form.addRow("Provider:", self._ai_provider)
        
        self._ai_model = QLineEdit("llama3.2")
        form.addRow("Model:", self._ai_model)
        
        self._ai_url = QLineEdit("http://localhost:11434")
        form.addRow("Base URL:", self._ai_url)
        
        self._ai_temperature = QSlider(Qt.Orientation.Horizontal)
        self._ai_temperature.setRange(0, 100)
        self._ai_temperature.setValue(70)
        form.addRow("Temperature:", self._ai_temperature)
        
        self._ai_max_tokens = QSpinBox()
        self._ai_max_tokens.setRange(100, 8192)
        self._ai_max_tokens.setValue(4096)
        form.addRow("Max Tokens:", self._ai_max_tokens)
        
        layout.addWidget(group)
        
        group2 = QGroupBox("System Prompt")
        prompt_edit = QTextEdit("Eres un asistente de programación útil.")
        prompt_edit.setMaximumHeight(100)
        group2.layout().addWidget(prompt_edit)
        layout.addWidget(group2)
        
        layout.addStretch()
        return widget
    
    def _create_files_panel(self) -> QWidget:
        """Create files settings panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("File Settings")
        form = QFormLayout(group)
        
        self._default_lang = QComboBox()
        self._default_lang.addItems(["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust"])
        form.addRow("Default Language:", self._default_lang)
        
        self._auto_detect = QCheckBox("Auto detect language from extension")
        self._auto_detect.setChecked(True)
        form.addRow("", self._auto_detect)
        
        self._encoding = QComboBox()
        self._encoding.addItems(["UTF-8", "UTF-16", "ASCII", "ISO-8859-1"])
        self._encoding.setCurrentText("UTF-8")
        form.addRow("Default Encoding:", self._encoding)
        
        self._new_ext = QLineEdit(".py")
        form.addRow("New File Extension:", self._new_ext)
        
        layout.addWidget(group)
        layout.addStretch()
        return widget
    
    def _create_terminal_panel(self) -> QWidget:
        """Create terminal settings panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Terminal")
        form = QFormLayout(group)
        
        self._shell = QLineEdit("/bin/bash")
        form.addRow("Shell:", self._shell)
        
        self._python_path = QLineEdit("python3")
        form.addRow("Python Path:", self._python_path)
        
        cursor_style = QComboBox()
        cursor_style.addItems(["Block", "Underline", "I-Beam"])
        form.addRow("Cursor Style:", cursor_style)
        
        layout.addWidget(group)
        
        group2 = QGroupBox("Execution")
        form2 = QFormLayout(group2)
        
        form2.addRow("Run Key:", QLabel("F5"))
        form2.addRow("Stop Key:", QLabel("Shift+F5"))
        
        layout.addWidget(group2)
        layout.addStretch()
        return widget
    
    def _create_advanced_panel(self) -> QWidget:
        """Create advanced settings panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Toolbar settings
        toolbar_group = QGroupBox(self._get_text("toolbar_settings"))
        toolbar_form = QFormLayout(toolbar_group)
        
        self._show_file_toolbar = QCheckBox(self._get_text("show_toolbar"))
        self._show_file_toolbar.setChecked(True)
        toolbar_form.addRow("Archivo:", self._show_file_toolbar)
        
        self._show_edit_toolbar = QCheckBox(self._get_text("show_toolbar"))
        self._show_edit_toolbar.setChecked(True)
        toolbar_form.addRow("Editar:", self._show_edit_toolbar)
        
        self._show_search_toolbar = QCheckBox(self._get_text("show_toolbar"))
        self._show_search_toolbar.setChecked(True)
        toolbar_form.addRow("Buscar:", self._show_search_toolbar)
        
        self._show_view_toolbar = QCheckBox(self._get_text("show_toolbar"))
        self._show_view_toolbar.setChecked(True)
        toolbar_form.addRow("Ver:", self._show_view_toolbar)
        
        self._show_run_toolbar = QCheckBox(self._get_text("show_toolbar"))
        self._show_run_toolbar.setChecked(True)
        toolbar_form.addRow("Ejecutar:", self._show_run_toolbar)
        
        self._show_code_toolbar = QCheckBox(self._get_text("show_toolbar"))
        self._show_code_toolbar.setChecked(True)
        toolbar_form.addRow("Código:", self._show_code_toolbar)
        
        scroll_layout.addWidget(toolbar_group)
        
        # Advanced info
        group = QGroupBox(self._get_text("advanced"))
        form = QFormLayout(group)
        
        form.addRow("Config File:", QLabel("~/.editor_isk/config.json"))
        form.addRow("Cache Dir:", QLabel("~/.editor_isk/cache/"))
        
        reset_btn = QPushButton(self._get_text("reset_defaults"))
        reset_btn.clicked.connect(self._on_reset_settings)
        form.addRow("", reset_btn)
        
        scroll_layout.addWidget(group)
        
        group2 = QGroupBox(self._get_text("performance"))
        form2 = QFormLayout(group2)
        
        form2.addRow("Max File Size:", QLabel("10 MB"))
        form2.addRow("Undo History:", QLabel("Unlimited"))
        
        scroll_layout.addWidget(group2)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _on_reset_settings(self) -> None:
        """Reset all settings to defaults."""
        self._manager.reset()
        self._load_settings()
    
    def _on_category_changed(self, index: int) -> None:
        """Handle category selection."""
        self._stack.setCurrentIndex(index)
    
    def _load_settings(self) -> None:
        """Load current settings into UI."""
        settings = self._manager.get_all()
        
        # Editor
        editor = settings.get('editor', {})
        self._font_combo.setCurrentText(editor.get('font_family', 'Consolas'))
        self._font_size.setValue(editor.get('font_size', 12))
        self._tab_size.setValue(editor.get('tab_size', 4))
        self._use_spaces.setChecked(editor.get('use_spaces', True))
        self._line_numbers.setChecked(editor.get('line_numbers', True))
        self._minimap.setChecked(editor.get('show_minimap', True))
        self._highlight_line.setChecked(editor.get('highlight_current_line', True))
        self._show_whitespace.setChecked(editor.get('show_whitespace', False))
        self._show_end_of_line.setChecked(editor.get('show_end_of_line', False))
        self._show_right_margin.setChecked(editor.get('show_right_margin', False))
        self._right_margin_column.setValue(editor.get('right_margin_column', 80))
        self._word_wrap.setChecked(editor.get('word_wrap', False))
        self._auto_indent.setChecked(editor.get('auto_indent', True))
        self._smart_home.setChecked(editor.get('smart_home', True))
        self._bracket_matching.setChecked(editor.get('bracket_matching', True))
        self._bracket_colorization.setChecked(editor.get('bracket_colorization', True))
        self._auto_complete.setChecked(editor.get('auto_complete', True))
        
        line_ending = editor.get('line_ending', 'LF')
        line_ending_map = {'LF': 0, 'CRLF': 1, 'CR': 2}
        self._line_ending.setCurrentIndex(line_ending_map.get(line_ending, 0))
        
        encoding = editor.get('default_encoding', 'UTF-8')
        encoding_map = {'UTF-8': 0, 'UTF-16': 1, 'ISO-8859-1': 2, 'Windows-1252': 3, 'ASCII': 4}
        self._default_encoding.setCurrentIndex(encoding_map.get(encoding, 0))
        
        self._auto_save.setChecked(editor.get('auto_save', True))
        self._auto_save_interval.setValue(editor.get('auto_save_interval', 300))
        
        # Advanced - Toolbars
        advanced = settings.get('advanced', {})
        self._show_file_toolbar.setChecked(advanced.get('show_file_toolbar', True))
        self._show_edit_toolbar.setChecked(advanced.get('show_edit_toolbar', True))
        self._show_search_toolbar.setChecked(advanced.get('show_search_toolbar', True))
        self._show_view_toolbar.setChecked(advanced.get('show_view_toolbar', True))
        self._show_run_toolbar.setChecked(advanced.get('show_run_toolbar', True))
        self._show_code_toolbar.setChecked(advanced.get('show_code_toolbar', True))
        
        # Appearance - Theme
        appearance = settings.get('appearance', {})
        theme_name = appearance.get('theme', 'Default Dark')
        if self._theme_combo.findText(theme_name) >= 0:
            self._theme_combo.setCurrentText(theme_name)
    
    def _on_accept(self) -> None:
        """Handle accept button."""
        self._save_settings()
        self.accept()
    
    def _on_apply(self) -> None:
        """Handle apply button."""
        self._save_settings()
        self.settings_changed.emit(self._manager.get_all())
    
    def _save_settings(self) -> None:
        """Save UI values to settings manager."""
        # Editor - Font
        self._manager.set('editor', 'font_family', self._font_combo.currentText())
        self._manager.set('editor', 'font_size', self._font_size.value())
        
        # Editor - Tabs
        self._manager.set('editor', 'tab_size', self._tab_size.value())
        self._manager.set('editor', 'use_spaces', self._use_spaces.isChecked())
        
        # Editor - Display
        self._manager.set('editor', 'line_numbers', self._line_numbers.isChecked())
        self._manager.set('editor', 'show_minimap', self._minimap.isChecked())
        self._manager.set('editor', 'highlight_current_line', self._highlight_line.isChecked())
        self._manager.set('editor', 'show_whitespace', self._show_whitespace.isChecked())
        self._manager.set('editor', 'show_end_of_line', self._show_end_of_line.isChecked())
        self._manager.set('editor', 'show_right_margin', self._show_right_margin.isChecked())
        self._manager.set('editor', 'right_margin_column', self._right_margin_column.value())
        self._manager.set('editor', 'word_wrap', self._word_wrap.isChecked())
        
        # Editor - Behavior
        self._manager.set('editor', 'auto_indent', self._auto_indent.isChecked())
        self._manager.set('editor', 'smart_home', self._smart_home.isChecked())
        self._manager.set('editor', 'bracket_matching', self._bracket_matching.isChecked())
        self._manager.set('editor', 'bracket_colorization', self._bracket_colorization.isChecked())
        self._manager.set('editor', 'auto_complete', self._auto_complete.isChecked())
        
        # Editor - Files
        line_ending_values = ['LF', 'CRLF', 'CR']
        self._manager.set('editor', 'line_ending', line_ending_values[self._line_ending.currentIndex()])
        
        encoding_values = ['UTF-8', 'UTF-16', 'ISO-8859-1', 'Windows-1252', 'ASCII']
        self._manager.set('editor', 'default_encoding', encoding_values[self._default_encoding.currentIndex()])
        
        # Editor - Auto save
        self._manager.set('editor', 'auto_save', self._auto_save.isChecked())
        self._manager.set('editor', 'auto_save_interval', self._auto_save_interval.value())
        
        # Appearance
        self._manager.set('appearance', 'theme', self._theme_combo.currentText())
        
        # LSP
        self._manager.set('lsp', 'enabled', self._lsp_enabled.isChecked())
        self._manager.set('lsp', 'server_command', self._lsp_server.text())
        self._manager.set('lsp', 'check_on_save', self._check_on_save.isChecked())
        self._manager.set('lsp', 'check_on_type', self._check_on_type.isChecked())
        
        # AI
        self._manager.set('ai', 'provider', self._ai_provider.currentText())
        self._manager.set('ai', 'model', self._ai_model.text())
        self._manager.set('ai', 'base_url', self._ai_url.text())
        
        # Files
        self._manager.set('files', 'default_language', self._default_lang.currentText())
        self._manager.set('files', 'auto_detect_language', self._auto_detect.isChecked())
        self._manager.set('files', 'encoding', self._encoding.currentText())
        self._manager.set('files', 'new_file_extension', self._new_ext.text())
        
        # Terminal
        self._manager.set('terminal', 'shell', self._shell.text())
        self._manager.set('terminal', 'python_path', self._python_path.text())
        
        # Advanced - Toolbars
        self._manager.set('advanced', 'show_file_toolbar', self._show_file_toolbar.isChecked())
        self._manager.set('advanced', 'show_edit_toolbar', self._show_edit_toolbar.isChecked())
        self._manager.set('advanced', 'show_search_toolbar', self._show_search_toolbar.isChecked())
        self._manager.set('advanced', 'show_view_toolbar', self._show_view_toolbar.isChecked())
        self._manager.set('advanced', 'show_run_toolbar', self._show_run_toolbar.isChecked())
        self._manager.set('advanced', 'show_code_toolbar', self._show_code_toolbar.isChecked())


def show_settings_dialog(parent: Optional[QWidget] = None) -> Optional[dict]:
    """Show the settings dialog and return the new settings."""
    dialog = SettingsDialog(parent)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog._manager.get_all()
    
    return None