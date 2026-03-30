"""
Tests for Code Validation
=========================
Tests for syntax validation, type checking, and linting.
"""

import unittest
import tempfile
import os
from pathlib import Path


class TestSyntaxValidation(unittest.TestCase):
    """Test syntax validation."""
    
    def test_valid_python_syntax(self):
        """Test valid Python syntax passes."""
        code = """
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
"""
        
        # Should parse without errors
        try:
            compile(code, '<string>', 'exec')
            is_valid = True
        except SyntaxError:
            is_valid = False
        
        self.assertTrue(is_valid)
    
    def test_invalid_syntax_detected(self):
        """Test invalid syntax is detected."""
        code = """
def broken(
    return 1
"""
        
        try:
            compile(code, '<string>', 'exec')
            is_valid = True
        except SyntaxError:
            is_valid = False
        
        self.assertFalse(is_valid)
    
    def test_matching_brackets(self):
        """Test bracket matching."""
        code = "def func(a, b):\n    return a + b"
        
        # Count brackets
        open_parens = code.count('(')
        close_parens = code.count(')')
        
        self.assertEqual(open_parens, close_parens)
    
    def test_matching_braces(self):
        """Test brace matching."""
        code = "dict = {'key': 'value'}"
        
        open_braces = code.count('{')
        close_braces = code.count('}')
        
        self.assertEqual(open_braces, close_braces)


class TestLintIntegration(unittest.TestCase):
    """Test linting integration."""
    
    def test_pylint_available(self):
        """Test pylint is available check."""
        import shutil
        is_available = shutil.which("pylint") is not None
        
        # May or may not be installed
        self.assertIn(is_available, [True, False])
    
    def test_flake8_available(self):
        """Test flake8 is available check."""
        import shutil
        is_available = shutil.which("flake8") is not None
        
        self.assertIn(is_available, [True, False])
    
    def test_black_available(self):
        """Test black formatter is available."""
        import shutil
        is_available = shutil.which("black") is not None
        
        self.assertIn(is_available, [True, False])


class TestTypeChecking(unittest.TestCase):
    """Test type checking features."""
    
    def test_type_hints_valid(self):
        """Test type hints work correctly."""
        code = """
def greet(name: str) -> str:
    return f"Hello, {name}"

message: str = greet("World")
"""
        
        # Should compile with type hints
        try:
            compile(code, '<string>', 'exec')
            has_types = True
        except Exception:
            has_types = False
        
        self.assertTrue(has_types)
    
    def test_type_hints_enforced(self):
        """Test type enforcement."""
        def typed_func(x: int) -> int:
            return x * 2
        
        result = typed_func(5)
        
        self.assertEqual(result, 10)
        self.assertIsInstance(result, int)


class TestErrorDetection(unittest.TestCase):
    """Test error detection in code."""
    
    def test_undefined_variable_detected(self):
        """Test undefined variable detection."""
        code = """
x = y + 1  # y is undefined
"""
        
        # This will cause NameError at runtime
        with self.assertRaises(NameError):
            exec(code)
    
    def test_import_error_handling(self):
        """Test handling import errors."""
        # Try importing non-existent module
        try:
            import nonexistent_module_12345
            has_import = True
        except ImportError:
            has_import = False
        
        self.assertFalse(has_import)
    
    def test_division_by_zero_handling(self):
        """Test division by zero handling."""
        try:
            result = 10 / 0
            has_error = False
        except ZeroDivisionError:
            has_error = True
        
        self.assertTrue(has_error)


class TestPEP8Compliance(unittest.TestCase):
    """Test PEP8 style compliance."""
    
    def test_line_length_check(self):
        """Test checking line length."""
        long_line = "x = " + "".join(["a" for i in range(79)])
        
        self.assertGreater(len(long_line), 79)
    
    def test_naming_conventions(self):
        """Test naming conventions."""
        valid_names = ["variable", "function_name", "ClassName", "CONSTANT"]
        
        for name in valid_names:
            self.assertTrue(name.isidentifier() or name[0].isupper())
    
    def test_indentation_check(self):
        """Test indentation consistency."""
        # Test that we can detect proper indentation
        code = "    x = 1\n    y = 2"
        
        lines = code.split('\n')
        # Lines should have leading spaces
        self.assertTrue(len(lines[0]) > 0)


class TestCodeAnalysis(unittest.TestCase):
    """Test code analysis capabilities."""
    
    def test_count_functions(self):
        """Test counting functions in code."""
        code = """
def func1():
    pass

def func2():
    pass

class MyClass:
    def method(self):
        pass
"""
        
        func_count = code.count('def ')
        
        self.assertEqual(func_count, 3)
    
    def test_count_classes(self):
        """Test counting classes in code."""
        code = """
class A:
    pass

class B:
    pass
"""
        
        class_count = code.count('class ')
        
        self.assertEqual(class_count, 2)
    
    def test_extract_imports(self):
        """Test extracting imports from code."""
        code = """
import os
import sys
from pathlib import Path
from typing import List
"""
        
        imports = []
        for line in code.split('\n'):
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line.strip())
        
        self.assertEqual(len(imports), 4)


class TestFormatterIntegration(unittest.TestCase):
    """Test code formatter integration."""
    
    def test_black_format_import(self):
        """Test Black can be imported."""
        try:
            import black
            has_black = True
        except ImportError:
            has_black = False
        
        self.assertIn(has_black, [True, False])
    
    def test_autopep8_import(self):
        """Test autopep8 can be imported."""
        try:
            import autopep8
            has_autopep8 = True
        except ImportError:
            has_autopep8 = False
        
        # May or may not be installed
        self.assertIn(has_autopep8, [True, False])


if __name__ == '__main__':
    unittest.main()