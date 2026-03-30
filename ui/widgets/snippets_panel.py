"""
Snippets Panel Widget
=====================
Panel widget to display and manage code snippets.
"""

from typing import Optional, List, Dict, Any, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QListWidgetItem, QPushButton, QLabel, QLineEdit,
                            QComboBox, QTextEdit, QDialog, QDialogButtonBox,
                            QFormLayout, QMessageBox)
from PyQt6.QtGui import QFont


class SnippetsPanel(QWidget):
    """
    Panel to display and manage code snippets.
    """
    
    snippet_selected = pyqtSignal(str, str)  # name, content
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._snippets: Dict[str, str] = {}
        self._filtered_snippets: List[str] = []
        self._lang = "es"  # Default language
        
        self._setup_ui()
        self._load_default_snippets()
    
    def set_language(self, lang: str) -> None:
        """Set the panel language."""
        self._lang = lang
        self._update_ui_text()
    
    def _update_ui_text(self) -> None:
        """Update UI text based on language."""
        translations = {
            "es": {
                "title": "Fragmentos",
                "add": "Añadir",
                "search": "Buscar fragmentos...",
                "preview": "Vista previa:",
                "insert": "Insertar",
                "edit": "Editar",
                "delete": "Eliminar",
                "add_title": "Añadir Fragmento",
                "edit_title": "Editar Fragmento",
                "name": "Nombre:",
                "trigger": "Disparador:",
                "content": "Contenido:",
                "save": "Guardar",
                "cancel": "Cancelar",
                "confirm_delete": "¿Eliminar fragmento?",
                "no_snippets": "No hay fragmentos",
            },
            "en": {
                "title": "Snippets",
                "add": "Add",
                "search": "Search snippets...",
                "preview": "Preview:",
                "insert": "Insert",
                "edit": "Edit",
                "delete": "Delete",
                "add_title": "Add Snippet",
                "edit_title": "Edit Snippet",
                "name": "Name:",
                "trigger": "Trigger:",
                "content": "Content:",
                "save": "Save",
                "cancel": "Cancel",
                "confirm_delete": "Delete snippet?",
                "no_snippets": "No snippets",
            }
        }
        
        t = translations.get(self._lang, translations["en"])
        
        # Update title label
        if hasattr(self, '_title_label'):
            self._title_label.setText(t["title"])
        
        # Update add button
        if hasattr(self, '_add_btn'):
            self._add_btn.setToolTip(t["add"])
        
        # Update search placeholder
        if hasattr(self, '_search_input'):
            self._search_input.setPlaceholderText(t["search"])
        
        # Update preview label
        if hasattr(self, '_preview_label'):
            self._preview_label.setText(t["preview"])
        
        # Update buttons
        if hasattr(self, '_insert_btn'):
            self._insert_btn.setText(t["insert"])
        if hasattr(self, '_edit_btn'):
            self._edit_btn.setText(t["edit"])
        if hasattr(self, '_delete_btn'):
            self._delete_btn.setText(t["delete"])
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        translations = {
            "es": {"title": "Fragmentos", "add": "Añadir", "search": "Buscar fragmentos...", 
                   "preview": "Vista previa:", "insert": "Insertar", "edit": "Editar", "delete": "Eliminar"},
            "en": {"title": "Snippets", "add": "Add", "search": "Search snippets...",
                  "preview": "Preview:", "insert": "Insert", "edit": "Edit", "delete": "Delete"}
        }
        t = translations.get(self._lang, translations["es"])
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Header
        header_layout = QHBoxLayout()
        
        self._title_label = QLabel(t["title"])
        self._title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self._title_label)
        
        header_layout.addStretch()
        
        self._add_btn = QPushButton("+")
        self._add_btn.setMaximumWidth(25)
        self._add_btn.setToolTip(t["add"])
        self._add_btn.clicked.connect(self._on_add_snippet)
        header_layout.addWidget(self._add_btn)
        
        layout.addLayout(header_layout)
        
        # Search/filter
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(t["search"])
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input)
        
        # Snippet list
        self._snippet_list = QListWidget()
        self._snippet_list.itemDoubleClicked.connect(self._on_snippet_selected)
        layout.addWidget(self._snippet_list)
        
        # Preview
        self._preview_label = QLabel(t["preview"])
        self._preview_label.setStyleSheet("font-weight: bold; color: #888;")
        layout.addWidget(self._preview_label)
        
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMaximumHeight(100)
        self._preview.setFont(QFont("monospace", 9))
        layout.addWidget(self._preview)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self._insert_btn = QPushButton(t["insert"])
        self._insert_btn.clicked.connect(self._on_insert_snippet)
        actions_layout.addWidget(self._insert_btn)
        
        self._edit_btn = QPushButton(t["edit"])
        self._edit_btn.clicked.connect(self._on_edit_snippet)
        actions_layout.addWidget(self._edit_btn)
        
        self._delete_btn = QPushButton(t["delete"])
        self._delete_btn.clicked.connect(self._on_delete_snippet)
        actions_layout.addWidget(self._delete_btn)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
    
    def _load_default_snippets(self) -> None:
        """Load default snippets."""
        defaults = {
            "python-class": '''class ClassName:
    """Description."""
    
    def __init__(self):
        pass
    
    def method(self):
        pass''',
            "python-function": '''def function_name(param):
    """Description."""
    pass''',
            "python-if-main": '''if __name__ == "__main__":
    main()''',
            "js-arrow-function": 'const name = (params) => {\n    return value;\n};',
            "js-console-log": 'console.log("Debug:", value);',
            "html-div": '<div class="container">\n    \n</div>',
            "html-form": '<form action="/submit" method="POST">\n    \n</form>',
            "sql-select": 'SELECT * FROM table_name\nWHERE condition;',
            "sql-insert": 'INSERT INTO table_name (col1, col2)\nVALUES (val1, val2);',
            "dockerfile": '''FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]''',
        }
        
        for name, content in defaults.items():
            self._snippets[name] = content
        
        self._update_list()
    
    def _update_list(self) -> None:
        """Update the snippet list."""
        self._snippet_list.clear()
        
        search_text = self._search_input.text().lower()
        
        for name in sorted(self._snippets.keys()):
            if not search_text or search_text in name.lower():
                item = QListWidgetItem(name)
                self._snippet_list.addItem(item)
    
    def _on_search_changed(self, text: str) -> None:
        """Handle search change."""
        self._update_list()
    
    def _on_snippet_selected(self, item: QListWidgetItem) -> None:
        """Handle snippet selection."""
        name = item.text()
        content = self._snippets.get(name, "")
        self._preview.setPlainText(content)
    
    def _on_add_snippet(self) -> None:
        """Add a new snippet."""
        dialog = SnippetEditDialog(self, "Add Snippet", "", "")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, content = dialog.get_values()
            if name:
                self._snippets[name] = content
                self._update_list()
    
    def _on_edit_snippet(self) -> None:
        """Edit selected snippet."""
        current_item = self._snippet_list.currentItem()
        if not current_item:
            return
        
        name = current_item.text()
        content = self._snippets.get(name, "")
        
        dialog = SnippetEditDialog(self, "Edit Snippet", name, content)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, new_content = dialog.get_values()
            if new_name and new_name != name:
                del self._snippets[name]
            if new_name:
                self._snippets[new_name] = new_content
                self._update_list()
    
    def _on_delete_snippet(self) -> None:
        """Delete selected snippet."""
        current_item = self._snippet_list.currentItem()
        if not current_item:
            return
        
        name = current_item.text()
        
        reply = QMessageBox.question(
            self, "Delete Snippet",
            f"Delete snippet '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self._snippets[name]
            self._update_list()
            self._preview.clear()
    
    def _on_insert_snippet(self) -> None:
        """Insert selected snippet."""
        current_item = self._snippet_list.currentItem()
        if not current_item:
            return
        
        name = current_item.text()
        content = self._snippets.get(name, "")
        
        self.snippet_selected.emit(name, content)
    
    def get_snippet_content(self, name: str) -> Optional[str]:
        """Get snippet content by name."""
        return self._snippets.get(name)
    
    def get_all_snippets(self) -> Dict[str, str]:
        """Get all snippets."""
        return self._snippets.copy()


class SnippetEditDialog(QDialog):
    """Dialog to edit a snippet."""
    
    def __init__(self, parent: Optional[QWidget], title: str, name: str, content: str) -> None:
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumSize(400, 300)
        
        layout = QFormLayout(self)
        
        # Name input
        self._name_input = QLineEdit(name)
        self._name_input.setPlaceholderText("Snippet name")
        layout.addRow("Name:", self._name_input)
        
        # Content input
        self._content_input = QTextEdit()
        self._content_input.setPlainText(content)
        self._content_input.setFont(QFont("monospace", 10))
        layout.addRow("Content:", self._content_input)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self) -> tuple:
        """Get dialog values."""
        return self._name_input.text(), self._content_input.toPlainText()


def show_snippets_panel(parent: Optional[QWidget] = None) -> SnippetsPanel:
    """Create and return a snippets panel."""
    return SnippetsPanel(parent)