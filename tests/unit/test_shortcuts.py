"""
Test: Shortcuts Manager
=======================
Tests for core/utils/shortcuts.py
"""

import unittest
from core.utils.shortcuts import (
    ShortcutManager, KeyboardShortcut, ShortcutCategory,
    ShortcutManagerSignals
)


class TestKeyboardShortcut(unittest.TestCase):
    """Test KeyboardShortcut dataclass."""
    
    def test_creation(self):
        """Test creating a KeyboardShortcut."""
        shortcut = KeyboardShortcut(
            id="test.action",
            name="Test Action",
            key_sequence="Ctrl+T",
            category=ShortcutCategory.EDITING,
            description="A test shortcut",
            enabled=True
        )
        
        self.assertEqual(shortcut.id, "test.action")
        self.assertEqual(shortcut.name, "Test Action")
        self.assertEqual(shortcut.key_sequence, "Ctrl+T")
        self.assertEqual(shortcut.category, ShortcutCategory.EDITING)
        self.assertEqual(shortcut.description, "A test shortcut")
        self.assertTrue(shortcut.enabled)
    
    def test_default_values(self):
        """Test default values."""
        shortcut = KeyboardShortcut(
            id="test.action",
            name="Test",
            key_sequence="Ctrl+T",
            category=ShortcutCategory.EDITING
        )
        
        self.assertEqual(shortcut.description, "")
        self.assertIsNone(shortcut.handler)
        self.assertTrue(shortcut.enabled)


class TestShortcutManager(unittest.TestCase):
    """Test ShortcutManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ShortcutManager()
    
    def test_initialization(self):
        """Test manager initializes with default shortcuts."""
        # Should have default shortcuts registered
        all_shortcuts = self.manager.get_all_shortcuts()
        self.assertGreater(len(all_shortcuts), 0)
    
    def test_get_shortcut(self):
        """Test getting a shortcut by ID."""
        shortcut = self.manager.get_shortcut("edit.undo")
        self.assertIsNotNone(shortcut)
        self.assertEqual(shortcut.name, "Undo")
    
    def test_get_shortcut_not_found(self):
        """Test getting non-existent shortcut returns None."""
        shortcut = self.manager.get_shortcut("nonexistent.action")
        self.assertIsNone(shortcut)
    
    def test_get_shortcuts_by_category(self):
        """Test getting shortcuts by category."""
        editing_shortcuts = self.manager.get_shortcuts_by_category(
            ShortcutCategory.EDITING
        )
        
        self.assertIsInstance(editing_shortcuts, list)
        # Should have undo, redo, cut, copy, paste at minimum
        self.assertGreaterEqual(len(editing_shortcuts), 5)
    
    def test_shortcut_categories(self):
        """Test all category types have shortcuts."""
        for category in ShortcutCategory:
            shortcuts = self.manager.get_shortcuts_by_category(category)
            # At least some categories should have shortcuts
            if category in [ShortcutCategory.EDITING, ShortcutCategory.FILE, 
                           ShortcutCategory.SEARCH]:
                self.assertGreater(len(shortcuts), 0)
    
    def test_update_shortcut(self):
        """Test updating a shortcut key sequence."""
        result = self.manager.update_shortcut("edit.undo", "Ctrl+Shift+Z")
        self.assertTrue(result)
        
        # Verify the change
        shortcut = self.manager.get_shortcut("edit.undo")
        self.assertEqual(shortcut.key_sequence, "Ctrl+Shift+Z")
    
    def test_update_shortcut_not_found(self):
        """Test updating non-existent shortcut returns False."""
        result = self.manager.update_shortcut("nonexistent.action", "Ctrl+X")
        self.assertFalse(result)
    
    def test_set_shortcut_enabled(self):
        """Test enabling/disabling shortcuts."""
        result = self.manager.set_shortcut_enabled("edit.undo", False)
        self.assertTrue(result)
        
        shortcut = self.manager.get_shortcut("edit.undo")
        self.assertFalse(shortcut.enabled)
    
    def test_set_shortcut_enabled_not_found(self):
        """Test enabling non-existent shortcut returns False."""
        result = self.manager.set_shortcut_enabled("nonexistent.action", False)
        self.assertFalse(result)
    
    def test_get_key_sequence_for_id(self):
        """Test getting key sequence for shortcut ID."""
        key = self.manager.get_key_sequence_for_id("edit.copy")
        self.assertIsNotNone(key)
        self.assertEqual(key, "Ctrl+C")
    
    def test_to_dict(self):
        """Test exporting shortcuts to dictionary."""
        data = self.manager.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertIn("edit.undo", data)
        self.assertIn("file.save", data)
    
    def test_from_dict(self):
        """Test importing shortcuts from dictionary."""
        original_key = self.manager.get_key_sequence_for_id("edit.copy")
        
        # Modify via from_dict
        new_data = {"edit.copy": {"key_sequence": "Ctrl+Shift+C", "enabled": True}}
        self.manager.from_dict(new_data)
        
        # Verify change
        new_key = self.manager.get_key_sequence_for_id("edit.copy")
        self.assertEqual(new_key, "Ctrl+Shift+C")
        
        # Restore
        self.manager.from_dict({"edit.copy": {"key_sequence": original_key, "enabled": True}})


class TestShortcutCategories(unittest.TestCase):
    """Test ShortcutCategory enum."""
    
    def test_all_categories_defined(self):
        """Test all expected categories are defined."""
        expected = [
            ShortcutCategory.EDITING,
            ShortcutCategory.NAVIGATION,
            ShortcutCategory.FILE,
            ShortcutCategory.VIEW,
            ShortcutCategory.SEARCH,
            ShortcutCategory.DEBUG,
            ShortcutCategory.TOOLS
        ]
        
        for cat in expected:
            self.assertIsNotNone(cat)


class TestShortcutManagerSignals(unittest.TestCase):
    """Test ShortcutManagerSignals."""
    
    def test_signals_defined(self):
        """Test all required signals are defined."""
        signals = ShortcutManagerSignals()
        
        self.assertTrue(hasattr(signals, 'shortcut_executed'))
        self.assertTrue(hasattr(signals, 'shortcut_registered'))
        self.assertTrue(hasattr(signals, 'shortcut_unregistered'))


if __name__ == '__main__':
    unittest.main()