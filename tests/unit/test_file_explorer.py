"""
Unit Tests for File Explorer
=============================
Tests for the file explorer widget.
Note: Full widget tests require QApplication, so we test the signals class.
"""

import unittest
from unittest.mock import Mock


class TestFileExplorerSignals(unittest.TestCase):
    """Test FileExplorerSignals class."""
    
    def test_signals_defined(self):
        """Test all signals are defined."""
        # Just verify class attributes exist
        from ui.widgets.file_explorer import FileExplorerSignals
        
        # Check class-level signal attributes exist
        self.assertTrue(hasattr(FileExplorerSignals, 'file_selected'))
        self.assertTrue(hasattr(FileExplorerSignals, 'directory_changed'))
        self.assertTrue(hasattr(FileExplorerSignals, 'file_created'))
        self.assertTrue(hasattr(FileExplorerSignals, 'file_deleted'))
        self.assertTrue(hasattr(FileExplorerSignals, 'file_renamed'))


if __name__ == '__main__':
    unittest.main()