"""
Unit Tests for Emmet Module
============================
Tests for the Emmet abbreviation expansion.
"""

import unittest

from core.utils.emmet import EmmetEngine, get_engine


class TestEmmetEngine(unittest.TestCase):
    """Test EmmetEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EmmetEngine()
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertIsNotNone(self.engine._abbreviations)
    
    def test_expand_basic_tag(self):
        """Test expanding basic HTML tag."""
        result = self.engine.expand("div")
        
        self.assertEqual(result, "<div></div>")
    
    def test_expand_self_closing_tag(self):
        """Test expanding self-closing tag."""
        result = self.engine.expand("img")
        
        self.assertEqual(result, '<img src="" alt="">')
    
    def test_expand_with_id(self):
        """Test expanding tag with ID."""
        result = self.engine.expand("div#container")
        
        self.assertIn('id="container"', result)
    
    def test_expand_with_class(self):
        """Test expanding tag with class."""
        result = self.engine.expand("div.header")
        
        self.assertIn('class="header"', result)
    
    def test_expand_multiple_classes(self):
        """Test expanding tag with multiple classes."""
        result = self.engine.expand("div.active.bold")
        
        self.assertIn('class="active bold"', result)
    
    def test_expand_child(self):
        """Test expanding child relationship."""
        result = self.engine.expand("ul>li")
        
        self.assertIn("<ul>", result)
        self.assertIn("<li></li>", result)
    
    def test_expand_sibling(self):
        """Test expanding sibling relationship."""
        result = self.engine.expand("div+p")
        
        self.assertIn("<div>", result)
        self.assertIn("<p>", result)
    
    def test_expand_table(self):
        """Test expanding table tag."""
        result = self.engine.expand("table>tr>td")
        
        self.assertIn("<table>", result)
        self.assertIn("<tr>", result)
        self.assertIn("<td>", result)
    
    def test_expand_abbr(self):
        """Test expanding abbreviation alias."""
        result = self.engine.expand("!")
        
        self.assertIn("<div>", result)
    
    def test_expand_input_type(self):
        """Test expanding input with type."""
        result = self.engine.expand("input:email")
        
        self.assertIn('type="email"', result)
    
    def test_expand_link(self):
        """Test expanding link tag."""
        result = self.engine.expand("link:css")
        
        self.assertIn('rel="stylesheet"', result)
    
    def test_expand_form(self):
        """Test expanding form tag."""
        result = self.engine.expand("form")
        
        self.assertIn("<form", result)
    
    def test_expand_unknown_tag(self):
        """Test expanding unknown tag."""
        result = self.engine.expand("unknown")
        
        self.assertIn("<unknown>", result)
    
    def test_has_expansion(self):
        """Test has_expansion method."""
        self.assertTrue(self.engine.has_expansion("div"))
        self.assertTrue(self.engine.has_expansion("!"))
        self.assertTrue(self.engine.has_expansion("input:email"))
    
    def test_expand_html(self):
        """Test expanding html tag."""
        result = self.engine.expand("html")
        
        self.assertEqual(result, "<html></html>")


class TestGetEngine(unittest.TestCase):
    """Test get_engine function."""
    
    def test_returns_engine_instance(self):
        """Test function returns EmmetEngine."""
        engine = get_engine()
        
        self.assertIsInstance(engine, EmmetEngine)


if __name__ == '__main__':
    unittest.main()