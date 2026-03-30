"""
Test: Language Definitions
=========================
Tests for core/editor/languages.py
"""

import unittest
from core.editor.languages import (
    LANGUAGES, get_language_by_extension, get_language_by_name,
    get_supported_languages, LanguageDefinition
)


class TestLanguageDefinitions(unittest.TestCase):
    """Test language definition module."""
    
    def test_languages_registered(self):
        """Test that all languages are registered."""
        self.assertGreater(len(LANGUAGES), 0)
        self.assertIn('python', LANGUAGES)
        self.assertIn('javascript', LANGUAGES)
        self.assertIn('typescript', LANGUAGES)
    
    def test_get_language_by_name(self):
        """Test getting language by name."""
        lang = get_language_by_name('python')
        self.assertIsNotNone(lang)
        self.assertIsInstance(lang, LanguageDefinition)
        self.assertEqual(lang.name, 'Python')
    
    def test_get_language_by_name_case_insensitive(self):
        """Test case insensitive language lookup."""
        lang = get_language_by_name('PYTHON')
        self.assertIsNotNone(lang)
        
        lang = get_language_by_name('JavaScript')
        self.assertIsNotNone(lang)
    
    def test_get_language_by_extension(self):
        """Test getting language by file extension."""
        lang = get_language_by_extension('.py')
        self.assertIsNotNone(lang)
        self.assertEqual(lang.name, 'Python')
    
    def test_get_language_by_extension_none(self):
        """Test unknown extension returns None."""
        lang = get_language_by_extension('.unknown')
        self.assertIsNone(lang)
    
    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        langs = get_supported_languages()
        self.assertIsInstance(langs, list)
        self.assertIn('python', langs)
        self.assertIn('javascript', langs)
    
    def test_python_language_definition(self):
        """Test Python language has required attributes."""
        py = LANGUAGES['python']
        
        self.assertEqual(py.name, 'Python')
        self.assertIn('.py', py.extensions)
        self.assertIn('def', py.keywords)
        self.assertIn('import', py.keywords)
        self.assertIn('class', py.keywords)
        self.assertIn('print', py.builtins)
        self.assertEqual(py.comment_single, '#')
        self.assertEqual(py.comment_multi_start, '"""')
    
    def test_javascript_language_definition(self):
        """Test JavaScript language has required attributes."""
        js = LANGUAGES['javascript']
        
        self.assertEqual(js.name, 'JavaScript')
        self.assertIn('.js', js.extensions)
        self.assertIn('function', js.keywords)
        self.assertIn('const', js.keywords)
        self.assertIn('let', js.keywords)
        self.assertEqual(js.comment_single, '//')
    
    def test_language_has_all_attributes(self):
        """Test that all languages have required attributes."""
        for lang_id, lang in LANGUAGES.items():
            with self.subTest(lang_id=lang_id):
                self.assertIsNotNone(lang.name)
                self.assertIsNotNone(lang.extensions)
                self.assertIsNotNone(lang.keywords)
                self.assertIsNotNone(lang.builtins)
                self.assertIsNotNone(lang.string_patterns)
                self.assertGreater(len(lang.extensions), 0)
                self.assertGreater(len(lang.keywords), 0)


class TestLanguageRegistry(unittest.TestCase):
    """Test the language registry functionality."""
    
    def test_all_languages_have_keyword_patterns(self):
        """All languages should have keyword patterns."""
        for lang_id, lang in LANGUAGES.items():
            with self.subTest(lang_id=lang_id):
                # Should have keywords
                self.assertIsInstance(lang.keywords, list)
                self.assertGreater(len(lang.keywords), 0,
                    f"{lang_id} should have keywords")
    
    def test_multiple_extensions(self):
        """Some languages should have multiple extensions."""
        # C++ should have multiple extensions
        cpp = LANGUAGES.get('cpp')
        if cpp:
            self.assertGreater(len(cpp.extensions), 1)


if __name__ == '__main__':
    unittest.main()