"""
Task List Panel
===============
Panel to display TODO, FIXME, and other task markers in the codebase.
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import re
import os
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QListWidgetItem, QPushButton, QLabel, QComboBox,
                            QLineEdit, QMessageBox)
from PyQt6.QtGui import QColor, QFont


@dataclass
class TaskItem:
    """Represents a task/todo item."""
    file_path: str
    line_number: int
    text: str
    task_type: str  # TODO, FIXME, NOTE, etc.
    priority: str = "normal"


class TaskListPanel(QWidget):
    """
    Panel to display tasks/todos in the project.
    """
    
    task_clicked = pyqtSignal(str, int)  # file_path, line
    
    # Task patterns
    TASK_PATTERNS = [
        (r'\bTODO\b', "TODO", "normal"),
        (r'\bFIXME\b', "FIXME", "high"),
        (r'\bBUG\b', "BUG", "high"),
        (r'\bHACK\b', "HACK", "medium"),
        (r'\bNOTE\b', "NOTE", "normal"),
        (r'\bWARNING\b', "WARNING", "medium"),
        (r'\bXXX\b', "XXX", "normal"),
        (r'\bTASK\b', "TASK", "normal"),
        (r'\bCHANGED\b', "CHANGED", "normal"),
    ]
    
    # Task files to auto-create
    TASK_FILES = [
        "TODO.md",
        "FIXME.md", 
        "NOTES.md",
    ]
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._tasks: List[TaskItem] = []
        self._root_path: str = ""
        self._language: str = "es"
        self._msg_tasks: str = "tareas"
        self._msg_no_tasks: str = "Sin tareas"
        self._setup_ui()
        self._update_ui_texts()
    
    def set_current_file(self, file_path: Optional[str]) -> None:
        """Set current file and update path to its directory."""
        if file_path:
            directory = os.path.dirname(os.path.abspath(file_path))
            if os.path.isdir(directory):
                self.set_root_path(directory)
    
    def _ensure_task_files_exist(self) -> None:
        """Create task files if they don't exist."""
        if not self._root_path or not os.path.isdir(self._root_path):
            return
        
        for task_file in self.TASK_FILES:
            file_path = os.path.join(self._root_path, task_file)
            if not os.path.exists(file_path):
                try:
                    # Create file with header
                    content = f"# {task_file.replace('.md', '')}\n\n"
                    if task_file == "TODO.md":
                        content += "## Pendiente\n- [ ] Tarea 1\n- [ ] Tarea 2\n"
                    elif task_file == "FIXME.md":
                        content += "## Problemas a resolver\n- Problema 1\n- Problema 2\n"
                    elif task_file == "NOTES.md":
                        content += "## Notas\n\nNotas del proyecto...\n"
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                except Exception:
                    pass
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Header
        header_layout = QHBoxLayout()
        
        self._title_label = QLabel("Tasks")
        self._title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self._title_label)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setMaximumWidth(25)
        refresh_btn.setToolTip("Refresh tasks")
        refresh_btn.clicked.connect(self.scan_tasks)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filter
        filter_layout = QHBoxLayout()
        
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "TODO", "FIXME", "BUG", "NOTE"])
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._filter_combo)
        
        layout.addLayout(filter_layout)
        
        # Search
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter tasks...")
        self._search_input.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self._search_input)
        
        # Task list
        self._task_list = QListWidget()
        self._task_list.itemDoubleClicked.connect(self._on_task_clicked)
        layout.addWidget(self._task_list)
        
        # Status
        self._status_label = QLabel("0 tasks")
        self._status_label.setStyleSheet("color: #888;")
        layout.addWidget(self._status_label)
    
    def set_language(self, lang_code: str) -> None:
        """Set UI language."""
        self._language = lang_code
        self._update_ui_texts()
    
    def _update_ui_texts(self) -> None:
        """Update UI texts based on language."""
        if self._language == "es":
            self._title_label.setText("Tareas")
            self._filter_combo.clear()
            self._filter_combo.addItems(["Todo", "TODO", "FIXME", "BUG", "NOTA"])
            self._search_input.setPlaceholderText("Filtrar tareas...")
            self._msg_tasks = "tareas"
            self._msg_no_tasks = "Sin tareas"
        else:
            self._title_label.setText("Tasks")
            self._filter_combo.clear()
            self._filter_combo.addItems(["All", "TODO", "FIXME", "BUG", "NOTE"])
            self._search_input.setPlaceholderText("Filter tasks...")
            self._msg_tasks = "tasks"
            self._msg_no_tasks = "No tasks"
        
        self._update_list()
    
    def set_root_path(self, path: str) -> None:
        """Set the root path to scan."""
        self._root_path = path
        self._ensure_task_files_exist()
        self.scan_tasks()
    
    def scan_tasks(self) -> None:
        """Scan for tasks in the project."""
        if not self._root_path:
            return
        
        self._tasks = []
        
        file_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', 
                         '.c', '.cpp', '.h', '.hpp', '.go', '.rs', '.rb',
                         '.php', '.html', '.css', '.scss', '.md', '.txt'}
        
        for root, dirs, files in os.walk(self._root_path):
            dirs[:] = [d for d in dirs if d not in 
                     ('.git', '__pycache__', 'node_modules', '.venv', 
                      'venv', 'build', 'dist')]
            
            for file in files:
                if Path(file).suffix not in file_extensions:
                    continue
                
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            for pattern, task_type, priority in self.TASK_PATTERNS:
                                if re.search(pattern, line, re.IGNORECASE):
                                    self._tasks.append(TaskItem(
                                        file_path=file_path,
                                        line_number=line_num,
                                        text=line.strip()[:100],  # Truncate
                                        task_type=task_type,
                                        priority=priority
                                    ))
                except Exception:
                    pass
        
        self._update_list()
    
    def _update_list(self) -> None:
        """Update the task list."""
        self._task_list.clear()
        
        filter_type = self._filter_combo.currentText()
        search_text = self._search_input.text().lower()
        
        for task in self._tasks:
            # Apply type filter (handle both English and Spanish)
            if filter_type not in ("All", "Todo") and task.task_type != filter_type:
                continue
            
            # Apply search filter
            if search_text and search_text not in task.text.lower():
                continue
            
            # Create item
            icon = self._get_icon(task.task_type)
            color = self._get_color(task.task_type)
            
            item = QListWidgetItem(icon)
            item.setForeground(color)
            
            # File:line - task text
            file_name = Path(task.file_path).name
            display = f"{file_name}:{task.line_number} {task.text}"
            item.setText(display)
            item.setData(Qt.ItemDataRole.UserRole, task)
            
            self._task_list.addItem(item)
        
        count = self._task_list.count()
        if count == 0:
            self._status_label.setText(self._msg_no_tasks)
        else:
            self._status_label.setText(f"{count} {self._msg_tasks}")
    
    def _get_icon(self, task_type: str) -> str:
        """Get icon for task type."""
        icons = {
            "TODO": "📝",
            "FIXME": "🔧",
            "BUG": "🐛",
            "HACK": "⚡",
            "NOTE": "📋",
            "WARNING": "⚠️",
            "XXX": "❓",
        }
        return icons.get(task_type, "•")
    
    def _get_color(self, task_type: str) -> QColor:
        """Get color for task type."""
        colors = {
            "TODO": QColor("#4ECDC4"),
            "FIXME": QColor("#FF6B6B"),
            "BUG": QColor("#FF6B6B"),
            "HACK": QColor("#FFEAA7"),
            "NOTE": QColor("#74B9FF"),
            "WARNING": QColor("#FDCB6E"),
            "XXX": QColor("#95A5A6"),
        }
        return colors.get(task_type, QColor("#FFFFFF"))
    
    def _on_filter_changed(self, text: str) -> None:
        """Handle filter change."""
        self._update_list()
    
    def _on_task_clicked(self, item: QListWidgetItem) -> None:
        """Handle task click."""
        task: TaskItem = item.data(Qt.ItemDataRole.UserRole)
        if task:
            self.task_clicked.emit(task.file_path, task.line_number)


def show_task_list(parent: Optional[QWidget] = None) -> TaskListPanel:
    """Create and return a task list panel."""
    return TaskListPanel(parent)