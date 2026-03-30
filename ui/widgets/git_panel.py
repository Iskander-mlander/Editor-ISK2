"""
Git Panel Widget
================
Git integration panel with real git functionality.
"""

from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QTabWidget,
    QLineEdit, QTextEdit, QMessageBox, QInputDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont

from features.git import GitClient, GitFileStatus


class GitPanel(QWidget):
    """
    Git integration panel with real git functionality.
    """
    
    file_selected = pyqtSignal(str)
    repository_opened = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._git_client: Optional[GitClient] = None
        self._current_path: str = ""
        
        self._setup_ui()
    
    @property
    def git_client(self) -> Optional[GitClient]:
        """Get the git client."""
        return self._git_client
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Header with status
        header_layout = QHBoxLayout()
        
        self._status_label = QLabel("No repository")
        self._status_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self._status_label)
        
        header_layout.addStretch()
        
        open_btn = QPushButton("Open")
        open_btn.setMaximumWidth(60)
        open_btn.clicked.connect(self._on_open_repo)
        header_layout.addWidget(open_btn)
        
        layout.addLayout(header_layout)
        
        # Branch info
        self._branch_label = QLabel("")
        self._branch_label.setStyleSheet("color: #888;")
        layout.addWidget(self._branch_label)
        
        # Tab widget for different views
        tabs = QTabWidget()
        
        # Changes tab
        changes_widget = QWidget()
        changes_layout = QVBoxLayout(changes_widget)
        changes_layout.setContentsMargins(0, 4, 0, 4)
        
        # Split into staged/unstaged
        splitter_layout = QHBoxLayout()
        
        # Staged section
        staged_widget = QWidget()
        staged_layout = QVBoxLayout(staged_widget)
        staged_layout.setContentsMargins(0, 0, 4, 0)
        
        staged_header = QLabel("Staged")
        staged_header.setStyleSheet("font-weight: bold;")
        staged_layout.addWidget(staged_header)
        
        self._staged_list = QListWidget()
        self._staged_list.setAlternatingRowColors(True)
        staged_layout.addWidget(self._staged_list)
        
        # Unstaged section
        unstaged_widget = QWidget()
        unstaged_layout = QVBoxLayout(unstaged_widget)
        unstaged_layout.setContentsMargins(4, 0, 0, 0)
        
        unstaged_header = QLabel("Changes")
        unstaged_header.setStyleSheet("font-weight: bold;")
        unstaged_layout.addWidget(unstaged_header)
        
        self._changes_list = QListWidget()
        self._changes_list.setAlternatingRowColors(True)
        unstaged_layout.addWidget(self._changes_list)
        
        splitter_layout.addWidget(staged_widget)
        splitter_layout.addWidget(unstaged_widget)
        
        changes_layout.addLayout(splitter_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        stage_btn = QPushButton("Stage")
        stage_btn.clicked.connect(self._on_stage_selected)
        buttons_layout.addWidget(stage_btn)
        
        unstage_btn = QPushButton("Unstage")
        unstage_btn.clicked.connect(self._on_unstage_selected)
        buttons_layout.addWidget(unstage_btn)
        
        discard_btn = QPushButton("Discard")
        discard_btn.clicked.connect(self._on_discard)
        buttons_layout.addWidget(discard_btn)
        
        stage_all_btn = QPushButton("Stage All")
        stage_all_btn.clicked.connect(self._on_stage_all)
        buttons_layout.addWidget(stage_all_btn)
        
        buttons_layout.addStretch()
        
        commit_btn = QPushButton("Commit")
        commit_btn.setMinimumWidth(80)
        commit_btn.clicked.connect(self._on_commit)
        buttons_layout.addWidget(commit_btn)
        
        changes_layout.addLayout(buttons_layout)
        
        tabs.addTab(changes_widget, "Changes")
        
        # Diff tab
        diff_widget = QWidget()
        diff_layout = QVBoxLayout(diff_widget)
        
        self._diff_view = QTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setFont(QFont("monospace"))
        diff_layout.addWidget(self._diff_view)
        
        tabs.addTab(diff_widget, "Diff")
        
        # Branch tab
        branch_widget = QWidget()
        branch_layout = QVBoxLayout(branch_widget)
        
        # Branch list
        self._branches_list = QListWidget()
        branch_layout.addWidget(self._branches_list)
        
        branch_buttons = QHBoxLayout()
        
        checkout_btn = QPushButton("Checkout")
        checkout_btn.clicked.connect(self._on_checkout_branch)
        branch_buttons.addWidget(checkout_btn)
        
        create_btn = QPushButton("Create Branch")
        create_btn.clicked.connect(self._on_create_branch)
        branch_buttons.addWidget(create_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._on_refresh)
        branch_buttons.addWidget(refresh_btn)
        
        branch_layout.addLayout(branch_buttons)
        
        tabs.addTab(branch_widget, "Branches")
        
        # Remotes tab
        remotes_widget = QWidget()
        remotes_layout = QVBoxLayout(remotes_widget)
        
        self._remotes_list = QListWidget()
        remotes_layout.addWidget(self._remotes_list)
        
        remote_buttons = QHBoxLayout()
        
        pull_btn = QPushButton("Pull")
        pull_btn.clicked.connect(self._on_pull)
        remote_buttons.addWidget(pull_btn)
        
        fetch_btn = QPushButton("Fetch")
        fetch_btn.clicked.connect(self._on_fetch)
        remote_buttons.addWidget(fetch_btn)
        
        push_btn = QPushButton("Push")
        push_btn.clicked.connect(self._on_push)
        remote_buttons.addWidget(push_btn)
        
        remote_buttons.addStretch()
        
        remotes_layout.addLayout(remote_buttons)
        
        tabs.addTab(remotes_widget, "Remotes")
        
        layout.addWidget(tabs)
        
        # Connect signals
        self._changes_list.itemSelectionChanged.connect(self._on_change_selected)
        self._staged_list.itemSelectionChanged.connect(self._on_change_selected)
    
    def open_repository(self, path: str) -> bool:
        """Open a git repository."""
        from pathlib import Path
        
        self._current_path = path
        
        if self._git_client is None:
            self._git_client = GitClient()
            self._git_client.signals.status_changed.connect(self._on_status_changed)
            self._git_client.signals.error_occurred.connect(self._on_error)
        
        repo_path = Path(path)
        
        # If it's a file, get parent directory
        if repo_path.is_file():
            repo_path = repo_path.parent
        
        if self._git_client.open_repository(repo_path):
            self._status_label.setText(f"📁 {repo_path.name}")
            self._branch_label.setText(f"Branch: {self._git_client.current_branch}")
            self._refresh_changes()
            self._refresh_branches()
            self._refresh_remotes()
            self.repository_opened.emit(str(repo_path))
            return True
        
        return False
    
    def _on_status_changed(self) -> None:
        """Handle status changed signal."""
        self._refresh_changes()
        self._branch_label.setText(f"Branch: {self._git_client.current_branch}")
    
    def _on_error(self, message: str) -> None:
        """Handle error signal."""
        QMessageBox.warning(self, "Git Error", message)
    
    def _refresh_changes(self) -> None:
        """Refresh the changes lists."""
        if not self._git_client:
            return
        
        # Staged files
        self._staged_list.clear()
        staged = self._git_client.get_staged_files()
        for f in staged:
            item = QListWidgetItem(f"✓ {f.path}")
            item.setData(Qt.ItemDataRole.UserRole, f)
            if f.status == 'A':
                item.setForeground(QColor(78, 201, 176))  # Green
            elif f.status == 'M':
                item.setForeground(QColor(245, 189, 72))  # Orange
            elif f.status == 'D':
                item.setForeground(QColor(242, 83, 80))  # Red
            self._staged_list.addItem(item)
        
        # Unstaged files
        self._changes_list.clear()
        modified = self._git_client.get_modified_files()
        untracked = self._git_client.get_untracked_files()
        
        for f in modified + untracked:
            if f.status == '?':
                item = QListWidgetItem(f"? {f.path}")
                item.setForeground(QColor(136, 136, 136))  # Gray
            else:
                item = QListWidgetItem(f"M {f.path}")
                item.setForeground(QColor(245, 189, 72))  # Orange
            item.setData(Qt.ItemDataRole.UserRole, f)
            self._changes_list.addItem(item)
    
    def _refresh_branches(self) -> None:
        """Refresh the branches list."""
        if not self._git_client:
            return
        
        self._branches_list.clear()
        
        # Local branches first
        for branch in self._git_client.branches:
            if not branch.is_remote:
                display = f"● {branch.name}" if branch.is_current else f"  {branch.name}"
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, branch)
                self._branches_list.addItem(item)
        
        # Remote branches
        self._branches_list.addItem("")
        for branch in self._git_client.branches:
            if branch.is_remote:
                item = QListWidgetItem(f"  {branch.name}")
                item.setForeground(QColor(100, 149, 237))  # Blue
                item.setData(Qt.ItemDataRole.UserRole, branch)
                self._branches_list.addItem(item)
    
    def _refresh_remotes(self) -> None:
        """Refresh the remotes list."""
        if not self._git_client:
            return
        
        self._remotes_list.clear()
        
        for remote in self._git_client.get_remotes():
            self._remotes_list.addItem(remote)
    
    def _on_open_repo(self) -> None:
        """Handle open repository button."""
        from PyQt6.QtWidgets import QFileDialog
        
        path = QFileDialog.getExistingDirectory(self, "Select Git Repository")
        
        if path:
            self.open_repository(path)
    
    def _on_stage_selected(self) -> None:
        """Stage selected files."""
        if not self._git_client:
            return
        
        selected = self._changes_list.selectedItems()
        
        for item in selected:
            f: GitFileStatus = item.data(Qt.ItemDataRole.UserRole)
            if f:
                self._git_client.stage_file(f.path)
    
    def _on_unstage_selected(self) -> None:
        """Unstage selected files."""
        if not self._git_client:
            return
        
        selected = self._staged_list.selectedItems()
        
        for item in selected:
            f: GitFileStatus = item.data(Qt.ItemDataRole.UserRole)
            if f:
                self._git_client.unstage_file(f.path)
    
    def _on_stage_all(self) -> None:
        """Stage all changes."""
        if self._git_client:
            self._git_client.stage_all()
    
    def _on_discard(self) -> None:
        """Discard selected file changes."""
        if not self._git_client:
            return
        
        selected = self._changes_list.selectedItems()
        
        if not selected:
            return
        
        reply = QMessageBox.question(
            self,
            "Discard Changes",
            "Are you sure you want to discard changes in these file(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected:
                f: GitFileStatus = item.data(Qt.ItemDataRole.UserRole)
                if f:
                    self._git_client.discard_changes(f.path)
    
    def _on_commit(self) -> None:
        """Commit staged changes."""
        if not self._git_client:
            return
        
        staged = self._git_client.get_staged_files()
        
        if not staged:
            QMessageBox.information(
                self,
                "No Staged Changes",
                "Stage some files first before committing."
            )
            return
        
        message, ok = QInputDialog.getMultiLineText(
            self,
            "Commit Message",
            "Enter commit message:"
        )
        
        if ok and message.strip():
            if self._git_client.commit(message.strip()):
                QMessageBox.information(self, "Success", "Commit created successfully!")
            # Error is handled by signal
    
    def _on_change_selected(self) -> None:
        """Show diff for selected change."""
        if not self._git_client:
            return
        
        # Check unstaged first
        selected = self._changes_list.selectedItems()
        if not selected:
            selected = self._staged_list.selectedItems()
        
        if not selected:
            self._diff_view.clear()
            return
        
        f: GitFileStatus = selected[0].data(Qt.ItemDataRole.UserRole)
        
        if not f:
            return
        
        if f.staged:
            diff = self._git_client.get_staged_diff(f.path)
        else:
            diff = self._git_client.get_diff(f.path)
        
        self._diff_view.setPlainText(diff if diff else "No changes")
    
    def _on_checkout_branch(self) -> None:
        """Checkout selected branch."""
        if not self._git_client:
            return
        
        selected = self._branches_list.selectedItems()
        
        if not selected:
            return
        
        branch = selected[0].data(Qt.ItemDataRole.UserRole)
        
        if branch:
            self._git_client.checkout_branch(branch.name)
    
    def _on_create_branch(self) -> None:
        """Create a new branch."""
        if not self._git_client:
            return
        
        name, ok = QInputDialog.getText(self, "New Branch", "Branch name:")
        
        if ok and name.strip():
            self._git_client.create_branch(name.strip())
    
    def _on_refresh(self) -> None:
        """Refresh all git data."""
        if self._git_client:
            self._git_client.refresh_status()
            self._git_client.refresh_branches()
            self._refresh_changes()
            self._refresh_branches()
    
    def _on_pull(self) -> None:
        """Pull from remote."""
        if self._git_client:
            if self._git_client.pull():
                QMessageBox.information(self, "Success", "Pull completed!")
    
    def _on_fetch(self) -> None:
        """Fetch from remote."""
        if self._git_client:
            if self._git_client.fetch():
                QMessageBox.information(self, "Success", "Fetch completed!")
                self._git_client.refresh_branches()
                self._refresh_branches()
    
    def _on_push(self) -> None:
        """Push to remote."""
        if self._git_client:
            if self._git_client.push():
                QMessageBox.information(self, "Success", "Push completed!")
    
    def set_repository_status(self, status: Dict[str, Any]) -> None:
        """Set repository status (legacy)."""
        branch = status.get("branch", "")
        self._status_label.setText(f"Repository: {status.get('repo', 'Unknown')}")
        self._branch_label.setText(f"Branch: {branch}")
    
    def set_changes(self, changes: List[Dict[str, Any]]) -> None:
        """Set the list of changes (legacy)."""
        # This is handled by _refresh_changes now
        pass
    
    def show_commit_dialog(self) -> None:
        """Show commit dialog."""
        self._on_commit()
    
    def pull(self) -> bool:
        """Pull from remote."""
        if self._git_client:
            return self._git_client.pull()
        return False
    
    def push(self) -> bool:
        """Push to remote."""
        if self._git_client:
            return self._git_client.push()
        return False
    
    def show_branch_dialog(self) -> None:
        """Show branch dialog."""
        self._branches_list.setFocus()