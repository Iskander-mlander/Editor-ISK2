"""
Unit Tests for File Type Detector
==================================
Tests for the file type detection module.
"""

import unittest
import tempfile
import os

from core.utils.file_type_detector import FileTypeDetector, get_detector


class TestFileType(unittest.TestCase):
    """Test FileType dataclass."""
    
    def test_creation(self):
        """Test creating a file type."""
        from core.utils.file_type_detector import FileType
        
        ft = FileType("Python", "python", [".py", ".pyw"], r"^#!/.*python")
        
        self.assertEqual(ft.name, "Python")
        self.assertEqual(ft.language, "python")
        self.assertEqual(ft.extensions, [".py", ".pyw"])


class TestFileTypeDetector(unittest.TestCase):
    """Test FileTypeDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = get_detector()
    
    def test_initialization(self):
        """Test initialization."""
        self.assertIsNotNone(self.detector._extension_map)
    
    def test_detect_python_file(self):
        """Test detecting Python file."""
        lang = self.detector.detect_from_extension("test.py")
        self.assertEqual(lang, "python")
    
    def test_detect_js_file(self):
        """Test detecting JavaScript file."""
        lang = self.detector.detect_from_extension("test.js")
        self.assertEqual(lang, "javascript")
    
    def test_detect_html_file(self):
        """Test detecting HTML file."""
        lang = self.detector.detect_from_extension("test.html")
        self.assertEqual(lang, "html")
    
    def test_detect_json_file(self):
        """Test detecting JSON file."""
        lang = self.detector.detect_from_extension("test.json")
        self.assertEqual(lang, "json")
    
    def test_detect_unknown_extension(self):
        """Test detecting unknown extension."""
        lang = self.detector.detect_from_extension("test.xyz")
        self.assertEqual(lang, "text")
    
    def test_detect_from_shebang_python(self):
        """Test detecting Python from shebang."""
        content = "#!/usr/bin/python\nprint('hello')"
        lang = self.detector.detect_from_content(content)
        self.assertEqual(lang, "python")
    
    def test_detect_from_shebang_bash(self):
        """Test detecting Bash from shebang."""
        content = "#!/bin/bash\necho hello"
        lang = self.detector.detect_from_content(content)
        self.assertEqual(lang, "shell")
    
    def test_detect_from_shebang_node(self):
        """Test detecting Node.js from shebang."""
        content = "#!/usr/bin/node\nconsole.log('hello')"
        lang = self.detector.detect_from_content(content)
        self.assertEqual(lang, "javascript")
    
    def test_detect_no_content(self):
        """Test detecting with no content."""
        lang = self.detector.detect_from_content("")
        self.assertIsNone(lang)
    
    def test_detect_full(self):
        """Test full detection with extension."""
        lang = self.detector.detect("test.py", "#!/usr/bin/python\ncode")
        self.assertEqual(lang, "python")
    
    def test_detect_fallback_to_content(self):
        """Test fallback to content detection."""
        lang = self.detector.detect("test.xyz", "#!/bin/bash\ncode")
        self.assertEqual(lang, "shell")
    
    def test_get_language_name(self):
        """Test getting language display name."""
        name = self.detector.get_language_name("python")
        self.assertEqual(name, "Python")
        
        name = self.detector.get_language_name("javascript")
        self.assertEqual(name, "JavaScript")
    
    def test_case_insensitive_extension(self):
        """Test case insensitive extension detection."""
        lang = self.detector.detect_from_extension("test.PY")
        self.assertEqual(lang, "python")


class TestFileTypeDetectorMultipleExtensions(unittest.TestCase):
    """Test file types with multiple extensions."""
    
    def test_shell_extensions(self):
        """Test shell file extensions."""
        detector = get_detector()
        
        for ext in ['.sh', '.bash', '.zsh']:
            lang = detector.detect_from_extension(f"script{ext}")
            self.assertEqual(lang, "shell")


if __name__ == '__main__':
    unittest.main()