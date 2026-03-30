"""
Git Client Module
=================
Real git implementation using subprocess.
"""

import subprocess
import os
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class GitFileStatus:
    """Represents a file's git status."""
    path: str
    status: str  # M, A, D, R, C, U, ?, !
    staged: bool = False
    old_path: Optional[str] = None  # For renames


@dataclass
class GitCommit:
    """Represents a git commit."""
    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    message: str


@dataclass
class GitBranch:
    """Represents a git branch."""
    name: str
    is_current: bool
    is_remote: bool


class GitSignals(QObject):
    """Signals for git events."""
    status_changed = pyqtSignal()
    branch_changed = pyqtSignal(str)
    commit_created = pyqtSignal(str)
    error_occurred = pyqtSignal(str)


class GitClient(QObject):
    """
    Git client for version control using subprocess.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = GitSignals()
        self._repo_path: Optional[Path] = None
        self._current_branch: str = ""
        self._status: List[GitFileStatus] = []
        self._commits: List[GitCommit] = []
        self._branches: List[GitBranch] = []
    
    @property
    def signals(self) -> GitSignals:
        """Get git signals."""
        return self._signals
    
    @property
    def repo_path(self) -> Optional[Path]:
        """Get repository path."""
        return self._repo_path
    
    @property
    def current_branch(self) -> str:
        """Get current branch name."""
        return self._current_branch
    
    @property
    def status(self) -> List[GitFileStatus]:
        """Get current status."""
        return self._status
    
    @property
    def branches(self) -> List[GitBranch]:
        """Get branches."""
        return self._branches
    
    def _run_command(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """
        Run a git command.
        
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if cwd is None:
            cwd = self._repo_path
        
        if cwd is None:
            return (-1, "", "No repository path set")
        
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (-1, "", "Command timed out")
        except FileNotFoundError:
            return (-1, "", "Git not found. Is git installed?")
        except Exception as e:
            return (-1, "", str(e))
    
    def is_git_repo(self, path: Path) -> bool:
        """Check if path is a git repository."""
        git_dir = path / ".git"
        return git_dir.exists()
    
    def open_repository(self, path: Path) -> bool:
        """Open a git repository."""
        if not self.is_git_repo(path):
            self._repo_path = None
            self._signals.error_occurred.emit(f"Not a git repository: {path}")
            return False
        
        self._repo_path = path
        self.refresh_status()
        self._get_current_branch()
        self.refresh_branches()
        
        return True
    
    def refresh_status(self) -> bool:
        """Refresh the repository status."""
        if not self._repo_path:
            return False
        
        code, stdout, stderr = self._run_command(["status", "--porcelain=v1"])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Git error: {stderr}")
            return False
        
        self._status = self._parse_status(stdout)
        self._signals.status_changed.emit()
        return True
    
    def _parse_status(self, output: str) -> List[GitFileStatus]:
        """Parse git status output."""
        statuses = []
        
        for line in output.split('\n'):
            if not line or len(line) < 3:
                continue
            
            # Format: XY filename
            index_status = line[0]
            worktree_status = line[1]
            path = line[3:].strip()
            
            if not path:
                continue
            
            # Determine status character and staged state
            status = ""
            staged = False
            
            # Index (staged) status
            if index_status == 'M':
                status = 'M'
                staged = True
            elif index_status == 'A':
                status = 'A'
                staged = True
            elif index_status == 'D':
                status = 'D'
                staged = True
            elif index_status == 'R':
                status = 'R'
                staged = True
            elif index_status == 'C':
                status = 'C'
                staged = True
            
            # Worktree (unstaged) status
            if worktree_status == 'M':
                status = 'M'
                staged = False
            elif worktree_status == 'D':
                status = 'D'
                staged = False
            
            # Untracked files
            if index_status == '?' and worktree_status == '?':
                status = '?'
                staged = False
            
            # Ignored files
            if index_status == '!' and worktree_status == '!':
                status = '!'
                staged = False
            
            # Handle renames (RR means both staged and unstaged rename)
            old_path = None
            if ' -> ' in path:
                parts = path.split(' -> ')
                old_path = parts[0]
                path = parts[1]
            
            if status:
                statuses.append(GitFileStatus(
                    path=path,
                    status=status,
                    staged=staged,
                    old_path=old_path
                ))
        
        return statuses
    
    def _get_current_branch(self) -> str:
        """Get current branch name."""
        code, stdout, _ = self._run_command(["branch", "--show-current"])
        
        if code == 0 and stdout.strip():
            self._current_branch = stdout.strip()
            return self._current_branch
        
        # Could be in detached HEAD state
        code, stdout, _ = self._run_command(["rev-parse", "--short", "HEAD"])
        if code == 0:
            self._current_branch = f"(detached at {stdout.strip()})"
        
        return self._current_branch
    
    def refresh_branches(self) -> bool:
        """Refresh branches."""
        if not self._repo_path:
            return False
        
        branches = []
        
        # Get local branches
        code, stdout, _ = self._run_command(["branch"])
        if code == 0:
            for line in stdout.split('\n'):
                if not line:
                    continue
                name = line[2:].strip() if line.startswith('* ') else line.strip()
                if name:
                    branches.append(GitBranch(
                        name=name,
                        is_current=line.startswith('*'),
                        is_remote=False
                    ))
        
        # Get remote branches
        code, stdout, _ = self._run_command(["branch", "-r"])
        if code == 0:
            for line in stdout.split('\n'):
                if not line or '->' in line:
                    continue
                name = line.strip()
                if name and not name.endswith('HEAD'):
                    branches.append(GitBranch(
                        name=name,
                        is_current=False,
                        is_remote=True
                    ))
        
        self._branches = branches
        return True
    
    def get_staged_files(self) -> List[GitFileStatus]:
        """Get staged files."""
        return [s for s in self._status if s.staged]
    
    def get_modified_files(self) -> List[GitFileStatus]:
        """Get modified (unstaged) files."""
        return [s for s in self._status if not s.staged and s.status == 'M']
    
    def get_untracked_files(self) -> List[GitFileStatus]:
        """Get untracked files."""
        return [s for s in self._status if s.status == '?']
    
    def stage_file(self, file_path: str) -> bool:
        """Stage a file."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["add", file_path])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to stage: {stderr}")
            return False
        
        self.refresh_status()
        return True
    
    def unstage_file(self, file_path: str) -> bool:
        """Unstage a file."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["reset", "HEAD", "--", file_path])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to unstage: {stderr}")
            return False
        
        self.refresh_status()
        return True
    
    def stage_all(self) -> bool:
        """Stage all changes."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["add", "-A"])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to stage all: {stderr}")
            return False
        
        self.refresh_status()
        return True
    
    def unstage_all(self) -> bool:
        """Unstage all changes."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["reset", "HEAD"])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to unstage all: {stderr}")
            return False
        
        self.refresh_status()
        return True
    
    def commit(self, message: str) -> bool:
        """Create a commit."""
        if not self._repo_path:
            return False
        
        # Check if there are staged changes
        staged = self.get_staged_files()
        if not staged:
            self._signals.error_occurred.emit("No staged changes to commit")
            return False
        
        code, _, stderr = self._run_command(["commit", "-m", message])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to commit: {stderr}")
            return False
        
        self.refresh_status()
        self._signals.commit_created.emit(message)
        return True
    
    def get_commits(self, limit: int = 50) -> List[GitCommit]:
        """Get recent commits."""
        if not self._repo_path:
            return []
        
        # Format: hash|author|email|date|message
        code, stdout, _ = self._run_command([
            "log",
            f"-{limit}",
            "--format=%h|%an|%ae|%at|%s"
        ])
        
        if code != 0:
            return []
        
        commits = []
        
        for line in stdout.split('\n'):
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) >= 5:
                try:
                    timestamp = datetime.fromtimestamp(int(parts[3]))
                except (ValueError, OSError):
                    timestamp = datetime.now()
                
                commits.append(GitCommit(
                    hash=parts[0],
                    short_hash=parts[0],
                    author=parts[1],
                    email=parts[2],
                    date=timestamp,
                    message='|'.join(parts[4:])
                ))
        
        self._commits = commits
        return commits
    
    def get_diff(self, file_path: Optional[str] = None) -> str:
        """Get diff for file or all changes."""
        if not self._repo_path:
            return ""
        
        args = ["diff"]
        if file_path:
            args.append("--")
            args.append(file_path)
        
        code, stdout, _ = self._run_command(args)
        return stdout if code == 0 else ""
    
    def get_staged_diff(self, file_path: Optional[str] = None) -> str:
        """Get diff for staged changes."""
        if not self._repo_path:
            return ""
        
        args = ["diff", "--cached"]
        if file_path:
            args.append("--")
            args.append(file_path)
        
        code, stdout, _ = self._run_command(args)
        return stdout if code == 0 else ""
    
    def checkout_branch(self, branch: str) -> bool:
        """Checkout a branch."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["checkout", branch])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to checkout: {stderr}")
            return False
        
        self._get_current_branch()
        self.refresh_status()
        self._signals.branch_changed.emit(self._current_branch)
        return True
    
    def create_branch(self, branch: str, checkout: bool = True) -> bool:
        """Create a new branch."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["branch", branch])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to create branch: {stderr}")
            return False
        
        if checkout:
            return self.checkout_branch(branch)
        
        self.refresh_branches()
        return True
    
    def delete_branch(self, branch: str, force: bool = False) -> bool:
        """Delete a branch."""
        if not self._repo_path:
            return False
        
        flag = "-D" if force else "-d"
        code, _, stderr = self._run_command(["branch", flag, branch])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to delete branch: {stderr}")
            return False
        
        self.refresh_branches()
        return True
    
    def pull(self) -> bool:
        """Pull from remote."""
        if not self._repo_path:
            return False
        
        code, stdout, stderr = self._run_command(["pull"])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Pull failed: {stderr}")
            return False
        
        self.refresh_status()
        return True
    
    def push(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """Push to remote."""
        if not self._repo_path:
            return False
        
        args = ["push"]
        if remote:
            args.append(remote)
        if branch:
            args.append(branch)
        
        code, stdout, stderr = self._run_command(args)
        
        if code != 0:
            self._signals.error_occurred.emit(f"Push failed: {stderr}")
            return False
        
        return True
    
    def fetch(self, remote: str = "origin") -> bool:
        """Fetch from remote."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["fetch", remote])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Fetch failed: {stderr}")
            return False
        
        return True
    
    def get_remotes(self) -> List[str]:
        """Get list of remote names."""
        if not self._repo_path:
            return []
        
        code, stdout, _ = self._run_command(["remote"])
        
        if code != 0:
            return []
        
        return [r.strip() for r in stdout.split('\n') if r.strip()]
    
    def discard_changes(self, file_path: str) -> bool:
        """Discard changes in a file."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["checkout", "--", file_path])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to discard: {stderr}")
            return False
        
        self.refresh_status()
        return True
    
    def discard_all_changes(self) -> bool:
        """Discard all changes."""
        if not self._repo_path:
            return False
        
        code, _, stderr = self._run_command(["checkout", "--", "."])
        
        if code != 0:
            self._signals.error_occurred.emit(f"Failed to discard: {stderr}")
            return False
        
        self.refresh_status()
        return True