"""
Welcome Screen
=============
Welcome screen shown when no files are open.
"""

from typing import Optional, Callable, Dict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QFontDatabase
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem

from core.utils import icon_manager


class WelcomeScreen(QWidget):
    """
    Welcome screen widget shown when no files are open.
    """
    
    file_opened = pyqtSignal(str)
    new_file_requested = pyqtSignal()
    open_folder_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._recent_files: list[str] = []
        self._title_label = None
        self._subtitle_label = None
        self._recent_label = None
        self._new_file_btn = None
        self._open_file_btn = None
        self._open_folder_btn = None
        self._setup_ui()
    
    def set_language(self, lang: str) -> None:
        """Set language for translated text."""
        translations = self._get_translations(lang)
        self._update_text(translations)
    
    def _get_translations(self, lang: str) -> Dict[str, str]:
        """Get translations for the given language."""
        translations = {
            "en": {
                "title": "Editor ISK",
                "subtitle": "Welcome to Editor ISK 2.0",
                "new_file": "New File",
                "open_file": "Open File...",
                "open_folder": "Open Folder...",
                "recent_files": "Recent Files",
            },
            "es": {
                "title": "Editor ISK",
                "subtitle": "Bienvenido a Editor ISK 2.0",
                "new_file": "Nuevo archivo",
                "open_file": "Abrir archivo...",
                "open_folder": "Abrir carpeta...",
                "recent_files": "Archivos recientes",
            }
        }
        return translations.get(lang, translations["en"])
    
    def _update_text(self, t: Dict[str, str]) -> None:
        """Update all text elements with translations."""
        if self._title_label:
            self._title_label.setText(t.get("title", "Editor ISK"))
        if self._subtitle_label:
            self._subtitle_label.setText(t.get("subtitle", ""))
        if self._new_file_btn:
            self._new_file_btn.setText(t.get("new_file", "New File"))
        if self._open_file_btn:
            self._open_file_btn.setText(t.get("open_file", "Open File..."))
        if self._open_folder_btn:
            self._open_folder_btn.setText(t.get("open_folder", "Open Folder..."))
        if self._recent_label:
            self._recent_label.setText(t.get("recent_files", "Recent Files"))
    
    def set_theme(self, bg_color: str, fg_color: str) -> None:
        """Apply theme colors to the welcome screen."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {fg_color};
            }}
            QLabel {{
                color: {fg_color};
            }}
            QPushButton {{
                background-color: {bg_color};
                color: {fg_color};
                border: 1px solid {fg_color};
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {fg_color};
                color: {bg_color};
            }}
            QListWidget {{
                background-color: {bg_color};
                color: {fg_color};
                border: 1px solid {fg_color};
            }}
        """)
        if self._subtitle_label:
            self._subtitle_label.setStyleSheet(f"color: {fg_color}; opacity: 0.7;")
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        self._title_label = QLabel("Editor ISK")
        title_font = QFont("Sans-serif", 32, QFont.Weight.Bold)
        self._title_label.setFont(title_font)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)
        
        # Subtitle
        self._subtitle_label = QLabel("Welcome to Editor ISK 2.0")
        subtitle_font = QFont("Sans-serif", 14)
        self._subtitle_label.setFont(subtitle_font)
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_label.setStyleSheet("color: #888;")
        layout.addWidget(self._subtitle_label)
        
        layout.addSpacing(40)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # New file button
        self._new_file_btn = QPushButton("New File")
        self._new_file_btn.setMinimumWidth(120)
        self._new_file_btn.clicked.connect(self.new_file_requested.emit)
        button_layout.addWidget(self._new_file_btn)
        
        # Open file button
        self._open_file_btn = QPushButton("Open File...")
        self._open_file_btn.setMinimumWidth(120)
        self._open_file_btn.clicked.connect(self._on_open_file)
        button_layout.addWidget(self._open_file_btn)
        
        # Open folder button
        self._open_folder_btn = QPushButton("Open Folder...")
        self._open_folder_btn.setMinimumWidth(120)
        self._open_folder_btn.clicked.connect(self.open_folder_requested.emit)
        button_layout.addWidget(self._open_folder_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addSpacing(30)
        
        # Recent files section
        self._recent_label = QLabel("Recent Files")
        recent_font = QFont("Sans-serif", 12, QFont.Weight.Bold)
        self._recent_label.setFont(recent_font)
        layout.addWidget(self._recent_label)
        
        # Recent files list
        self._recent_list = QListWidget()
        self._recent_list.itemDoubleClicked.connect(self._on_recent_file_clicked)
        layout.addWidget(self._recent_list)
        
        layout.addStretch()
    
    def set_recent_files(self, files: list[str]) -> None:
        """Set recent files list."""
        self._recent_files = files
        self._update_recent_list()
    
    def _update_recent_list(self) -> None:
        """Update the recent files list."""
        self._recent_list.clear()
        for file_path in self._recent_files[:10]:
            item = QListWidgetItem(file_path)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self._recent_list.addItem(item)
    
    def _on_open_file(self) -> None:
        """Handle open file button click."""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "",
            "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            self.file_opened.emit(file_path)
    
    def _on_recent_file_clicked(self, item: QListWidgetItem) -> None:
        """Handle recent file click."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_opened.emit(file_path)


def show_welcome_screen(parent: Optional[QWidget] = None) -> WelcomeScreen:
    """Create and return a welcome screen widget."""
    return WelcomeScreen(parent)