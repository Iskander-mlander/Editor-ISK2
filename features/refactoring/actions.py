"""
Code Actions Module
===================
Provides quick fixes and refactoring suggestions.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal


class ActionKind(Enum):
    """Kinds of code actions."""
    QUICK_FIX = auto()
    REFACTOR = auto()
    SOURCE_ACTION = auto()
    REFACTORING = auto()
    COMPILE = auto()
    LINE_ACTION = auto()


@dataclass
class CodeAction:
    """Represents a code action/quick fix."""
    title: str
    kind: ActionKind
    description: str
    edit: Optional['DocumentEdit'] = None
    command: Optional[str] = None
    is_preferred: bool = False
    

@dataclass
class DocumentEdit:
    """Represents a document edit."""
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    new_text: str


@dataclass
class Diagnostic:
    """Represents a diagnostic issue."""
    message: str
    severity: int  # 1=error, 2=warning, 3=info
    source: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    code: Optional[str] = None


class CodeActionsProvider(QObject):
    """
    Provides code actions and quick fixes based on diagnostics.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._diagnostics: List[Diagnostic] = []
        self._action_handlers: Dict[str, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default action handlers."""
        # Python-specific handlers
        self._action_handlers['unused-import'] = self._fix_unused_import
        self._action_handlers['undefined-variable'] = self._fix_undefined_variable
        self._action_handlers['unused-variable'] = self._fix_unused_variable
        self._action_handlers['redefining-function'] = self._fix_redefining_function
        self._action_handlers['missing-function-docstring'] = self._add_docstring
        self._action_handlers['simplify-comparison'] = self._simplify_comparison
        self._action_handlers['fix-indent'] = self._fix_indentation
    
    def set_diagnostics(self, diagnostics: List[Diagnostic]) -> None:
        """Set current diagnostics."""
        self._diagnostics = diagnostics
    
    def get_code_actions(self, context: Dict[str, Any]) -> List[CodeAction]:
        """Get available code actions for the context."""
        actions = []
        
        cursor_line = context.get('cursor_line', 0)
        cursor_column = context.get('cursor_column', 0)
        document = context.get('document', '')
        
        for diag in self._diagnostics:
            # Check if diagnostic is near cursor
            if abs(diag.line - cursor_line) <= 2:
                # Generate actions based on diagnostic code/message
                action = self._generate_action(diag, document)
                if action:
                    actions.append(action)
        
        # Add general refactoring actions
        actions.extend(self._get_general_actions(document, cursor_line))
        
        return actions
    
    def _generate_action(self, diag: Diagnostic, document: str) -> Optional[CodeAction]:
        """Generate an action for a diagnostic."""
        message = diag.message.lower()
        code = (diag.code or '').lower()
        
        # Match patterns to actions
        if 'unused' in message and 'import' in message:
            return self._action_handlers.get('unused-import', lambda d, doc: None)(diag, document)
        
        if 'undefined' in message or 'name' in message and "'" in message:
            return self._action_handlers.get('undefined-variable', lambda d, doc: None)(diag, document)
        
        if 'unused' in message and 'variable' in message:
            return self._action_handlers.get('unused-variable', lambda d, doc: None)(diag, document)
        
        if 'redefining' in message or 'redefinition' in message:
            return self._action_handlers.get('redefining-function', lambda d, doc: None)(diag, document)
        
        if 'docstring' in message or 'missing' in message and 'document' in message:
            return self._action_handlers.get('missing-function-docstring', lambda d, doc: None)(diag, document)
        
        if 'indent' in message or 'indentation' in message:
            return self._action_handlers.get('fix-indent', lambda d, doc: None)(diag, document)
        
        return None
    
    def _fix_unused_import(self, diag: Diagnostic, document: str) -> Optional[CodeAction]:
        """Fix unused import."""
        line_num = diag.line - 1
        lines = document.split('\n')
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            
            # Check if it's an import line
            if 'import' in line:
                return CodeAction(
                    title="Remove unused import",
                    kind=ActionKind.QUICK_FIX,
                    description="Remove the unused import statement",
                    edit=DocumentEdit(
                        start_line=line_num,
                        start_column=0,
                        end_line=line_num,
                        end_column=len(line),
                        new_text=""
                    ),
                    is_preferred=True
                )
        
        return None
    
    def _fix_undefined_variable(self, diag: Diagnostic, document: str) -> Optional[CodeAction]:
        """Fix undefined variable."""
        # Extract variable name from diagnostic
        match = re.search(r"'(\w+)'", diag.message)
        if not match:
            return None
        
        var_name = match.group(1)
        
        # Check if it might need to be imported
        return CodeAction(
            title=f"Import '{var_name}' from its module",
            kind=ActionKind.QUICK_FIX,
            description=f"Add import statement for '{var_name}'",
            command=f"import {var_name}"
        )
    
    def _fix_unused_variable(self, diag: Diagnostic, document: str) -> Optional[CodeAction]:
        """Fix unused variable."""
        line_num = diag.line - 1
        lines = document.split('\n')
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            
            # Check for assignment
            if '=' in line and '==' not in line:
                return CodeAction(
                    title="Remove unused variable assignment",
                    kind=ActionKind.QUICK_FIX,
                    description="Remove the assignment to the unused variable",
                    edit=DocumentEdit(
                        start_line=line_num,
                        start_column=0,
                        end_line=line_num,
                        end_column=len(line),
                        new_text=""
                    )
                )
        
        return None
    
    def _fix_redefining_function(self, diag: Diagnostic, document: str) -> Optional[CodeAction]:
        """Fix function redefinition."""
        return CodeAction(
            title="Rename function to avoid shadowing",
            kind=ActionKind.REFACTOR,
            description="Rename the function to avoid redefining an existing one"
        )
    
    def _add_docstring(self, diag: Diagnostic, document: str) -> Optional[CodeAction]:
        """Add missing docstring."""
        line_num = diag.line - 1
        lines = document.split('\n')
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            
            # Check for function definition
            if 'def ' in line:
                # Extract function name
                match = re.search(r'def (\w+)', line)
                func_name = match.group(1) if match else "function"
                
                # Add docstring after the definition
                if ':' in line:
                    colon_pos = line.index(':') + 1
                    docstring = f'\n    """Brief description of {func_name}.\n\n    Args:\n        param1: Description\n\n    Returns:\n        Description\n    """'
                    
                    return CodeAction(
                        title="Add docstring",
                        kind=ActionKind.SOURCE_ACTION,
                        description=f"Add docstring to function '{func_name}'",
                        edit=DocumentEdit(
                            start_line=line_num,
                            start_column=colon_pos,
                            end_line=line_num,
                            end_column=colon_pos,
                            new_text=docstring
                        )
                    )
        
        return None
    
    def _simplify_comparison(self, diag: Diagnostic, document: str) -> Optional[CodeAction]:
        """Simplify comparison."""
        return CodeAction(
            title="Simplify comparison",
            kind=ActionKind.REFACTOR,
            description="Use a more concise comparison"
        )
    
    def _fix_indentation(self, diag: Diagnostic, document: str) -> Optional[CodeAction]:
        """Fix indentation."""
        return CodeAction(
            title="Fix indentation",
            kind=ActionKind.QUICK_FIX,
            description="Correct the indentation of this line"
        )
    
    def _get_general_actions(self, document: str, cursor_line: int) -> List[CodeAction]:
        """Get general refactoring actions."""
        actions = []
        
        # Add common actions based on context
        actions.append(CodeAction(
            title="Organize imports",
            kind=ActionKind.SOURCE_ACTION,
            description="Sort and remove unused imports",
            command="organizeImports"
        ))
        
        actions.append(CodeAction(
            title="Format document",
            kind=ActionKind.SOURCE_ACTION,
            description="Format the entire document",
            command="formatDocument"
        ))
        
        actions.append(CodeAction(
            title="Extract to function",
            kind=ActionKind.REFACTORING,
            description="Extract selection to a new function"
        ))
        
        return actions
    
    def apply_action(self, action: CodeAction, document: str) -> str:
        """Apply a code action to the document."""
        if not action.edit:
            return document
        
        lines = document.split('\n')
        edit = action.edit
        
        if edit.new_text == "":
            # Remove line
            if 0 <= edit.start_line < len(lines):
                lines.pop(edit.start_line)
        else:
            # Replace content
            if 0 <= edit.start_line < len(lines):
                if edit.start_line == edit.end_line:
                    # Single line edit
                    line = lines[edit.start_line]
                    before = line[:edit.start_column]
                    after = line[edit.end_column:]
                    lines[edit.start_line] = before + edit.new_text + after
                else:
                    # Multi-line edit
                    lines[edit.start_line:edit.end_line + 1] = [action.edit.new_text]
        
        return '\n'.join(lines)


class RefactoringProvider(QObject):
    """
    Provides refactoring operations.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
    
    def extract_function(self, document: str, selection: tuple, name: str) -> str:
        """Extract code to a new function."""
        start, end = selection
        lines = document.split('\n')
        selected = '\n'.join(lines[start:end])
        
        # Find common indentation
        indent = 0
        for line in lines[start:end]:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                break
        
        # Build new function
        func = f"\n\ndef {name}():\n"
        for line in selected.split('\n'):
            if line.strip():
                func += ' ' * (indent + 4) + line + '\n'
        
        # Replace selection with function call
        func_call = ' ' * indent + f"{name}()\n"
        
        result = lines[:start] + [func_call] + lines[end:]
        result.append(func)
        
        return '\n'.join(result)
    
    def rename_symbol(self, document: str, old_name: str, new_name: str) -> str:
        """Rename all occurrences of a symbol."""
        # Use word boundary to avoid partial matches
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, document)
    
    def extract_variable(self, document: str, selection: tuple, var_name: str) -> str:
        """Extract expression to a variable."""
        start, end = selection
        lines = document.split('\n')
        
        # Get selected text
        selected = '\n'.join(lines[start:end])
        
        # Find indentation
        indent = 0
        if start < len(lines):
            line = lines[start]
            indent = len(line) - len(line.lstrip())
        
        # Create variable assignment
        var_assign = ' ' * indent + f"{var_name} = {selected.strip()}\n"
        
        # Replace with variable
        result = lines[:start] + [var_assign + ' ' * indent + var_name] + lines[end:]
        
        return '\n'.join(result)
    
    def inline_variable(self, document: str, var_name: str) -> str:
        """Inline a variable definition."""
        # Find variable assignment
        pattern = rf'^(\s*){re.escape(var_name)}\s*=\s*(.+)$'
        
        lines = document.split('\n')
        var_line = None
        var_value = None
        
        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                var_line = i
                var_value = match.group(2).rstrip()
                break
        
        if var_line is None:
            return document
        
        # Replace all occurrences of the variable with its value
        for i, line in enumerate(lines):
            if i != var_line and var_name in line:
                lines[i] = line.replace(var_name, f"({var_value})")
        
        # Remove the assignment
        lines.pop(var_line)
        
        return '\n'.join(lines)


class QuickFixPanel(QObject):
    """
    UI component for displaying and applying quick fixes.
    """
    
    action_selected = pyqtSignal(object)  # CodeAction
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._provider = CodeActionsProvider()
        self._current_actions: List[CodeAction] = []
    
    @property
    def provider(self) -> CodeActionsProvider:
        """Get the code actions provider."""
        return self._provider
    
    def show_actions(self, context: Dict[str, Any]) -> List[CodeAction]:
        """Show available actions for context."""
        self._current_actions = self._provider.get_code_actions(context)
        return self._current_actions
    
    def apply_selected(self, action: CodeAction, document: str) -> str:
        """Apply the selected action."""
        return self._provider.apply_action(action, document)