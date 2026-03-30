"""
Unit Tests for Split Editor
============================
Tests for the split editor functionality.
Note: Full widget tests require QApplication with display.
"""

import unittest


class TestEditorSplit(unittest.TestCase):
    """Test EditorSplit dataclass."""
    
    def test_creation(self):
        """Test creating an EditorSplit."""
        from ui.widgets.split_editor import EditorSplit
        from unittest.mock import Mock
        
        editor = Mock()
        highlighter = Mock()
        
        split = EditorSplit(
            editor=editor,
            highlighter=highlighter,
            file_path="/test/file.py",
            is_modified=True
        )
        
        self.assertEqual(split.file_path, "/test/file.py")
        self.assertTrue(split.is_modified)
    
    def test_default_values(self):
        """Test default values."""
        from ui.widgets.split_editor import EditorSplit
        from unittest.mock import Mock
        
        editor = Mock()
        highlighter = Mock()
        
        split = EditorSplit(
            editor=editor,
            highlighter=highlighter
        )
        
        self.assertIsNone(split.file_path)
        self.assertFalse(split.is_modified)


class TestSplitEditorSignals(unittest.TestCase):
    """Test SplitEditorSignals class."""
    
    def test_signals_defined(self):
        """Test all signals are defined."""
        # Just check class attributes exist (can't instantiate without QApplication)
        from ui.widgets.split_editor import SplitEditorSignals
        
        # Verify class has signal attributes
        self.assertTrue(hasattr(SplitEditorSignals, 'split_created'))
        self.assertTrue(hasattr(SplitEditorSignals, 'split_closed'))
        self.assertTrue(hasattr(SplitEditorSignals, 'split_focused'))
        self.assertTrue(hasattr(SplitEditorSignals, 'editor_changed'))


class TestSplitEditorManager(unittest.TestCase):
    """Test SplitEditorManager class."""
    
    def test_class_exists(self):
        """Test SplitEditorManager class exists."""
        from ui.widgets.split_editor import SplitEditorManager
        
        self.assertTrue(hasattr(SplitEditorManager, 'create_split'))
        self.assertTrue(hasattr(SplitEditorManager, 'close_split'))
        self.assertTrue(hasattr(SplitEditorManager, 'get_split_count'))
        self.assertTrue(hasattr(SplitEditorManager, 'get_active_split'))
        self.assertTrue(hasattr(SplitEditorManager, 'split_horizontal'))
        self.assertTrue(hasattr(SplitEditorManager, 'split_vertical'))
        self.assertTrue(hasattr(SplitEditorManager, 'close_active_split'))
        self.assertTrue(hasattr(SplitEditorManager, 'focus_next_split'))
        self.assertTrue(hasattr(SplitEditorManager, 'focus_previous_split'))


class TestCreateSplitManager(unittest.TestCase):
    """Test create_split_manager function."""
    
    def test_function_exists(self):
        """Test function exists."""
        from ui.widgets.split_editor import create_split_manager
        
        self.assertTrue(callable(create_split_manager))


if __name__ == '__main__':
    unittest.main()