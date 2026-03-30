"""
Language Server Registry Module
===============================
Registers and configures language servers for different languages.
"""

import os
import shutil
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal


class ServerStatus(Enum):
    """Language server status."""
    NOT_INSTALLED = auto()
    INSTALLED = auto()
    RUNNING = auto()
    ERROR = auto()


@dataclass
class LanguageServerConfig:
    """Configuration for a language server."""
    language_id: str
    name: str
    command: List[str]
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    root_patterns: List[str] = field(default_factory=list)
    filetypes: List[str] = field(default_factory=list)
    initialization_options: Dict[str, Any] = field(default_factory=dict)
    install_command: str = ""
    install_hint: str = ""
    

class LanguageServerRegistry(QObject):
    """
    Registry for managing language servers.
    """
    
    servers_changed = pyqtSignal()
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._servers: Dict[str, LanguageServerConfig] = {}
        self._server_status: Dict[str, ServerStatus] = {}
        self._server_paths: Dict[str, str] = {}
        
        # Register default servers
        self._register_default_servers()
    
    def _register_default_servers(self) -> None:
        """Register default language servers."""
        # Python - pylsp
        self.register_server(LanguageServerConfig(
            language_id="python",
            name="Python LSP Server",
            command=["pylsp"],
            root_patterns=["pyproject.toml", "setup.py", "requirements.txt"],
            filetypes=["python"],
            install_command="pip install python-lsp-server",
            install_hint="pip install python-lsp-server"
        ))
        
        # Python - pyright
        self.register_server(LanguageServerConfig(
            language_id="python-type",
            name="Pyright",
            command=["pyright"],
            args=["--stdio"],
            root_patterns=["pyproject.toml", "setup.py"],
            filetypes=["python"],
            install_command="npm install -g pyright",
            install_hint="npm install -g pyright"
        ))
        
        # JavaScript/TypeScript - typescript-language-server
        self.register_server(LanguageServerConfig(
            language_id="javascript",
            name="JavaScript Language Server",
            command=["typescript-language-server"],
            args=["--stdio"],
            root_patterns=["package.json"],
            filetypes=["javascript", "javascriptreact"],
            install_command="npm install -g typescript-language-server",
            install_hint="npm install -g typescript-language-server"
        ))
        
        self.register_server(LanguageServerConfig(
            language_id="typescript",
            name="TypeScript Language Server",
            command=["typescript-language-server"],
            args=["--stdio"],
            root_patterns=["tsconfig.json", "package.json"],
            filetypes=["typescript", "typescriptreact"],
            install_command="npm install -g typescript-language-server",
            install_hint="npm install -g typescript-language-server"
        ))
        
        # JSON - vscode-json-languageserver
        self.register_server(LanguageServerConfig(
            language_id="json",
            name="JSON Language Server",
            command=["vscode-json-languageserver"],
            args=["--stdio"],
            root_patterns=["package.json"],
            filetypes=["json"],
            install_command="npm install -g vscode-json-languageserver",
            install_hint="npm install -g vscode-json-languageserver"
        ))
        
        # HTML - html-language-server
        self.register_server(LanguageServerConfig(
            language_id="html",
            name="HTML Language Server",
            command=["html-language-server"],
            args=["--stdio"],
            root_patterns=["package.json"],
            filetypes=["html"],
            install_command="npm install -g html-language-server",
            install_hint="npm install -g html-language-server"
        ))
        
        # CSS - css-language-server
        self.register_server(LanguageServerConfig(
            language_id="css",
            name="CSS Language Server",
            command=["css-language-server"],
            args=["--stdio"],
            root_patterns=["package.json"],
            filetypes=["css", "scss", "less"],
            install_command="npm install -g css-language-server",
            install_hint="npm install -g css-language-server"
        ))
        
        # Rust - rust-analyzer
        self.register_server(LanguageServerConfig(
            language_id="rust",
            name="Rust Analyzer",
            command=["rust-analyzer"],
            root_patterns=["Cargo.toml", "rust-toolchain"],
            filetypes=["rust"],
            install_command="cargo install rust-analyzer",
            install_hint="Run: cargo install rust-analyzer"
        ))
        
        # Go - gopls
        self.register_server(LanguageServerConfig(
            language_id="go",
            name="Go Language Server",
            command=["gopls"],
            root_patterns=["go.mod"],
            filetypes=["go"],
            install_command="go install golang.org/x/tools/gopls@latest",
            install_hint="go install golang.org/x/tools/gopls@latest"
        ))
        
        # C/C++ - clangd
        self.register_server(LanguageServerConfig(
            language_id="c",
            name="Clangd (C)",
            command=["clangd"],
            root_patterns=["compile_commands.json", ".clangd"],
            filetypes=["c", "h"],
            install_command="apt install clangd",
            install_hint="Install clangd via package manager"
        ))
        
        self.register_server(LanguageServerConfig(
            language_id="cpp",
            name="Clangd (C++)",
            command=["clangd"],
            root_patterns=["compile_commands.json", ".clangd", "CMakeLists.txt"],
            filetypes=["cpp", "cc", "cxx", "hpp", "hh"],
            install_command="apt install clangd",
            install_hint="Install clangd via package manager"
        ))
        
        # Java - eclipse.jdtls
        self.register_server(LanguageServerConfig(
            language_id="java",
            name="Eclipse JDT Language Server",
            command=["jdtls"],
            root_patterns=["pom.xml", "build.gradle", ".project"],
            filetypes=["java"],
            install_command="See https://github.com/eclipse/eclipse.jdt.ls",
            install_hint="Requires Eclipse JDT LS installation"
        ))
        
        # Vue - vls
        self.register_server(LanguageServerConfig(
            language_id="vue",
            name="Vetur Language Server",
            command=["vls"],
            root_patterns=["package.json", "vetur.config.js"],
            filetypes=["vue"],
            install_command="npm install -g vls",
            install_hint="npm install -g vls"
        ))
    
    def register_server(self, config: LanguageServerConfig) -> None:
        """Register a language server."""
        self._servers[config.language_id] = config
        self._server_status[config.language_id] = ServerStatus.NOT_INSTALLED
        self._check_installation(config.language_id)
        self.servers_changed.emit()
    
    def get_server(self, language_id: str) -> Optional[LanguageServerConfig]:
        """Get server configuration for a language."""
        return self._servers.get(language_id)
    
    def get_server_status(self, language_id: str) -> ServerStatus:
        """Get the status of a language server."""
        return self._server_status.get(language_id, ServerStatus.NOT_INSTALLED)
    
    def _check_installation(self, language_id: str) -> None:
        """Check if a language server is installed."""
        config = self._servers.get(language_id)
        if not config:
            return
        
        # Check if the command is available
        cmd = config.command[0]
        
        # Check in PATH
        if shutil.which(cmd):
            self._server_status[language_id] = ServerStatus.INSTALLED
            self._server_paths[language_id] = shutil.which(cmd)
        else:
            self._server_status[language_id] = ServerStatus.NOT_INSTALLED
    
    def is_installed(self, language_id: str) -> bool:
        """Check if a language server is installed."""
        return self.get_server_status(language_id) in (ServerStatus.INSTALLED, ServerStatus.RUNNING)
    
    def is_available(self, language_id: str) -> bool:
        """Check if a language server is available for a language."""
        # Check direct match
        if language_id in self._servers:
            return True
        
        # Check by file type
        for config in self._servers.values():
            if language_id in config.filetypes:
                return True
        
        return False
    
    def get_install_hint(self, language_id: str) -> str:
        """Get installation hint for a language server."""
        config = self._servers.get(language_id)
        return config.install_hint if config else ""
    
    def get_servers_for_filetype(self, filetype: str) -> List[LanguageServerConfig]:
        """Get all servers that support a file type."""
        servers = []
        
        for config in self._servers.values():
            if filetype in config.filetypes:
                servers.append(config)
        
        return servers
    
    def get_all_servers(self) -> Dict[str, LanguageServerConfig]:
        """Get all registered servers."""
        return self._servers.copy()
    
    def get_servers_by_status(self, status: ServerStatus) -> List[LanguageServerConfig]:
        """Get all servers with a specific status."""
        result = []
        
        for lang_id, st in self._server_status.items():
            if st == status:
                if lang_id in self._servers:
                    result.append(self._servers[lang_id])
        
        return result
    
    def refresh_status(self) -> None:
        """Refresh status of all servers."""
        for lang_id in self._servers:
            self._check_installation(lang_id)
        self.servers_changed.emit()
    
    def get_server_command(self, language_id: str) -> Optional[List[str]]:
        """Get the full command to start a language server."""
        config = self._servers.get(language_id)
        
        if config and self.is_installed(language_id):
            return config.command + config.args
        
        return None


class ServerManager(QObject):
    """
    Manages running language server processes.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._registry = LanguageServerRegistry()
        self._active_servers: Dict[str, Any] = {}
    
    @property
    def registry(self) -> LanguageServerRegistry:
        """Get the server registry."""
        return self._registry
    
    def start_server(self, language_id: str) -> bool:
        """Start a language server."""
        if language_id in self._active_servers:
            return True  # Already running
        
        cmd = self._registry.get_server_command(language_id)
        
        if not cmd:
            return False
        
        # TODO: Start the server process
        # This would integrate with the LSP client
        
        return False
    
    def stop_server(self, language_id: str) -> None:
        """Stop a language server."""
        if language_id in self._active_servers:
            # TODO: Stop the process
            del self._active_servers[language_id]
    
    def stop_all(self) -> None:
        """Stop all running servers."""
        for lang_id in list(self._active_servers.keys()):
            self.stop_server(lang_id)