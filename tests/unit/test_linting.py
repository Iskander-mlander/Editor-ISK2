"""
Unit Tests for Linting Module
=============================
Tests for the linting integration module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from core.linting import (
    LinterType, LintResult, LinterConfig, LinterSignals,
    Linter, PyLintLinter, Flake8Linter, BlackLinter,
    ShellCheckLinter, LintingManager
)


class TestLinterType(unittest.TestCase):
    """Test LinterType enum."""
    
    def test_linter_types_defined(self):
        """Test all linter types are defined."""
        self.assertIsNotNone(LinterType.PYLINT)
        self.assertIsNotNone(LinterType.FLAKE8)
        self.assertIsNotNone(LinterType.BLACK)
        self.assertIsNotNone(LinterType.ISORT)
        self.assertIsNotNone(LinterType.SHELLCHECK)


class TestLintResult(unittest.TestCase):
    """Test LintResult dataclass."""
    
    def test_creation(self):
        """Test creating a lint result."""
        result = LintResult(
            line=10,
            column=5,
            severity="error",
            message="Undefined variable 'x'",
            code="E0602",
            linter="pylint"
        )
        
        self.assertEqual(result.line, 10)
        self.assertEqual(result.column, 5)
        self.assertEqual(result.severity, "error")
        self.assertEqual(result.message, "Undefined variable 'x'")
        self.assertEqual(result.code, "E0602")
        self.assertEqual(result.linter, "pylint")
    
    def test_default_values(self):
        """Test default values."""
        result = LintResult(
            line=1,
            column=0,
            severity="info",
            message="Test message"
        )
        
        self.assertEqual(result.code, "")
        self.assertEqual(result.linter, "")


class TestLinterConfig(unittest.TestCase):
    """Test LinterConfig dataclass."""
    
    def test_creation(self):
        """Test creating linter config."""
        config = LinterConfig(
            name="Pylint",
            linter_type=LinterType.PYLINT,
            command=["pylint"],
            file_types=[".py"],
            config_file=".pylintrc",
            install_hint="pip install pylint"
        )
        
        self.assertEqual(config.name, "Pylint")
        self.assertEqual(config.linter_type, LinterType.PYLINT)
        self.assertEqual(config.command, ["pylint"])
        self.assertEqual(config.file_types, [".py"])


class TestLinterSignals(unittest.TestCase):
    """Test LinterSignals."""
    
    def test_signals_defined(self):
        """Test all signals are defined."""
        signals = LinterSignals()
        
        # Check signals exist
        self.assertTrue(hasattr(signals, 'lint_started'))
        self.assertTrue(hasattr(signals, 'lint_finished'))
        self.assertTrue(hasattr(signals, 'lint_error'))


class TestPyLintLinter(unittest.TestCase):
    """Test PyLintLinter class."""
    
    def test_initialization(self):
        """Test initialization."""
        linter = PyLintLinter()
        
        self.assertEqual(linter.config.name, "Pylint")
        self.assertEqual(linter.config.linter_type, LinterType.PYLINT)
        self.assertEqual(linter.config.file_types, [".py"])
    
    def test_is_available(self):
        """Test availability check."""
        linter = PyLintLinter()
        
        # Mock shutil.which
        with patch('shutil.which', return_value='/usr/bin/pylint'):
            result = linter.is_available()
            self.assertTrue(result)
        
        with patch('shutil.which', return_value=None):
            result = linter.is_available()
            # Should return cached result from first call
            self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_lint_file_empty(self, mock_run):
        """Test linting when linter not available."""
        linter = PyLintLinter()
        
        with patch.object(linter, 'is_available', return_value=False):
            results = linter.lint_file("/path/to/file.py")
            self.assertEqual(results, [])


class TestFlake8Linter(unittest.TestCase):
    """Test Flake8Linter class."""
    
    def test_initialization(self):
        """Test initialization."""
        linter = Flake8Linter()
        
        self.assertEqual(linter.config.name, "Flake8")
        self.assertEqual(linter.config.linter_type, LinterType.FLAKE8)


class TestBlackLinter(unittest.TestCase):
    """Test BlackLinter class."""
    
    def test_initialization(self):
        """Test initialization."""
        linter = BlackLinter()
        
        self.assertEqual(linter.config.name, "Black")
        self.assertEqual(linter.config.linter_type, LinterType.BLACK)


class TestShellCheckLinter(unittest.TestCase):
    """Test ShellCheckLinter class."""
    
    def test_initialization(self):
        """Test initialization."""
        linter = ShellCheckLinter()
        
        self.assertEqual(linter.config.name, "ShellCheck")
        self.assertEqual(linter.config.linter_type, LinterType.SHELLCHECK)
        self.assertEqual(linter.config.file_types, [".sh", ".bash"])


class TestLintingManager(unittest.TestCase):
    """Test LintingManager class."""
    
    def test_initialization(self):
        """Test initialization."""
        manager = LintingManager()
        
        # Check default linters are registered
        self.assertIn(LinterType.PYLINT, manager._linters)
        self.assertIn(LinterType.FLAKE8, manager._linters)
        self.assertIn(LinterType.BLACK, manager._linters)
        self.assertIn(LinterType.SHELLCHECK, manager._linters)
    
    def test_signals_exist(self):
        """Test manager has signals."""
        manager = LintingManager()
        self.assertTrue(hasattr(manager, 'signals'))
    
    def test_get_linter_for_python_file(self):
        """Test getting linter for Python file."""
        manager = LintingManager()
        
        with patch.object(manager._linters[LinterType.PYLINT], 'is_available', return_value=True):
            linter = manager.get_linter_for_file("/path/to/file.py")
            self.assertIsNotNone(linter)
    
    def test_get_linter_for_shell_file(self):
        """Test getting linter for shell file."""
        manager = LintingManager()
        
        with patch.object(manager._linters[LinterType.SHELLCHECK], 'is_available', return_value=True):
            linter = manager.get_linter_for_file("/path/to/script.sh")
            self.assertIsNotNone(linter)
    
    def test_get_linter_for_unknown_file(self):
        """Test getting linter for unknown file type."""
        manager = LintingManager()
        
        linter = manager.get_linter_for_file("/path/to/file.xyz")
        self.assertIsNone(linter)


class TestLinterBaseClass(unittest.TestCase):
    """Test base Linter class."""
    
    def test_run_command_success(self):
        """Test successful command execution."""
        config = LinterConfig(
            name="Test",
            linter_type=LinterType.PYLINT,
            command=["echo", "test"]
        )
        linter = Linter(config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")
            code, stdout, stderr = linter._run_command(["echo", "test"])
            
            self.assertEqual(code, 0)
            self.assertEqual(stdout, "output")
    
    def test_run_command_timeout(self):
        """Test command timeout."""
        config = LinterConfig(
            name="Test",
            linter_type=LinterType.PYLINT,
            command=["sleep", "10"]
        )
        linter = Linter(config)
        
        with patch('subprocess.run', side_effect=Exception("Timeout")):
            code, stdout, stderr = linter._run_command(["sleep", "10"])
            self.assertEqual(code, -1)


if __name__ == '__main__':
    unittest.main()