"""
Debug Manager Module
====================
Enhanced debugging with breakpoints and interactive control.
"""

import os
import subprocess
import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum, auto
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QProcess, QTimer
from PyQt6.QtWidgets import QPlainTextEdit


class DebugState(Enum):
    """Debug session states."""
    IDLE = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    TERMINATED = auto()


@dataclass
class Breakpoint:
    """Represents a breakpoint."""
    id: str
    file_path: str
    line: int
    enabled: bool = True
    condition: str = ""
    hit_count: int = 0
    
    def __hash__(self) -> int:
        return hash((self.file_path, self.line))


@dataclass
class StackFrame:
    """Represents a stack frame."""
    level: int
    file_path: str
    line: int
    function: str
    source_line: str = ""


@dataclass
class Variable:
    """Represents a variable in the debug context."""
    name: str
    value: str
    type_name: str = ""
    scope: str = "local"
    

class DebugSignals(QObject):
    """Signals for debug events."""
    state_changed = pyqtSignal(DebugState)
    breakpoint_hit = pyqtSignal(str, int)  # file, line
    stopped = pyqtSignal(str, int)  # reason, line
    continued = pyqtSignal()
    terminated = pyqtSignal()
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    variables_changed = pyqtSignal(list)  # List[Variable]
    stack_changed = pyqtSignal(list)  # List[StackFrame]


class DebugManager(QObject):
    """
    Manages debugging sessions with breakpoint support.
    Uses subprocess-based debugging with custom protocol.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = DebugSignals()
        self._state = DebugState.IDLE
        
        self._process: Optional[QProcess] = None
        self._file_path: Optional[str] = None
        self._breakpoints: Dict[str, Set[Breakpoint]] = {}  # file_path -> set of breakpoints
        self._enabled_breakpoints: Set[Tuple[str, int]] = set()
        
        self._stack: List[StackFrame] = []
        self._variables: List[Variable] = []
        
        self._output_buffer: str = ""
        self._command_queue: List[str] = []
        
        # Settings
        self._python_path: str = "python3"
        self._sublime_debug_port: int = 2112
    
    @property
    def signals(self) -> DebugSignals:
        """Get debug signals."""
        return self._signals
    
    @property
    def state(self) -> DebugState:
        """Get current debug state."""
        return self._state
    
    @property
    def is_debugging(self) -> bool:
        """Check if currently debugging."""
        return self._state in (DebugState.STARTING, DebugState.RUNNING, DebugState.PAUSED)
    
    def _set_state(self, state: DebugState) -> None:
        """Set debug state."""
        self._state = state
        self._signals.state_changed.emit(state)
    
    def set_python_path(self, path: str) -> None:
        """Set Python interpreter path."""
        self._python_path = path
    
    def add_breakpoint(self, file_path: str, line: int, condition: str = "", enabled: bool = True) -> Breakpoint:
        """Add a breakpoint."""
        import uuid
        
        # Normalize path
        file_path = os.path.abspath(file_path)
        
        # Create breakpoint
        bp = Breakpoint(
            id=str(uuid.uuid4()),
            file_path=file_path,
            line=line,
            condition=condition,
            enabled=enabled
        )
        
        # Add to collection
        if file_path not in self._breakpoints:
            self._breakpoints[file_path] = set()
        
        self._breakpoints[file_path].add(bp)
        
        if enabled:
            self._enabled_breakpoints.add((file_path, line))
        
        return bp
    
    def remove_breakpoint(self, file_path: str, line: int) -> bool:
        """Remove a breakpoint."""
        file_path = os.path.abspath(file_path)
        
        if file_path in self._breakpoints:
            for bp in self._breakpoints[file_path]:
                if bp.line == line:
                    self._breakpoints[file_path].discard(bp)
                    self._enabled_breakpoints.discard((file_path, line))
                    return True
        
        return False
    
    def toggle_breakpoint(self, file_path: str, line: int, condition: str = "") -> Optional[Breakpoint]:
        """Toggle a breakpoint at line."""
        file_path = os.path.abspath(file_path)
        
        # Check if exists
        if file_path in self._breakpoints:
            for bp in self._breakpoints[file_path]:
                if bp.line == line:
                    self.remove_breakpoint(file_path, line)
                    return None
        
        return self.add_breakpoint(file_path, line, condition)
    
    def get_breakpoints(self, file_path: Optional[str] = None) -> List[Breakpoint]:
        """Get breakpoints for a file or all."""
        if file_path:
            file_path = os.path.abspath(file_path)
            return list(self._breakpoints.get(file_path, set()))
        
        all_bp = []
        for bps in self._breakpoints.values():
            all_bp.extend(bps)
        return all_bp
    
    def clear_breakpoints(self) -> None:
        """Clear all breakpoints."""
        self._breakpoints.clear()
        self._enabled_breakpoints.clear()
    
    def start_debugging(self, file_path: str, python_args: List[str] = None) -> bool:
        """Start debugging a file."""
        if self.is_debugging:
            return False
        
        file_path = os.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            self._signals.error_received.emit(f"File not found: {file_path}")
            return False
        
        self._file_path = file_path
        self._set_state(DebugState.STARTING)
        
        # Create debugger process
        # Using a custom debug script approach
        debug_script = self._create_debug_script()
        
        # Build command
        cmd = [self._python_path, debug_script, file_path]
        
        if python_args:
            cmd.extend(python_args)
        
        # Start process
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        self._process.readyReadStandardOutput.connect(self._on_output)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)
        
        self._process.start(cmd[0], cmd[1:])
        
        return True
    
    def _create_debug_script(self) -> str:
        """Create a debug wrapper script."""
        # Simple debug wrapper that supports breakpoints
        debug_code = '''
import sys
import traceback
import json

class SimpleDebugger:
    def __init__(self):
        self.breakpoints = {}
        self.running = True
        self.step_mode = False
        
    def set_breakpoints(self, bps):
        for file_path, lines in bps.items():
            self.breakpoints[file_path] = set(lines)
    
    def should_break(self, file_path, line):
        return file_path in self.breakpoints and line in self.breakpoints[file_path]
    
    def run(self, code, globals_dict, locals_dict):
        try:
            exec(code, globals_dict, locals_dict)
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()
    
    def trace_calls(self, frame, event, arg):
        if not self.running:
            return self.trace_calls
        
        file_path = frame.f_code.co_filename
        line_no = frame.f_lineno
        
        if event == 'line':
            if self.should_break(file_path, line_no):
                print(f"BREAK: {file_path}:{line_no}")
                # Read source
                try:
                    with open(file_path) as f:
                        lines = f.readlines()
                        if line_no <= len(lines):
                            print(f"SOURCE: {line_no}: {lines[line_no-1].rstrip()}")
                except:
                    pass
                
                self.step_mode = True
            
            if self.step_mode:
                print(f"LINE: {file_path}:{line_no}")
        
        return self.trace_calls

if __name__ == "__main__":
    dbg = SimpleDebugger()
    dbg.running = True
    
    file_to_run = sys.argv[1] if len(sys.argv) > 1 else None
    
    if file_to_run:
        with open(file_to_run) as f:
            code = f.read()
        
        sys.settrace(dbg.trace_calls)
        try:
            exec(code, {}, {})
        except SystemExit:
            pass
        except Exception as e:
            print(f"Error: {e}")
        finally:
            sys.settrace(None)
'''
        
        # Write to temp file
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.py')
        os.write(fd, debug_code.encode())
        os.close(fd)
        
        return path
    
    def _on_output(self) -> None:
        """Handle process output."""
        if not self._process:
            return
        
        output = self._process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self._output_buffer += output
        
        self._signals.output_received.emit(output)
        
        # Parse debug output
        self._parse_debug_output(output)
    
    def _parse_debug_output(self, output: str) -> None:
        """Parse debug protocol output."""
        # Look for BREAK markers
        for line in output.split('\n'):
            if line.startswith('BREAK:'):
                parts = line[6:].split(':')
                if len(parts) >= 2:
                    file_path = ':'.join(parts[:-1])
                    try:
                        line_num = int(parts[-1])
                        self._set_state(DebugState.PAUSED)
                        self._signals.breakpoint_hit.emit(file_path, line_num)
                    except ValueError:
                        pass
            
            elif line.startswith('LINE:'):
                parts = line[5:].split(':')
                if len(parts) >= 2:
                    file_path = ':'.join(parts[:-1])
                    try:
                        line_num = int(parts[-1])
                        self._signals.stopped.emit("step", line_num)
                    except ValueError:
                        pass
    
    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """Handle process finished."""
        self._set_state(DebugState.TERMINATED)
        self._signals.terminated.emit()
    
    def _on_error(self, error: QProcess.ProcessError) -> None:
        """Handle process error."""
        if self._process:
            self._signals.error_received.emit(self._process.errorString())
        self._set_state(DebugState.IDLE)
    
    def continue_debug(self) -> None:
        """Continue execution."""
        if self._state == DebugState.PAUSED:
            self._set_state(DebugState.RUNNING)
            self._signals.continued.emit()
    
    def step_over(self) -> None:
        """Step over current line."""
        if self._state == DebugState.PAUSED:
            # In our simple implementation, just continue
            self._set_state(DebugState.RUNNING)
            self._signals.continued.emit()
    
    def step_into(self) -> None:
        """Step into function."""
        self.step_over()  # Simplified
    
    def step_out(self) -> None:
        """Step out of function."""
        self.step_over()  # Simplified
    
    def stop_debug(self) -> None:
        """Stop debugging."""
        if self._process and self._state != DebugState.IDLE:
            self._process.kill()
            self._process.waitForFinished(1000)
        
        self._set_state(DebugState.IDLE)
        self._signals.terminated.emit()
    
    def evaluate_expression(self, expression: str) -> Optional[str]:
        """Evaluate an expression in the current context."""
        # This would require more sophisticated debugging
        # For now, return None
        return None


class DebugPanel(QObject):
    """
    UI panel for debugging with breakpoint management.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._debug_manager = DebugManager()
        self._debug_manager.signals.state_changed.connect(self._on_state_changed)
        self._debug_manager.signals.breakpoint_hit.connect(self._on_breakpoint_hit)
        self._debug_manager.signals.output_received.connect(self._on_output)
    
    @property
    def debug_manager(self) -> DebugManager:
        """Get the debug manager."""
        return self._debug_manager
    
    def _on_state_changed(self, state: DebugState) -> None:
        """Handle state changes."""
        pass
    
    def _on_breakpoint_hit(self, file_path: str, line: int) -> None:
        """Handle breakpoint hit."""
        pass
    
    def _on_output(self, output: str) -> None:
        """Handle debug output."""
        pass