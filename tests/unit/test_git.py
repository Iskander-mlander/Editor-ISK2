"""
Test: Git Client
================
Tests for features/git/client.py
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestGitFileStatus(unittest.TestCase):
    """Test GitFileStatus dataclass."""
    
    def test_creation(self):
        """Test creating a GitFileStatus."""
        from features.git import GitFileStatus
        
        status = GitFileStatus(path="test.py", status="M", staged=False)
        self.assertEqual(status.path, "test.py")
        self.assertEqual(status.status, "M")
        self.assertFalse(status.staged)
    
    def test_with_old_path(self):
        """Test GitFileStatus with rename."""
        from features.git import GitFileStatus
        
        status = GitFileStatus(
            path="new.py",
            status="R",
            staged=True,
            old_path="old.py"
        )
        self.assertEqual(status.old_path, "old.py")


class TestGitClient(unittest.TestCase):
    """Test GitClient functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from features.git import GitClient
        self.client = GitClient()
    
    def test_initialization(self):
        """Test client initializes correctly."""
        self.assertIsNone(self.client.repo_path)
        self.assertEqual(self.client.current_branch, "")
    
    def test_is_not_git_repo(self):
        """Test non-git directory detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertFalse(self.client.is_git_repo(Path(tmpdir)))
    
    def test_get_staged_files(self):
        """Test getting staged files returns empty list initially."""
        staged = self.client.get_staged_files()
        self.assertIsInstance(staged, list)
        self.assertEqual(len(staged), 0)
    
    def test_get_modified_files(self):
        """Test getting modified files returns empty list initially."""
        modified = self.client.get_modified_files()
        self.assertIsInstance(modified, list)
        self.assertEqual(len(modified), 0)
    
    def test_get_untracked_files(self):
        """Test getting untracked files returns empty list initially."""
        untracked = self.client.get_untracked_files()
        self.assertIsInstance(untracked, list)
        self.assertEqual(len(untracked), 0)
    
    def test_get_remotes_empty(self):
        """Test getting remotes returns empty when no repo."""
        remotes = self.client.get_remotes()
        self.assertIsInstance(remotes, list)
        self.assertEqual(len(remotes), 0)
    
    def test_signals_exist(self):
        """Test client has required signals."""
        from features.git import GitSignals
        self.assertIsInstance(self.client.signals, GitSignals)


class TestGitCommit(unittest.TestCase):
    """Test GitCommit dataclass."""
    
    def test_creation(self):
        """Test creating a GitCommit."""
        from features.git import GitCommit
        from datetime import datetime
        
        commit = GitCommit(
            hash="abc123",
            short_hash="abc123",
            author="Test User",
            email="test@example.com",
            date=datetime.now(),
            message="Test commit"
        )
        
        self.assertEqual(commit.hash, "abc123")
        self.assertEqual(commit.short_hash, "abc123")
        self.assertEqual(commit.author, "Test User")
        self.assertEqual(commit.message, "Test commit")


class TestGitBranch(unittest.TestCase):
    """Test GitBranch dataclass."""
    
    def test_creation(self):
        """Test creating a GitBranch."""
        from features.git import GitBranch
        
        branch = GitBranch(
            name="main",
            is_current=True,
            is_remote=False
        )
        
        self.assertEqual(branch.name, "main")
        self.assertTrue(branch.is_current)
        self.assertFalse(branch.is_remote)


class TestGitClientCommands(unittest.TestCase):
    """Test GitClient command execution."""
    
    def setUp(self):
        """Set up test fixtures."""
        from features.git import GitClient
        self.client = GitClient()
    
    def test_run_command_returns_tuple(self):
        """Test _run_command returns correct tuple format."""
        result = self.client._run_command(["--version"])
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], int)  # return code
        self.assertIsInstance(result[1], str)  # stdout
        self.assertIsInstance(result[2], str)  # stderr
    
    def test_run_command_no_repo(self):
        """Test command fails gracefully when no repo set."""
        result = self.client._run_command(["status"])
        
        # Should return error
        self.assertEqual(result[0], -1)
        self.assertIn("No repository path set", result[2])


class TestGitSignals(unittest.TestCase):
    """Test GitSignals functionality."""
    
    def test_signals_defined(self):
        """Test all required signals are defined."""
        from PyQt6.QtCore import pyqtSignal
        from features.git import GitSignals
        
        signals = GitSignals()
        
        # Check signals exist
        self.assertTrue(hasattr(signals, 'status_changed'))
        self.assertTrue(hasattr(signals, 'branch_changed'))
        self.assertTrue(hasattr(signals, 'commit_created'))
        self.assertTrue(hasattr(signals, 'error_occurred'))


if __name__ == '__main__':
    unittest.main()