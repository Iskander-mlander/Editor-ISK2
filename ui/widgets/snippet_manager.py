"""
Snippet Manager Widget
======================
Widget for managing code snippets - list, edit, create, delete.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLineEdit, QTextEdit, QPushButton, QLabel, QDialog, QDialogButtonBox,
    QSplitter, QMessageBox, QComboBox, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from features.snippets import SnippetManager, Snippet


class SnippetManagerWidget(QWidget):
    """
    Widget for managing code snippets.
    """
    
    snippet_selected = pyqtSignal(str)  # snippet ID
    snippet_saved = pyqtSignal(str)    # snippet ID
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._snippet_manager: Optional[SnippetManager] = None
        self._current_snippet: Optional[Snippet] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Toolbar for actions - OUTSIDE the frame
        toolbar = QHBoxLayout()
        
        self._refresh_btn = QPushButton("🔄 Recargar")
        self._refresh_btn.setToolTip("Recargar snippets")
        self._refresh_btn.clicked.connect(self._refresh_snippets)
        
        self._new_btn = QPushButton("➕ Nuevo")
        self._new_btn.setToolTip("Crear nuevo snippet")
        self._new_btn.clicked.connect(self._new_snippet)
        
        self._delete_btn = QPushButton("🗑️ Eliminar")
        self._delete_btn.setToolTip("Eliminar snippet seleccionado")
        self._delete_btn.clicked.connect(self._delete_snippet)
        
        toolbar.addWidget(self._refresh_btn)
        toolbar.addWidget(self._new_btn)
        toolbar.addWidget(self._delete_btn)
        toolbar.addStretch()
        
        main_layout.addLayout(toolbar)
        
        # Content area with splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Snippet List - IN A FRAME
        left_group = QGroupBox("Snippets")
        left_layout = QVBoxLayout(left_group)
        
        # Search filter
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filtrar snippets...")
        self._filter_edit.textChanged.connect(self._filter_changed)
        left_layout.addWidget(self._filter_edit)
        
        # Snippet list
        self._snippet_list = QListWidget()
        self._snippet_list.itemClicked.connect(self._on_snippet_clicked)
        left_layout.addWidget(self._snippet_list)
        
        content_splitter.addWidget(left_group)
        
        # Right panel - Editor - IN A FRAME
        right_group = QGroupBox("Editor de Snippet")
        right_layout = QVBoxLayout(right_group)
        
        # Form fields
        form_layout = QVBoxLayout()
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nombre:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Nombre del snippet")
        name_layout.addWidget(self._name_edit)
        form_layout.addLayout(name_layout)
        
        # Trigger
        trigger_layout = QHBoxLayout()
        trigger_layout.addWidget(QLabel("Disparador:"))
        self._trigger_edit = QLineEdit()
        self._trigger_edit.setPlaceholderText("Palabra para activar (ej: 'for')")
        trigger_layout.addWidget(self._trigger_edit)
        form_layout.addLayout(trigger_layout)
        
        # Language
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Lenguaje:"))
        self._language_combo = QComboBox()
        self._language_combo.addItems(["python", "javascript", "typescript", "html", "css", "json", "markdown", "global"])
        lang_layout.addWidget(self._language_combo)
        form_layout.addLayout(lang_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Descripción:"))
        self._description_edit = QLineEdit()
        self._description_edit.setPlaceholderText("Breve descripción")
        desc_layout.addWidget(self._description_edit)
        form_layout.addLayout(desc_layout)
        
        right_layout.addLayout(form_layout)
        
        # Content editor
        content_label = QLabel("Contenido (usa ${1:default} para placeholders):")
        right_layout.addWidget(content_label)
        
        self._content_edit = QTextEdit()
        self._content_edit.setPlaceholderText("def ${1:function_name}(${2:args}):\n    ${3:pass}")
        self._content_edit.setFont(self._get_code_font())
        right_layout.addWidget(self._content_edit)
        
        # Save button
        self._save_btn = QPushButton("💾 Guardar Snippet")
        self._save_btn.clicked.connect(self._save_snippet)
        right_layout.addWidget(self._save_btn)
        
        content_splitter.addWidget(right_group)
        
        # Set sizes
        content_splitter.setSizes([250, 500])
        
        main_layout.addWidget(content_splitter)
        
        # Initially disable editor
        self._set_editor_enabled(False)
    
    def _get_code_font(self) -> QFont:
        """Get monospace font for code editing."""
        font = QFont("Monospace")
        font.setPointSize(10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font
    
    def _set_editor_enabled(self, enabled: bool) -> None:
        """Enable/disable the editor panel."""
        self._name_edit.setEnabled(enabled)
        self._trigger_edit.setEnabled(enabled)
        self._language_combo.setEnabled(enabled)
        self._description_edit.setEnabled(enabled)
        self._content_edit.setEnabled(enabled)
        self._save_btn.setEnabled(enabled)
    
    def set_snippet_manager(self, manager: SnippetManager) -> None:
        """Set the snippet manager and load snippets."""
        self._snippet_manager = manager
        self._refresh_snippets()
    
    def _refresh_snippets(self) -> None:
        """Refresh the snippet list."""
        if not self._snippet_manager:
            return
        
        self._snippet_list.clear()
        
        filter_text = self._filter_edit.text().lower()
        
        for snippet_id, snippet in self._snippet_manager.snippets.items():
            # Apply filter
            if filter_text:
                if (filter_text not in snippet.name.lower() and 
                    filter_text not in snippet.trigger.lower() and
                    filter_text not in snippet.description.lower()):
                    continue
            
            # Add to list
            item = QListWidgetItem(f"{snippet.trigger} - {snippet.name}")
            item.setData(Qt.ItemDataRole.UserRole, snippet_id)
            item.setToolTip(snippet.description or "Sin descripción")
            self._snippet_list.addItem(item)
    
    def _filter_changed(self, text: str) -> None:
        """Handle filter text change."""
        self._refresh_snippets()
    
    def _on_snippet_clicked(self, item: QListWidgetItem) -> None:
        """Handle snippet selection."""
        snippet_id = item.data(Qt.ItemDataRole.UserRole)
        
        if self._snippet_manager:
            self._current_snippet = self._snippet_manager.get_snippet(snippet_id)
            
            if self._current_snippet:
                self._load_snippet_to_editor(self._current_snippet)
                self._set_editor_enabled(True)
                
                self.snippet_selected.emit(snippet_id)
    
    def _load_snippet_to_editor(self, snippet: Snippet) -> None:
        """Load snippet data into the editor fields."""
        self._name_edit.setText(snippet.name)
        self._trigger_edit.setText(snippet.trigger)
        self._language_combo.setCurrentText(snippet.language)
        self._description_edit.setText(snippet.description)
        self._content_edit.setText(snippet.content)
    
    def _new_snippet(self) -> None:
        """Create a new snippet."""
        # Clear editor
        self._current_snippet = None
        self._name_edit.clear()
        self._trigger_edit.clear()
        self._language_combo.setCurrentText("python")
        self._description_edit.clear()
        self._content_edit.clear()
        
        self._set_editor_enabled(True)
        self._name_edit.setFocus()
        
        # Set placeholder
        self._content_edit.setPlaceholderText("def ${1:function_name}(${2:args}):\n    ${3:pass}")
    
    def _save_snippet(self) -> None:
        """Save the current snippet."""
        # Validate
        name = self._name_edit.text().strip()
        trigger = self._trigger_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validación", "El nombre es requerido")
            return
        
        if not trigger:
            QMessageBox.warning(self, "Validación", "El disparador es requerido")
            return
        
        content = self._content_edit.toPlainText()
        if not content:
            QMessageBox.warning(self, "Validación", "El contenido es requerido")
            return
        
        language = self._language_combo.currentText()
        description = self._description_edit.text().strip()
        
        # Check if it's a new snippet or update
        if self._current_snippet:
            # Update existing
            self._current_snippet.name = name
            self._current_snippet.trigger = trigger
            self._current_snippet.language = language
            self._current_snippet.description = description
            self._current_snippet.content = content
            
            if self._snippet_manager.update_snippet(self._current_snippet):
                self._save_snippet_to_file(self._current_snippet)
                QMessageBox.information(self, "Éxito", "Snippet actualizado correctamente!")
                self.snippet_saved.emit(self._current_snippet.id)
            else:
                QMessageBox.warning(self, "Error", "Error al actualizar el snippet")
        else:
            # Create new
            snippet_id = trigger.lower().replace(" ", "_")
            new_snippet = Snippet(
                id=snippet_id,
                name=name,
                trigger=trigger,
                content=content,
                language=language,
                description=description
            )
            
            if self._snippet_manager.add_snippet(new_snippet):
                self._save_snippet_to_file(new_snippet)
                self._current_snippet = new_snippet
                QMessageBox.information(self, "Éxito", "Snippet creado correctamente!")
                self.snippet_saved.emit(snippet_id)
                self._refresh_snippets()
            else:
                QMessageBox.warning(self, "Error", f"El snippet con disparador '{trigger}' ya existe")
    
    def _save_snippet_to_file(self, snippet: Snippet) -> None:
        """Save snippet to file."""
        import json
        
        # Determine save path
        if hasattr(self._snippet_manager, '_snippets_path'):
            snippets_dir = Path(self._snippet_manager._snippets_path)
        else:
            # Default to Editor-1.3-dev2 snippets
            snippets_dir = Path(__file__).parent.parent.parent / "Editor-1.3-dev2" / "snippets" / snippet.language
        
        snippets_dir.mkdir(parents=True, exist_ok=True)
        
        snippet_file = snippets_dir / f"{snippet.id}.snippet"
        
        data = {
            "name": snippet.name,
            "trigger": snippet.trigger,
            "description": snippet.description,
            "body": snippet.content.split('\n'),
            "scope": snippet.language
        }
        
        with open(snippet_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def _delete_snippet(self) -> None:
        """Delete the selected snippet."""
        if not self._current_snippet:
            QMessageBox.information(self, "Información", "Selecciona un snippet para eliminar")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que quieres eliminar '{self._current_snippet.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            snippet_id = self._current_snippet.id
            
            if self._snippet_manager.remove_snippet(snippet_id):
                # Also delete file
                self._delete_snippet_file(snippet_id)
                
                QMessageBox.information(self, "Éxito", "Snippet eliminado")
                
                # Clear editor
                self._current_snippet = None
                self._name_edit.clear()
                self._trigger_edit.clear()
                self._description_edit.clear()
                self._content_edit.clear()
                self._set_editor_enabled(False)
                
                self._refresh_snippets()
            else:
                QMessageBox.warning(self, "Error", "Error al eliminar el snippet")
    
    def _delete_snippet_file(self, snippet_id: str) -> None:
        """Delete snippet file from disk."""
        # Try to find and delete the file
        if hasattr(self._snippet_manager, '_snippets_path'):
            snippets_dir = Path(self._snippet_manager._snippets_path)
        else:
            snippets_dir = Path(__file__).parent.parent.parent / "Editor-1.3-dev2" / "snippets"
        
        # Search for the file in all language subdirectories
        for snippet_file in snippets_dir.rglob(f"{snippet_id}.snippet"):
            try:
                snippet_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete file {snippet_file}: {e}")


class SnippetManagerDialog(QDialog):
    """
    Dialog for managing snippets.
    """
    
    def __init__(self, parent: Optional[QWidget] = None, snippet_manager: Optional[SnippetManager] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gestionar Snippets")
        self.setMinimumSize(850, 650)
        
        layout = QVBoxLayout(self)
        
        self._widget = SnippetManagerWidget(self)
        if snippet_manager:
            self._widget.set_snippet_manager(snippet_manager)
        
        layout.addWidget(self._widget)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
    
    def set_snippet_manager(self, manager: SnippetManager) -> None:
        """Set the snippet manager."""
        self._widget.set_snippet_manager(manager)
