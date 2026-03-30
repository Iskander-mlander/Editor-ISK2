"""
Terminal Widget
==============
Embedded terminal emulator with output capture and command execution.
"""

import subprocess
import os
import shlex
from typing import Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QProcess, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QKeyEvent


class Terminal(QWidget):
    """
    Terminal emulator widget with execution support.
    """
    
    execution_finished = pyqtSignal(int)  # exit code
    execution_error = pyqtSignal(str)  # error message
    output_received = pyqtSignal(str)  # output text (stdout/stderr)
    
    # File extension to interpreter mapping
    INTERPRETERS = {
        ".py": ["python3", "python"],
        ".js": ["node"],
        ".sh": ["bash", "sh"],
        ".bash": ["bash"],
        ".zsh": ["zsh"],
        ".rb": ["ruby"],
        ".php": ["php"],
        ".pl": ["perl"],
        ".lua": ["lua"],
        ".go": ["go", "go run"],
        ".rs": ["rustc", "cargo run"],
        ".java": ["java"],
        ".c": ["gcc"],
        ".cpp": ["g++"],
        ".r": ["Rscript"],
        ".ps1": ["powershell"],
    }
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._process: Optional[QProcess] = None
        self._current_file: Optional[str] = None
        self._working_directory: Optional[str] = None
        self._python_interpreter: str = "python3"
        self._command_history: List[str] = []
        self._history_index: int = -1
        self._language: str = "es"  # Default language
        
        # Messages (will be set by _update_ui_texts)
        self._msg_no_file: str = "No hay archivo para ejecutar. Guarda el archivo primero."
        self._msg_file_not_found: str = "Archivo no encontrado:"
        self._msg_running: str = "Ejecutando con"
        self._msg_finished: str = "Finalizado con código de salida"
        self._msg_stopped: str = "[Ejecución detenida]"
        self._msg_error: str = "[Error:"
        
        # Callback to get current file from main window
        self._get_current_file_callback = None
        
        # Output buffer for diagnostics
        self._output_buffer: List[str] = []
        
        self._setup_ui()
        self._update_ui_texts()
    
    def set_get_current_file_callback(self, callback) -> None:
        """Set a callback function to get the current file from the main window."""
        self._get_current_file_callback = callback
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar with buttons
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(2, 2, 2, 2)
        
        # Interpreter label
        self._interpreter_label = QLabel("Python:")
        toolbar.addWidget(self._interpreter_label)
        
        self._interpreter_combo = QComboBox()
        self._interpreter_combo.setFixedWidth(120)
        self._interpreter_combo.addItems(["python3", "python", "python2"])
        self._interpreter_combo.currentTextChanged.connect(self._on_interpreter_changed)
        toolbar.addWidget(self._interpreter_combo)
        
        toolbar.addSpacing(10)
        
        self._run_btn = QPushButton("Run")
        self._run_btn.setFixedWidth(70)
        self._run_btn.clicked.connect(self._on_run_clicked)
        toolbar.addWidget(self._run_btn)
        
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setFixedWidth(70)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        toolbar.addWidget(self._stop_btn)
        
        toolbar.addStretch()
        
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedWidth(70)
        self._clear_btn.clicked.connect(self.clear_output)
        toolbar.addWidget(self._clear_btn)
        
        layout.addLayout(toolbar)
        
        # Output area
        self._output = QPlainTextEdit()
        self._output.setReadOnly(False)  # Allow selecting text
        self._output.setFont(QFont("monospace"))
        self._output.setPlaceholderText("Output will appear here...\n\nUse the input field below to run commands.")
        layout.addWidget(self._output)
        
        # Input line for custom commands
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(2, 2, 2, 2)
        
        self._input_label = QLabel("$")
        input_layout.addWidget(self._input_label)
        
        self._command_input = QLineEdit()
        self._command_input.setFont(QFont("monospace"))
        self._command_input.returnPressed.connect(self._on_command_submitted)
        input_layout.addWidget(self._command_input)
        
        layout.addLayout(input_layout)
        
        # Initialize
        self._detect_python_versions()
    
    def _detect_python_versions(self) -> None:
        """Detect available Python versions."""
        versions = set()
        
        for binary in ["python3", "python", "python2"]:
            try:
                result = subprocess.run(
                    [binary, "--version"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    versions.add(binary)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if versions:
            self._interpreter_combo.clear()
            for v in sorted(versions):
                self._interpreter_combo.addItem(v)
    
    def set_language(self, lang_code: str) -> None:
        """Set the UI language."""
        self._language = lang_code
        self._update_ui_texts()
    
    def _update_ui_texts(self) -> None:
        """Update UI texts based on current language."""
        self._msg_no_file = "No hay archivo para ejecutar. Guarda el archivo primero." if self._language == "es" else "No file to run. Save the file first."
        self._msg_file_not_found = "Archivo no encontrado:" if self._language == "es" else "File not found:"
        self._msg_running = "Ejecutando con" if self._language == "es" else "Running with"
        self._msg_finished = "Finalizado con código de salida" if self._language == "es" else "Finished with exit code"
        self._msg_stopped = "[Ejecución detenida]" if self._language == "es" else "[Execution stopped]"
        self._msg_error = "[Error:" if self._language == "es" else "[Error:"
        
        if self._language == "es":
            self._interpreter_label.setText("Intérprete:")
            self._run_btn.setText("Ejecutar")
            self._stop_btn.setText("Detener")
            self._clear_btn.setText("Limpiar")
            self._output.setPlaceholderText("La salida aparecerá aquí...\n\nUsa el campo de abajo para ejecutar comandos.")
            self._input_label.setText("$")
        else:
            self._interpreter_label.setText("Interpreter:")
            self._run_btn.setText("Run")
            self._stop_btn.setText("Stop")
            self._clear_btn.setText("Clear")
            self._output.setPlaceholderText("Output will appear here...\n\nUse the input field below to run commands.")
            self._input_label.setText("$")
    
    def set_current_file_from_editor(self, file_path: Optional[str]) -> None:
        """Set current file from editor (external source)."""
        self._current_file = file_path
        if file_path:
            self.set_active_file(file_path)
    
    def get_interpreter_for_file(self, file_path: str) -> tuple[str, List[str]]:
        """Get the interpreter and arguments for a file based on its extension."""
        if not file_path:
            return "python3", []
        
        ext = Path(file_path).suffix.lower()
        
        # Check if we have an interpreter for this extension
        if ext in self.INTERPRETERS:
            interp_list = self.INTERPRETERS[ext]
            # Try each interpreter until we find one that works
            for interp in interp_list:
                if " " in interp:  # e.g., "go run" or "cargo run"
                    parts = interp.split(" ")
                    return parts[0], parts[1:] + [file_path]
                # Check if interpreter exists
                try:
                    subprocess.run([interp, "--version"], capture_output=True, timeout=2)
                    return interp, [file_path]
                except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    continue
        
        # Default to python3
        return "python3", [file_path]
    
    def set_active_file(self, file_path: Optional[str]) -> None:
        """Set the active file from the editor and update interpreter."""
        self._current_file = file_path
        
        if file_path:
            ext = Path(file_path).suffix.lower()
            
            # Update interpreter combo based on file type
            if ext == ".py":
                self._interpreter_label.setText("Python:")
                self._interpreter_combo.setVisible(True)
                self._interpreter_combo.setEnabled(True)
            else:
                # For non-Python files, try to detect interpreter
                interp, args = self.get_interpreter_for_file(file_path)
                self._interpreter_label.setText(f"{ext}:")
                self._interpreter_combo.setVisible(False)
    
    def _on_interpreter_changed(self, interpreter: str) -> None:
        """Handle interpreter change."""
        self._python_interpreter = interpreter
    
    def _on_run_clicked(self) -> None:
        """Handle run button click."""
        # Try to get current file from callback if available
        file_to_run = self._current_file
        if not file_to_run and self._get_current_file_callback:
            file_to_run = self._get_current_file_callback()
        self.run_file(file_to_run)
    
    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.stop_execution()
    
    def _on_command_submitted(self) -> None:
        """Handle command submission."""
        command = self._command_input.text().strip()
        
        if not command:
            return
        
        # Add to history
        self._command_history.append(command)
        self._history_index = len(self._command_history)
        
        # Clear input
        self._command_input.clear()
        
        # Execute command
        self.run_command(command)
    
    def _navigate_history(self, direction: int) -> None:
        """Navigate command history."""
        if not self._command_history:
            return
        
        if direction == -1:  # Up
            if self._history_index > 0:
                self._history_index -= 1
        else:  # Down
            if self._history_index < len(self._command_history) - 1:
                self._history_index += 1
            else:
                self._history_index = len(self._command_history)
                self._command_input.clear()
                return
        
        if 0 <= self._history_index < len(self._command_history):
            self._command_input.setText(self._command_history[self._history_index])
    
    def run_file(self, file_path: Optional[str], arguments: Optional[List[str]] = None) -> None:
        """Run a file in the terminal based on its extension."""
        if not file_path:
            self.append_output(f"{self._msg_no_file}\n", error=True)
            return
        
        if not os.path.exists(file_path):
            self.append_output(f"{self._msg_file_not_found} {file_path}\n", error=True)
            return
        
        self._current_file = file_path
        
        # Get working directory from file
        self._working_directory = os.path.dirname(os.path.abspath(file_path))
        
        # Clear previous output and buffer
        self._output.clear()
        self._output_buffer = []
        
        # Detect interpreter based on file extension
        interpreter, base_args = self.get_interpreter_for_file(file_path)
        
        # Build command
        cmd = [interpreter]
        
        # Add arguments from parameter
        if arguments:
            cmd.extend(arguments)
        else:
            # Add file path if not already in base_args
            if base_args and base_args[0] != file_path:
                cmd.extend(base_args)
            elif not base_args:
                cmd.append(file_path)
        
        # Show which interpreter is being used
        self.append_output(f"{self._msg_running} {interpreter}: {' '.join(cmd)}\n", highlight=True)
        self.append_output("=" * 50 + "\n")
        self.append_output("=" * 50 + "\n")
        
        # Disable run, enable stop
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        
        # Create process
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.setWorkingDirectory(self._working_directory)
        
        # Connect signals
        self._process.readyReadStandardOutput.connect(self._on_output_ready)
        self._process.finished.connect(self._on_process_finished)
        self._process.errorOccurred.connect(self._on_error_occurred)
        
        # Start process
        self._process.start(cmd[0], cmd[1:])
    
    def run_command(self, command: str) -> None:
        """Run a shell command."""
        # Clear previous output
        self._output.clear()
        
        # Determine working directory
        cwd = self._working_directory or os.getcwd()
        
        # Show command being run
        self.append_output(f"$ {command}\n", highlight=True)
        self.append_output("-" * 50 + "\n")
        
        # Disable run, enable stop
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        
        # Create process
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.setWorkingDirectory(cwd)
        
        # Parse command
        try:
            args = shlex.split(command)
        except ValueError:
            args = command.split()
        
        # Connect signals
        self._process.readyReadStandardOutput.connect(self._on_output_ready)
        self._process.finished.connect(self._on_process_finished)
        self._process.errorOccurred.connect(self._on_error_occurred)
        
        # Start process
        if args:
            self._process.start(args[0], args[1:])
    
    def stop_execution(self) -> None:
        """Stop the current execution."""
        if self._process and self._process.state() == QProcess.ProcessState.Running:
            self._process.kill()
            self._process.waitForFinished(1000)
            self.append_output(f"\n{self._msg_stopped}\n", error=True)
        
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
    
    def _on_output_ready(self) -> None:
        """Handle process output."""
        if self._process:
            output = self._process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            self._output.insertPlainText(output)
            # Accumulate output for diagnostics
            self._output_buffer.append(output)
            # Emit accumulated output signal for diagnostics panel
            self.output_received.emit(''.join(self._output_buffer))
            # Scroll to bottom
            self._output.moveCursor(QTextCursor.MoveOperation.End)
    
    def _on_process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """Handle process finished."""
        self.append_output("\n" + "=" * 50 + "\n")
        if exit_code == 0:
            self.append_output(f"[{self._msg_finished} 0]\n", success=True)
        else:
            self.append_output(f"[{self._msg_finished} {exit_code}]\n", error=True)
        
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self.execution_finished.emit(exit_code)
    
    def _on_error_occurred(self, error: QProcess.ProcessError) -> None:
        """Handle process error."""
        error_msg = self._process.errorString()
        self.append_output(f"\n{self._msg_error} {error_msg}]\n", error=True)
        self.execution_error.emit(error_msg)
        
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
    
    def append_output(self, text: str, highlight: bool = False, error: bool = False, success: bool = False) -> None:
        """Append text to output with optional styling."""
        self._output.appendPlainText(text)
        self._output.moveCursor(QTextCursor.MoveOperation.End)
    
    def clear_output(self) -> None:
        """Clear output."""
        self._output.clear()
        self._command_input.clear()
    
    def set_current_file(self, file_path: Optional[str]) -> None:
        """Set the current file to run."""
        self._current_file = file_path
    
    def set_working_directory(self, path: str) -> None:
        """Set the working directory."""
        if os.path.isdir(path):
            self._working_directory = path


class DiagnosticsPanel(QWidget):
    """
    Panel for displaying diagnostic messages.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QLabel
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._list = QListWidget()
        layout.addWidget(self._list)
    
    def set_diagnostics(self, diagnostics: List[dict]) -> None:
        """Set diagnostics to display."""
        self._list.clear()
        
        for diag in diagnostics:
            message = diag.get("message", "")
            severity = diag.get("severity", 3)  # 1=error, 2=warning, 3=info
            source = diag.get("source", "LSP")
            
            if severity == 1:
                prefix = "E"
            elif severity == 2:
                prefix = "W"
            else:
                prefix = "I"
            
            item = QListWidgetItem(f"[{prefix}] {message} ({source})")
            self._list.addItem(item)
    
    def clear_diagnostics(self) -> None:
        """Clear all diagnostics."""
        self._list.clear()


class GitPanel(QWidget):
    """
    Git panel (placeholder - see ui/widgets/git_panel.py for real implementation).
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        from PyQt6.QtWidgets import QVBoxLayout, QLabel
        
        layout = QVBoxLayout(self)
        
        label = QLabel("Git panel moved to ui/widgets/git_panel.py")
        layout.addWidget(label)