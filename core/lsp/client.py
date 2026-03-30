"""
LSP Client Module
================
Language Server Protocol client implementation.
"""

import json
import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal


class LSPState(Enum):
    """LSP client states."""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    ERROR = auto()


@dataclass
class LSPMessage:
    """Represents an LSP message."""
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    is_notification: bool = False
    
    def to_json(self) -> str:
        """Convert message to JSON."""
        message: Dict[str, Any] = {}
        
        if self.id is not None:
            message["id"] = self.id
        
        if self.method:
            message["method"] = self.method
        
        if self.params is not None:
            message["params"] = self.params
        
        if self.result is not None:
            message["result"] = self.result
        
        if self.error is not None:
            message["error"] = self.error
        
        return json.dumps(message)
    
    @classmethod
    def from_json(cls, text: str) -> 'LSPMessage':
        """Parse message from JSON."""
        try:
            data = json.loads(text)
            return cls(
                id=data.get("id"),
                method=data.get("method"),
                params=data.get("params"),
                result=data.get("result"),
                error=data.get("error"),
                is_notification=data.get("id") is None and data.get("method") is not None
            )
        except json.JSONDecodeError:
            return cls()


@dataclass
class TextDocumentPosition:
    """Text document position for LSP requests."""
    uri: str
    line: int
    character: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "textDocument": {"uri": self.uri},
            "position": {"line": self.line, "character": self.character}
        }


class LSPSignals(QObject):
    """Signals for LSP client events."""
    state_changed = pyqtSignal(LSPState)
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)
    initialized = pyqtSignal()
    diagnostics_received = pyqtSignal(str, list)  # uri, diagnostics
    completion_received = pyqtSignal(list)  # items
    hover_received = pyqtSignal(dict)  # hover info
    signature_received = pyqtSignal(dict)  # signature info
    definition_received = pyqtSignal(dict)  # definition location
    references_received = pyqtSignal(list)  # references
    document_symbols_received = pyqtSignal(list)  # symbols


class LSPClient(QObject):
    """
    Language Server Protocol client.
    Communicates with LSP servers using JSON-RPC.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = LSPSignals()
        self._state = LSPState.STOPPED
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._pending_requests: Dict[int, Callable[[Any], None]] = {}
        self._notification_handlers: Dict[str, Callable] = {}
        self._response_queue: queue.Queue = queue.Queue()
        self._listener_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._server_command: List[str] = []
        self._root_uri: Optional[str] = None
        self._capabilities: Dict[str, Any] = {}
        
        # Register default notification handlers
        self._register_default_handlers()
    
    @property
    def signals(self) -> LSPSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def state(self) -> LSPState:
        """Get the current state."""
        return self._state
    
    @property
    def is_running(self) -> bool:
        """Check if the LSP server is running."""
        return self._state == LSPState.RUNNING
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        return self._capabilities
    
    def _register_default_handlers(self) -> None:
        """Register default notification handlers."""
        self._notification_handlers["textDocument/publishDiagnostics"] = \
            self._handle_publish_diagnostics
        self._notification_handlers["$/progress"] = self._handle_progress
    
    def _set_state(self, state: LSPState) -> None:
        """Set the client state."""
        self._state = state
        self._signals.state_changed.emit(state)
    
    def start(self, command: Union[str, List[str]], root_path: Optional[str] = None) -> bool:
        """
        Start the LSP server.
        
        Args:
            command: The command to start the server
            root_path: The root path of the project
            
        Returns:
            True if started successfully
        """
        if isinstance(command, str):
            command = command.split()
        
        self._server_command = command
        self._root_uri = self._path_to_uri(root_path) if root_path else None
        
        self._set_state(LSPState.STARTING)
        
        try:
            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Start listener threads
            self._listener_thread = threading.Thread(
                target=self._listen_stdout,
                daemon=True
            )
            self._listener_thread.start()
            
            self._stderr_thread = threading.Thread(
                target=self._listen_stderr,
                daemon=True
            )
            self._stderr_thread.start()
            
            # Wait for server to initialize
            time.sleep(0.5)
            
            # Send initialize request
            if self._initialize():
                self._set_state(LSPState.RUNNING)
                self._signals.server_started.emit()
                self._signals.initialized.emit()
                return True
            else:
                self._set_state(LSPState.ERROR)
                return False
                
        except Exception as e:
            self._set_state(LSPState.ERROR)
            self._signals.server_error.emit(str(e))
            return False
    
    def stop(self) -> None:
        """Stop the LSP server."""
        if self._process:
            try:
                # Send shutdown request
                self._send_request("shutdown", {})
                time.sleep(0.1)
                
                # Send exit notification
                self._send_notification("exit", {})
                
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                pass
            finally:
                self._process = None
        
        self._set_state(LSPState.STOPPED)
        self._signals.server_stopped.emit()
    
    def _path_to_uri(self, path: str) -> str:
        """Convert a file path to a file URI."""
        import urllib.parse
        return f"file://{urllib.parse.quote(path)}"
    
    def _uri_to_path(self, uri: str) -> str:
        """Convert a file URI to a file path."""
        import urllib.parse
        if uri.startswith("file://"):
            return urllib.parse.unquote(uri[7:])
        return uri
    
    def _listen_stdout(self) -> None:
        """Listen to server stdout."""
        if not self._process:
            return
        
        buffer = ""
        
        try:
            for char in iter(lambda: self._process.stdout.read(1), ''):
                if not char:
                    break
                
                buffer += char
                
                # Try to parse complete JSON messages
                if buffer.strip():
                    try:
                        # Check if we have a complete JSON object
                        json.loads(buffer)
                        self._response_queue.put(buffer)
                        buffer = ""
                    except json.JSONDecodeError:
                        # Check for content-length header
                        if "\r\n\r\n" in buffer:
                            parts = buffer.split("\r\n\r\n", 1)
                            if parts[0].startswith("Content-Length:"):
                                content_length = int(parts[0].split(":")[1].strip())
                                if len(parts[1]) >= content_length:
                                    self._response_queue.put(parts[1])
                                    buffer = ""
        except Exception:
            pass
    
    def _listen_stderr(self) -> None:
        """Listen to server stderr."""
        if not self._process:
            return
        
        try:
            for line in self._process.stderr:
                if line.strip():
                    # Log stderr (could be connected to a logger)
                    pass
        except Exception:
            pass
    
    def _process_responses(self) -> None:
        """Process responses from the queue."""
        while True:
            try:
                response_text = self._response_queue.get_nowait()
                message = LSPMessage.from_json(response_text)
                self._handle_message(message)
            except queue.Empty:
                break
    
    def _handle_message(self, message: LSPMessage) -> None:
        """Handle an incoming LSP message."""
        # Handle response
        if message.id is not None and message.id in self._pending_requests:
            callback = self._pending_requests.pop(message.id)
            if message.result is not None:
                callback(message.result)
            elif message.error is not None:
                callback(None)
        
        # Handle notification
        elif message.is_notification and message.method:
            handler = self._notification_handlers.get(message.method)
            if handler and message.params:
                handler(message.params)
    
    def _handle_publish_diagnostics(self, params: Dict[str, Any]) -> None:
        """Handle diagnostic notifications."""
        uri = params.get("uri", "")
        diagnostics = params.get("diagnostics", [])
        self._signals.diagnostics_received.emit(uri, diagnostics)
    
    def _handle_progress(self, params: Dict[str, Any]) -> None:
        """Handle progress notifications."""
        pass
    
    def _initialize(self) -> bool:
        """Send initialize request."""
        params = {
            "processId": 0,
            "rootUri": self._root_uri,
            "capabilities": {
                "textDocument": {
                    "synchronization": {
                        "willSave": True,
                        "didSave": True,
                        "willSaveWaitUntil": True
                    },
                    "completion": {
                        "completionItem": {
                            "snippetSupport": True,
                            "documentationFormat": ["markdown", "plaintext"]
                        }
                    },
                    "hover": True,
                    "definition": True,
                    "references": True,
                    "documentSymbol": True,
                    "codeAction": True,
                    "formatting": True,
                    "rangeFormatting": True
                },
                "workspace": {
                    "applyEdit": True,
                    "workspaceFolders": True
                }
            }
        }
        
        result = self._send_request("initialize", params)
        if result:
            self._capabilities = result.get("capabilities", {})
        return result is not None
    
    def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Any]:
        """Send a request to the server."""
        if not self._process or not self._process.stdin:
            return None
        
        request_id = self._request_id
        self._request_id += 1
        
        message = LSPMessage(id=request_id, method=method, params=params)
        
        # Create JSON-RPC message
        json_content = message.to_json()
        content_length = len(json_content.encode('utf-8'))
        
        rpc_message = f"Content-Length: {content_length}\r\n\r\n{json_content}"
        
        try:
            self._process.stdin.write(rpc_message)
            self._process.stdin.flush()
            
            # Wait for response
            time.sleep(0.1)
            self._process_responses()
            
        except Exception as e:
            self._signals.server_error.emit(str(e))
            return None
        
        return None
    
    def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send a notification to the server."""
        if not self._process or not self._process.stdin:
            return
        
        message = LSPMessage(method=method, params=params, is_notification=True)
        
        json_content = message.to_json()
        content_length = len(json_content.encode('utf-8'))
        
        rpc_message = f"Content-Length: {content_length}\r\n\r\n{json_content}"
        
        try:
            self._process.stdin.write(rpc_message)
            self._process.stdin.flush()
        except Exception:
            pass
    
    # Public API methods
    
    def did_open(self, uri: str, language_id: str, text: str, version: int = 1) -> None:
        """Notify server that a document was opened."""
        params = {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "text": text,
                "version": version
            }
        }
        self._send_notification("textDocument/didOpen", params)
    
    def did_change(self, uri: str, text: str, version: int = 1) -> None:
        """Notify server that a document was changed."""
        params = {
            "textDocument": {
                "uri": uri,
                "version": version
            },
            "contentChanges": [
                {"text": text}
            ]
        }
        self._send_notification("textDocument/didChange", params)
    
    def did_save(self, uri: str, text: Optional[str] = None) -> None:
        """Notify server that a document was saved."""
        params = {
            "textDocument": {"uri": uri}
        }
        if text is not None:
            params["textDocument"]["text"] = text
        self._send_notification("textDocument/didSave", params)
    
    def did_close(self, uri: str) -> None:
        """Notify server that a document was closed."""
        params = {
            "textDocument": {"uri": uri}
        }
        self._send_notification("textDocument/didClose", params)
    
    def completion(self, uri: str, line: int, character: int) -> None:
        """Request completions at a position."""
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character}
        }
        
        def handle_result(result: Any) -> None:
            items = result.get("items", []) if result else []
            self._signals.completion_received.emit(items)
        
        self._pending_requests[self._request_id] = handle_result
        self._send_request("textDocument/completion", params)
    
    def hover(self, uri: str, line: int, character: int) -> None:
        """Request hover information at a position."""
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character}
        }
        
        def handle_result(result: Any) -> None:
            self._signals.hover_received.emit(result or {})
        
        self._pending_requests[self._request_id] = handle_result
        self._send_request("textDocument/hover", params)
    
    def definition(self, uri: str, line: int, character: int) -> None:
        """Request definition at a position."""
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character}
        }
        
        def handle_result(result: Any) -> None:
            self._signals.definition_received.emit(result or {})
        
        self._pending_requests[self._request_id] = handle_result
        self._send_request("textDocument/definition", params)
    
    def references(self, uri: str, line: int, character: int) -> None:
        """Request references at a position."""
        params = {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": character},
            "context": {"includeDeclaration": True}
        }
        
        def handle_result(result: Any) -> None:
            refs = result.get("references", []) if result else []
            self._signals.references_received.emit(refs)
        
        self._pending_requests[self._request_id] = handle_result
        self._send_request("textDocument/references", params)
    
    def document_symbols(self, uri: str) -> None:
        """Request document symbols."""
        params = {
            "textDocument": {"uri": uri}
        }
        
        def handle_result(result: Any) -> None:
            symbols = result or []
            self._signals.document_symbols_received.emit(symbols)
        
        self._pending_requests[self._request_id] = handle_result
        self._send_request("textDocument/documentSymbol", params)
