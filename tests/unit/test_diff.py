"""
Unit Tests for Diff Module
===========================
Tests for the diff/compare functionality.
"""

import unittest

from core.utils.diff import DiffLine, DiffChunk, DiffResult, DiffComputer


class TestDiffLine(unittest.TestCase):
    """Test DiffLine dataclass."""
    
    def test_creation(self):
        """Test creating a DiffLine."""
        line = DiffLine(
            type="added",
            content="new line",
            old_line_num=None,
            new_line_num=10
        )
        
        self.assertEqual(line.type, "added")
        self.assertEqual(line.content, "new line")
        self.assertIsNone(line.old_line_num)
        self.assertEqual(line.new_line_num, 10)
    
    def test_default_values(self):
        """Test default values."""
        line = DiffLine(type="unchanged", content="test")
        
        self.assertIsNone(line.old_line_num)
        self.assertIsNone(line.new_line_num)


class TestDiffChunk(unittest.TestCase):
    """Test DiffChunk dataclass."""
    
    def test_creation(self):
        """Test creating a DiffChunk."""
        lines = [
            DiffLine(type="removed", content="old", old_line_num=1),
            DiffLine(type="added", content="new", new_line_num=2)
        ]
        
        chunk = DiffChunk(
            old_start=1,
            old_count=1,
            new_start=2,
            new_count=1,
            lines=lines
        )
        
        self.assertEqual(chunk.old_start, 1)
        self.assertEqual(chunk.old_count, 1)
        self.assertEqual(chunk.new_start, 2)
        self.assertEqual(chunk.new_count, 1)
        self.assertEqual(len(chunk.lines), 2)


class TestDiffResult(unittest.TestCase):
    """Test DiffResult class."""
    
    def test_initial_state(self):
        """Test initial state."""
        result = DiffResult()
        
        self.assertEqual(result.chunks, [])
        self.assertEqual(result.total_added, 0)
        self.assertEqual(result.total_removed, 0)
    
    def test_has_changes_false(self):
        """Test has_changes returns False."""
        result = DiffResult()
        
        self.assertFalse(result.has_changes)
    
    def test_has_changes_true_added(self):
        """Test has_changes returns True when added."""
        result = DiffResult()
        result.total_added = 5
        
        self.assertTrue(result.has_changes)
    
    def test_has_changes_true_removed(self):
        """Test has_changes returns True when removed."""
        result = DiffResult()
        result.total_removed = 3
        
        self.assertTrue(result.has_changes)


class TestDiffComputer(unittest.TestCase):
    """Test DiffComputer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.computer = DiffComputer()
    
    def test_identical_text(self):
        """Test diff of identical text."""
        text = "line1\nline2\nline3\n"
        result = self.computer.compute_text_diff(text, text)
        
        self.assertFalse(result.has_changes)
    
    def test_added_lines(self):
        """Test diff with added lines."""
        old = "line1\nline2\n"
        new = "line1\nline2\nline3\n"
        
        result = self.computer.compute_text_diff(old, new)
        
        self.assertTrue(result.has_changes)
        self.assertEqual(result.total_added, 1)
    
    def test_removed_lines(self):
        """Test diff with removed lines."""
        old = "line1\nline2\nline3\n"
        new = "line1\nline2\n"
        
        result = self.computer.compute_text_diff(old, new)
        
        self.assertTrue(result.has_changes)
        self.assertEqual(result.total_removed, 1)
    
    def test_modified_lines(self):
        """Test diff with modified lines."""
        old = "line1\nold line\nline3\n"
        new = "line1\nnew line\nline3\n"
        
        result = self.computer.compute_text_diff(old, new)
        
        self.assertTrue(result.has_changes)
        self.assertTrue(result.total_added > 0)
        self.assertTrue(result.total_removed > 0)
    
    def test_empty_old(self):
        """Test diff with empty old text."""
        old = ""
        new = "new line\n"
        
        result = self.computer.compute_text_diff(old, new)
        
        self.assertTrue(result.has_changes)
        self.assertEqual(result.total_added, 1)
    
    def test_empty_new(self):
        """Test diff with empty new text."""
        old = "old line\n"
        new = ""
        
        result = self.computer.compute_text_diff(old, new)
        
        self.assertTrue(result.has_changes)
        self.assertEqual(result.total_removed, 1)
    
    def test_both_empty(self):
        """Test diff with both empty."""
        result = self.computer.compute_text_diff("", "")
        
        self.assertFalse(result.has_changes)
    
    def test_multiline_diff(self):
        """Test diff with multiple changes."""
        old = "start\nmiddle\nend\n"
        new = "start\nchanged\nend\n"
        
        result = self.computer.compute_text_diff(old, new)
        
        self.assertTrue(result.has_changes)
        self.assertIsNotNone(result.chunks)


if __name__ == '__main__':
    unittest.main()