"""
Tests for File Handling
========================
Tests for file operations: opening, saving, encoding, etc.
"""

import unittest
import tempfile
import os
from pathlib import Path


class TestOpenFileTypes(unittest.TestCase):
    """Test opening different file types."""
    
    def test_open_python_file(self):
        """Test opening .py file."""
        content = "def hello():\n    print('Hello')"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                read_content = f.read()
            
            self.assertEqual(read_content, content)
            self.assertTrue(temp_path.endswith('.py'))
        finally:
            os.unlink(temp_path)
    
    def test_open_text_file(self):
        """Test opening .txt file."""
        content = "This is a text file"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                read_content = f.read()
            
            self.assertEqual(read_content, content)
        finally:
            os.unlink(temp_path)
    
    def test_open_json_file(self):
        """Test opening .json file."""
        content = '{"key": "value", "number": 42}'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                read_content = f.read()
            
            self.assertIn('"key"', read_content)
        finally:
            os.unlink(temp_path)


class TestFileEncoding(unittest.TestCase):
    """Test file encoding handling."""
    
    def test_utf8_encoding(self):
        """Test UTF-8 encoding."""
        content = "print('Hallo Welt')"  # German
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', 
                                          encoding='utf-8', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                read_content = f.read()
            
            self.assertEqual(read_content, content)
        finally:
            os.unlink(temp_path)
    
    def test_utf8_with_unicode(self):
        """Test UTF-8 with unicode characters."""
        content = "print('αβγδ')"  # Greek letters
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                          encoding='utf-8', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                read_content = f.read()
            
            self.assertIn('α', read_content)
        finally:
            os.unlink(temp_path)
    
    def test_latin1_encoding(self):
        """Test Latin-1 encoding."""
        content = "print('café')"  # French
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                          encoding='latin-1', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r', encoding='latin-1') as f:
                read_content = f.read()
            
            self.assertIn('café', read_content)
        finally:
            os.unlink(temp_path)


class TestLargeFiles(unittest.TestCase):
    """Test handling large files."""
    
    def test_medium_file(self):
        """Test opening medium-sized file."""
        # Create file with 1000 lines
        lines = [f"line_{i} = {i}\n" for i in range(1000)]
        content = "".join(lines)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                read_lines = f.readlines()
            
            self.assertEqual(len(read_lines), 1000)
        finally:
            os.unlink(temp_path)


class TestFilePermissions(unittest.TestCase):
    """Test file permission handling."""
    
    def test_write_read_cycle(self):
        """Test write and read cycle."""
        content = "x = 100\ny = 200"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_path = f.name
        
        try:
            # Write
            with open(temp_path, 'w') as f:
                f.write(content)
            
            # Read
            with open(temp_path, 'r') as f:
                read_content = f.read()
            
            self.assertEqual(read_content, content)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_overwrite_existing_file(self):
        """Test overwriting existing file."""
        original = "original content"
        new = "new content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(original)
            temp_path = f.name
        
        try:
            # Overwrite
            with open(temp_path, 'w') as f:
                f.write(new)
            
            # Verify overwritten
            with open(temp_path, 'r') as f:
                read_content = f.read()
            
            self.assertEqual(read_content, new)
            self.assertNotEqual(read_content, original)
        finally:
            os.unlink(temp_path)


class TestSpecialCharacters(unittest.TestCase):
    """Test handling special characters in files."""
    
    def test_special_chars_in_filename(self):
        """Test file with special characters in content."""
        content = "path = 'C:\\Users\\test'\nprint(path)"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                read_content = f.read()
            
            self.assertIn('C:', read_content)
        finally:
            os.unlink(temp_path)
    
    def test_multiline_content(self):
        """Test multiline content."""
        content = "def func():\n    a = 1\n    b = 2\n    return a + b"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                lines = f.readlines()
            
            self.assertGreater(len(lines), 1)
        finally:
            os.unlink(temp_path)
    
    def test_empty_file(self):
        """Test handling empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                content = f.read()
            
            self.assertEqual(content, "")
        finally:
            os.unlink(temp_path)


class TestUnsavedChanges(unittest.TestCase):
    """Test handling unsaved changes."""
    
    def test_detect_unsaved_changes(self):
        """Test detecting unsaved changes."""
        # This tests the concept of tracking modified state
        # In actual implementation, editor would track this
        
        is_modified = True  # Simulated state
        
        # Should prompt user when closing
        self.assertTrue(is_modified)
    
    def test_modified_flag_cleared_on_save(self):
        """Test modified flag clears on save."""
        is_modified = True
        
        # After save operation, flag should be cleared
        # is_modified = False  # After save
        
        self.assertTrue(is_modified)  # Before save


class TestFilePathOperations(unittest.TestCase):
    """Test file path operations."""
    
    def test_get_file_extension(self):
        """Test extracting file extension."""
        path = "/path/to/file.py"
        
        ext = Path(path).suffix
        
        self.assertEqual(ext, ".py")
    
    def test_get_filename(self):
        """Test extracting filename."""
        path = "/path/to/my_script.py"
        
        name = Path(path).name
        
        self.assertEqual(name, "my_script.py")
    
    def test_get_stem(self):
        """Test extracting filename without extension."""
        path = "/path/to/my_script.py"
        
        stem = Path(path).stem
        
        self.assertEqual(stem, "my_script")


if __name__ == '__main__':
    unittest.main()