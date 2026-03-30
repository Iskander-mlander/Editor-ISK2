"""
Terminal Emulator Module
========================
Real terminal emulator using PTY for full shell support.
"""

import os
import pty
import select
import signal
import subprocess
import threading
from dataclasses import dataclass
from typing import Optional, List, Callable, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal, QProcess, QTimer
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QTextCursor, QKeyEvent


@dataclass
class TerminalConfig:
    """Terminal configuration."""
    shell: str = "/bin/bash"
    working_directory: str = ""
    environment: Dict[str, str] = None
    rows: int = 24
    columns: int = 80


class TerminalEmulator(QObject):
    """
    Real terminal emulator using PTY.
    Provides full terminal functionality with shell support.
    """
    
    output_received = pyqtSignal(str)
    finished = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._master_fd: Optional[int] = None
        self._process: Optional[subprocess.Popen] = None
        self._config = TerminalConfig()
        self._is_running = False
        
        self._read_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Buffer for partial reads
        self._buffer = ""
    
    @property
    def is_running(self) -> bool:
        """Check if terminal is running."""
        return self._is_running
    
    def start(self, config: Optional[TerminalConfig] = None) -> bool:
        """Start the terminal with the given configuration."""
        if self._is_running:
            return True
        
        if config:
            self._config = config
        
        # Prepare environment
        env = os.environ.copy()
        if self._config.environment:
            env.update(self._config.environment)
        
        # Set terminal type
        env['TERM'] = 'xterm-256color'
        
        # Set working directory
        cwd = self._config.working_directory or os.getcwd()
        
        try:
            # Create pseudo-terminal
            self._master_fd, slave_fd = pty.openpty()
            
            # Start shell
            self._process = subprocess.Popen(
                [self._config.shell],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                env=env,
                cwd=cwd,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Close slave in parent
            os.close(slave_fd)
            
            self._is_running = True
            
            # Start reading thread
            self._stop_event.clear()
            self._read_thread = threading.Thread(target=self._read_output, daemon=True)
            self._read_thread.start()
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to start terminal: {str(e)}")
            return False
    
    def _read_output(self) -> None:
        """Read output from the PTY in a background thread."""
        while not self._stop_event.is_set() and self._master_fd is not None:
            try:
                # Use select for non-blocking read
                ready, _, _ = select.select([self._master_fd], [], [], 0.1)
                
                if self._master_fd in ready:
                    try:
                        data = os.read(self._master_fd, 4096)
                        if data:
                            self.output_received.emit(data.decode('utf-8', errors='replace'))
                    except OSError:
                        break
                        
            except Exception:
                break
        
        # Process ended
        if self._process:
            self.finished.emit(self._process.returncode or 0)
        
        self._is_running = False
    
    def write(self, data: str) -> None:
        """Write data to the terminal."""
        if self._master_fd is not None and self._is_running:
            try:
                os.write(self._master_fd, data.encode('utf-8'))
            except OSError:
                pass
    
    def write_input(self, key: str) -> None:
        """Write a key press to the terminal."""
        self.write(key)
    
    def send_key(self, key: str) -> None:
        """Send a special key to the terminal."""
        # Map common keys to terminal codes
        key_map = {
            'enter': '\r',
            'tab': '\t',
            'backspace': '\x7f',
            'up': '\x1b[A',
            'down': '\x1b[B',
            'right': '\x1b[C',
            'left': '\x1b[D',
            'home': '\x1b[H',
            'end': '\x1b[F',
            'pageup': '\x1b[5~',
            'pagedown': '\x1b[6~',
            'escape': '\x1b',
            'f1': '\x1bOP',
            'f2': '\x1bOQ',
            'f3': '\x1bOR',
            'f4': '\x1bOS',
            'f5': '\x1b[15~',
            'f6': '\x1b[17~',
            'f7': '\x1b[18~',
            'f8': '\x1b[19~',
            'f9': '\x1b[20~',
            'f10': '\x1b[21~',
            'f11': '\x1b[23~',
            'f12': '\x1b[24~',
        }
        
        code = key_map.get(key.lower(), key)
        self.write(code)
    
    def resize(self, columns: int, rows: int) -> None:
        """Resize the terminal."""
        if self._master_fd is not None:
            try:
                # TIOCSWINSZ ioctl
                import fcntl
                import struct
                import termios
                
                winsize = struct.pack('HHHH', rows, columns, 0, 0)
                fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, winsize)
            except Exception:
                pass
    
    def stop(self) -> None:
        """Stop the terminal."""
        self._stop_event.set()
        
        if self._process:
            try:
                # Send SIGHUP to process group
                os.killpg(os.getpgid(self._process.pid), signal.SIGHUP)
                self._process.terminate()
                self._process.wait(timeout=2)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
        
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except Exception:
                pass
            self._master_fd = None
        
        self._is_running = False
    
    def send_signal(self, signal_num: int) -> None:
        """Send a signal to the terminal process."""
        if self._process:
            try:
                os.killpg(os.getpgid(self._process.pid), signal_num)
            except Exception:
                pass
    
    def interrupt(self) -> None:
        """Send interrupt signal (Ctrl+C)."""
        self.send_signal(signal.SIGINT)
    
    def suspend(self) -> None:
        """Suspend process (Ctrl+Z)."""
        self.send_signal(signal.SIGTSTP)
    
    def kill(self) -> None:
        """Kill the process."""
        self.send_signal(signal.SIGKILL)


class TerminalWidget(QPlainTextEdit):
    """
    Terminal widget that uses the PTY-based emulator.
    """
    
    command_executed = pyqtSignal(str)
    finished = pyqtSignal(int)
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        self._emulator = TerminalEmulator()
        self._emulator.output_received.connect(self._on_output)
        self._emulator.finished.connect(self._on_finished)
        
        self._setup_ui()
        self._start_terminal()
    
    def _setup_ui(self) -> None:
        """Setup the terminal widget UI."""
        self.setReadOnly(False)
        self.setCursorWidth(10)
        
        # Configure for terminal-like appearance
        from PyQt6.QtGui import QFont
        font = QFont("monospace")
        font.setPointSize(10)
        self.setFont(font)
        
        # Disable rich text
        self.setPlainText("")
    
    def _start_terminal(self) -> None:
        """Start the terminal emulator."""
        config = TerminalConfig()
        
        # Detect available shell
        for shell in [os.environ.get('SHELL', '/bin/bash'), '/bin/bash', '/bin/sh']:
            if os.path.exists(shell):
                config.shell = shell
                break
        
        self._emulator.start(config)
    
    def _on_output(self, text: str) -> None:
        """Handle terminal output."""
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.MoveOperation.End)
    
    def _on_finished(self, exit_code: int) -> None:
        """Handle terminal finished."""
        self.finished.emit(exit_code)
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        # Handle special keys
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            
            # Ctrl+C - interrupt
            if key == Qt.Key.Key_C:
                self._emulator.interrupt()
                return
            
            # Ctrl+D - EOF (exit shell)
            if key == Qt.Key.Key_D:
                self._emulator.write('\x04')
                return
            
            # Ctrl+Z - suspend
            if key == Qt.Key.Key_Z:
                self._emulator.suspend()
                return
            
            # Ctrl+L - clear
            if key == Qt.Key.Key_L:
                self._emulator.write('\x0c')
                return
        
        # Arrow keys
        if event.key() == Qt.Key.Key_Up:
            self._emulator.send_key('up')
            return
        if event.key() == Qt.Key.Key_Down:
            self._emulator.send_key('down')
            return
        if event.key() == Qt.Key.Key_Right:
            self._emulator.send_key('right')
            return
        if event.key() == Qt.Key.Key_Left:
            self._emulator.send_key('left')
            return
        
        # Function keys
        if event.key() == Qt.Key.Key_F1:
            self._emulator.send_key('f1')
            return
        if event.key() == Qt.Key.Key_F2:
            self._emulator.send_key('f2')
            return
        if event.key() == Qt.Key.Key_F3:
            self._emulator.send_key('f3')
            return
        if event.key() == Qt.Key.Key_F4:
            self._emulator.send_key('f4')
            return
        if event.key() == Qt.Key.Key_F5:
            self._emulator.send_key('f5')
            return
        
        # Tab
        if event.key() == Qt.Key.Key_Tab:
            self._emulator.write_input('\t')
            return
        
        # Backspace
        if event.key() == Qt.Key.Key_Backspace:
            self._emulator.write_input('\x7f')
            return
        
        # Enter
        if event.key() == Qt.Key.Key_Return:
            self._emulator.write_input('\r')
            return
        
        # Regular text
        text = event.text()
        if text:
            self._emulator.write(text)
    
    def run_command(self, command: str) -> None:
        """Run a specific command."""
        self._emulator.write(command + '\r')
        self.command_executed.emit(command)
    
    def interrupt(self) -> None:
        """Interrupt current command."""
        self._emulator.interrupt()
    
    def resizeEvent(self, event) -> None:
        """Handle resize to update terminal size."""
        super().resizeEvent(event)
        
        # Calculate terminal size
        font_metrics = self.fontMetrics()
        width = self.viewport().width()
        height = self.viewport().height()
        
        columns = width // font_metrics.horizontalAdvance('M')
        rows = height // font_metrics.height()
        
        # Resize terminal
        self._emulator.resize(columns, max(1, rows))
    
    def close(self) -> None:
        """Clean up on close."""
        self._emulator.stop()


# Import Qt for key handling
from PyQt6.QtCore import Qt