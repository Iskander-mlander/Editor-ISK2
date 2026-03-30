"""
Unit Tests for Bookmarks Module
================================
Tests for the bookmarks functionality.
"""

import unittest

from core.editor.bookmarks import Bookmark, BookmarkManager, BookmarkSignals


class TestBookmark(unittest.TestCase):
    """Test Bookmark dataclass."""
    
    def test_creation(self):
        """Test creating a bookmark."""
        bm = Bookmark(file_path="/test/file.py", line=10, label="Important", color="#FF0000")
        
        self.assertEqual(bm.file_path, "/test/file.py")
        self.assertEqual(bm.line, 10)
        self.assertEqual(bm.label, "Important")
        self.assertEqual(bm.color, "#FF0000")
    
    def test_default_values(self):
        """Test default values."""
        bm = Bookmark(file_path="/test/file.py", line=5)
        
        self.assertEqual(bm.label, "")
        self.assertEqual(bm.color, "#FFD700")
    
    def test_equality(self):
        """Test bookmark equality."""
        bm1 = Bookmark(file_path="/test/file.py", line=10)
        bm2 = Bookmark(file_path="/test/file.py", line=10)
        bm3 = Bookmark(file_path="/test/file.py", line=20)
        
        self.assertEqual(bm1, bm2)
        self.assertNotEqual(bm1, bm3)
    
    def test_hash(self):
        """Test bookmark hash."""
        bm1 = Bookmark(file_path="/test/file.py", line=10)
        bm2 = Bookmark(file_path="/test/file.py", line=10)
        
        self.assertEqual(hash(bm1), hash(bm2))


class TestBookmarkSignals(unittest.TestCase):
    """Test BookmarkSignals."""
    
    def test_signals_defined(self):
        """Test all signals are defined."""
        signals = BookmarkSignals()
        
        self.assertTrue(hasattr(signals, 'bookmark_added'))
        self.assertTrue(hasattr(signals, 'bookmark_removed'))
        self.assertTrue(hasattr(signals, 'bookmarks_changed'))


class TestBookmarkManager(unittest.TestCase):
    """Test BookmarkManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = BookmarkManager()
    
    def test_initialization(self):
        """Test initialization."""
        self.assertEqual(self.manager._bookmarks, {})
    
    def test_signals_exist(self):
        """Test manager has signals."""
        self.assertTrue(hasattr(self.manager, 'signals'))
    
    def test_add_bookmark(self):
        """Test adding a bookmark."""
        result = self.manager.add_bookmark("/test/file.py", 10, "Test label")
        
        self.assertTrue(result)
        self.assertTrue(self.manager.has_bookmark("/test/file.py", 10))
    
    def test_add_duplicate_bookmark(self):
        """Test adding duplicate bookmark."""
        self.manager.add_bookmark("/test/file.py", 10)
        result = self.manager.add_bookmark("/test/file.py", 10)
        
        self.assertFalse(result)
    
    def test_remove_bookmark(self):
        """Test removing a bookmark."""
        self.manager.add_bookmark("/test/file.py", 10)
        result = self.manager.remove_bookmark("/test/file.py", 10)
        
        self.assertTrue(result)
        self.assertFalse(self.manager.has_bookmark("/test/file.py", 10))
    
    def test_remove_nonexistent_bookmark(self):
        """Test removing non-existent bookmark."""
        result = self.manager.remove_bookmark("/test/file.py", 10)
        
        self.assertFalse(result)
    
    def test_toggle_bookmark_add(self):
        """Test toggling bookmark (add)."""
        result = self.manager.toggle_bookmark("/test/file.py", 10)
        
        self.assertTrue(result)
        self.assertTrue(self.manager.has_bookmark("/test/file.py", 10))
    
    def test_toggle_bookmark_remove(self):
        """Test toggling bookmark (remove)."""
        self.manager.add_bookmark("/test/file.py", 10)
        result = self.manager.toggle_bookmark("/test/file.py", 10)
        
        self.assertTrue(result)
        self.assertFalse(self.manager.has_bookmark("/test/file.py", 10))
    
    def test_get_bookmarks(self):
        """Test getting bookmarks for a file."""
        self.manager.add_bookmark("/test/file.py", 10)
        self.manager.add_bookmark("/test/file.py", 20)
        self.manager.add_bookmark("/test/file.py", 5)
        
        bookmarks = self.manager.get_bookmarks("/test/file.py")
        
        self.assertEqual(len(bookmarks), 3)
        # Should be sorted by line
        self.assertEqual(bookmarks[0].line, 5)
        self.assertEqual(bookmarks[1].line, 10)
        self.assertEqual(bookmarks[2].line, 20)
    
    def test_get_bookmarks_empty_file(self):
        """Test getting bookmarks for file with none."""
        bookmarks = self.manager.get_bookmarks("/test/nofile.py")
        
        self.assertEqual(bookmarks, [])
    
    def test_get_all_bookmarks(self):
        """Test getting all bookmarks."""
        self.manager.add_bookmark("/test/file1.py", 10)
        self.manager.add_bookmark("/test/file2.py", 20)
        
        all_bookmarks = self.manager.get_all_bookmarks()
        
        self.assertEqual(len(all_bookmarks), 2)
    
    def test_clear_file_bookmarks(self):
        """Test clearing bookmarks for a file."""
        self.manager.add_bookmark("/test/file.py", 10)
        self.manager.add_bookmark("/test/file.py", 20)
        
        self.manager.clear_file_bookmarks("/test/file.py")
        
        self.assertEqual(self.manager.get_bookmarks("/test/file.py"), [])
    
    def test_clear_all(self):
        """Test clearing all bookmarks."""
        self.manager.add_bookmark("/test/file1.py", 10)
        self.manager.add_bookmark("/test/file2.py", 20)
        
        self.manager.clear_all()
        
        self.assertEqual(self.manager.get_all_bookmarks(), {})
    
    def test_next_bookmark(self):
        """Test getting next bookmark."""
        self.manager.add_bookmark("/test/file.py", 10)
        self.manager.add_bookmark("/test/file.py", 30)
        self.manager.add_bookmark("/test/file.py", 50)
        
        next_line = self.manager.next_bookmark("/test/file.py", 20)
        self.assertEqual(next_line, 30)
    
    def test_next_bookmark_none(self):
        """Test next bookmark when none after."""
        self.manager.add_bookmark("/test/file.py", 10)
        
        next_line = self.manager.next_bookmark("/test/file.py", 20)
        self.assertIsNone(next_line)
    
    def test_previous_bookmark(self):
        """Test getting previous bookmark."""
        self.manager.add_bookmark("/test/file.py", 10)
        self.manager.add_bookmark("/test/file.py", 30)
        self.manager.add_bookmark("/test/file.py", 50)
        
        prev_line = self.manager.previous_bookmark("/test/file.py", 40)
        self.assertEqual(prev_line, 30)
    
    def test_previous_bookmark_none(self):
        """Test previous bookmark when none before."""
        self.manager.add_bookmark("/test/file.py", 10)
        
        prev_line = self.manager.previous_bookmark("/test/file.py", 5)
        self.assertIsNone(prev_line)


if __name__ == '__main__':
    unittest.main()