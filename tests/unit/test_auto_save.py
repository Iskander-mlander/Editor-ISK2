"""
Unit Tests for Auto-Save Module
================================
Tests for the auto-save functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from core.editor.auto_save import AutoSaveManager, AutoSaveConfig, AutoSaveSignals


class TestAutoSaveConfig(unittest.TestCase):
    """Test AutoSaveConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = AutoSaveConfig()
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.interval_seconds, 30)
        self.assertTrue(config.save_unsaved_only)
    
    def test_custom_values(self):
        """Test custom configuration."""
        config = AutoSaveConfig(enabled=False, interval_seconds=60)
        
        self.assertFalse(config.enabled)
        self.assertEqual(config.interval_seconds, 60)


class TestAutoSaveSignals(unittest.TestCase):
    """Test AutoSaveSignals."""
    
    def test_signals_defined(self):
        """Test all signals are defined."""
        signals = AutoSaveSignals()
        
        self.assertTrue(hasattr(signals, 'file_auto_saved'))
        self.assertTrue(hasattr(signals, 'auto_save_enabled'))
        self.assertTrue(hasattr(signals, 'auto_save_error'))


class TestAutoSaveManager(unittest.TestCase):
    """Test AutoSaveManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoSaveManager()
    
    def test_initialization(self):
        """Test initialization."""
        self.assertTrue(self.manager.config.enabled)
        self.assertEqual(self.manager.config.interval_seconds, 30)
    
    def test_signals_exist(self):
        """Test manager has signals."""
        self.assertTrue(hasattr(self.manager, 'signals'))
    
    def test_track_file(self):
        """Test tracking a file."""
        self.manager.track_file("/test/file.py", "print('hello')", True)
        
        self.assertTrue(self.manager.is_tracked("/test/file.py"))
    
    def test_untrack_file(self):
        """Test untracking a file."""
        self.manager.track_file("/test/file.py", "print('hello')", True)
        self.manager.untrack_file("/test/file.py")
        
        self.assertFalse(self.manager.is_tracked("/test/file.py"))
    
    def test_track_unmodified_file(self):
        """Test tracking unmodified file."""
        self.manager.track_file("/test/file.py", "print('hello')", False)
        
        self.assertFalse(self.manager.is_tracked("/test/file.py"))
    
    def test_get_tracked_count(self):
        """Test getting tracked file count."""
        self.manager.track_file("/test/file1.py", "content1", True)
        self.manager.track_file("/test/file2.py", "content2", True)
        
        self.assertEqual(self.manager.get_tracked_count(), 2)
    
    def test_set_config(self):
        """Test setting configuration."""
        config = AutoSaveConfig(enabled=False, interval_seconds=120)
        self.manager.set_config(config)
        
        self.assertEqual(self.manager.config.interval_seconds, 120)
    
    @patch('os.path.exists')
    @patch('builtins.open', create=True)
    def test_on_timer_saves_files(self, mock_open, mock_exists):
        """Test timer saves tracked files."""
        mock_exists.return_value = True
        
        self.manager.track_file("/test/file.py", "print('hello')", True)
        
        with patch('shutil.copy2'):
            self.manager._on_timer()
        
        mock_open.assert_called()
    
    def test_is_tracked_false(self):
        """Test is_tracked returns False for non-tracked file."""
        self.assertFalse(self.manager.is_tracked("/nonexistent/file.py"))


if __name__ == '__main__':
    unittest.main()