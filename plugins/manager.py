"""
Plugin Manager Module
=====================
Manages plugin loading, activation, and lifecycle.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Optional, Dict, List, Type, Any

from PyQt6.QtCore import QObject, pyqtSignal

from .base import Plugin, PluginMetadata, PluginState


class PluginManagerSignals(QObject):
    """Signals for plugin manager events."""
    plugin_loaded = pyqtSignal(str)
    plugin_unloaded = pyqtSignal(str)
    plugin_activated = pyqtSignal(str)
    plugin_deactivated = pyqtSignal(str)
    plugin_error = pyqtSignal(str, str)
    all_plugins_loaded = pyqtSignal()


class PluginManager(QObject):
    """
    Manages plugin lifecycle and discovery.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = PluginManagerSignals()
        
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}
        self._plugin_paths: List[Path] = []
        self._load_order: List[str] = []
    
    @property
    def signals(self) -> PluginManagerSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def plugins(self) -> Dict[str, Plugin]:
        """Get all loaded plugins."""
        return self._plugins
    
    def add_plugin_path(self, path: Path) -> None:
        """Add a path to search for plugins."""
        if path not in self._plugin_paths:
            self._plugin_paths.append(path)
    
    def register_plugin_class(self, plugin_class: Type[Plugin], plugin_id: str) -> None:
        """Register a plugin class."""
        self._plugin_classes[plugin_id] = plugin_class
    
    def discover_plugins(self) -> List[str]:
        """Discover plugins in the plugin paths."""
        discovered = []
        
        for plugin_path in self._plugin_paths:
            if not plugin_path.exists():
                continue
            
            for item in plugin_path.iterdir():
                if item.is_file() and item.suffix == ".py":
                    plugin_id = item.stem
                    if plugin_id not in self._plugin_classes:
                        discovered.append(plugin_id)
                elif item.is_dir() and (item / "__init__.py").exists():
                    plugin_id = item.name
                    if plugin_id not in self._plugin_classes:
                        discovered.append(plugin_id)
        
        return discovered
    
    def load_plugin(self, plugin_id: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load a plugin.
        
        Args:
            plugin_id: Plugin identifier
            config: Optional configuration
            
        Returns:
            True if loaded successfully
        """
        # Check if already loaded
        if plugin_id in self._plugins:
            return True
        
        # Get plugin class
        plugin_class = self._plugin_classes.get(plugin_id)
        if not plugin_class:
            self._signals.plugin_error.emit(plugin_id, "Plugin class not found")
            return False
        
        try:
            # Create plugin instance
            plugin = plugin_class()
            
            # Check dependencies
            if plugin.metadata and plugin.metadata.dependencies:
                for dep in plugin.metadata.dependencies:
                    if dep not in self._plugins:
                        self._signals.plugin_error.emit(
                            plugin_id,
                            f"Missing dependency: {dep}"
                        )
                        return False
            
            # Load plugin
            if not plugin.load(config):
                self._signals.plugin_error.emit(plugin_id, "Load failed")
                return False
            
            # Store plugin
            self._plugins[plugin_id] = plugin
            self._load_order.append(plugin_id)
            self._signals.plugin_loaded.emit(plugin_id)
            
            return True
            
        except Exception as e:
            self._signals.plugin_error.emit(plugin_id, str(e))
            return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if unloaded successfully
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        
        # Check if other plugins depend on this one
        for other_id, other_plugin in self._plugins.items():
            if other_id == plugin_id:
                continue
            if other_plugin.metadata and other_plugin.metadata.dependencies:
                if plugin_id in other_plugin.metadata.dependencies:
                    self._signals.plugin_error.emit(
                        other_id,
                        f"Cannot unload: {plugin_id} is a dependency"
                    )
                    return False
        
        # Deactivate if active
        if plugin.state == PluginState.ACTIVE:
            plugin.deactivate()
        
        # Unload
        if not plugin.unload():
            return False
        
        # Remove
        del self._plugins[plugin_id]
        self._load_order.remove(plugin_id)
        self._signals.plugin_unloaded.emit(plugin_id)
        
        return True
    
    def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if activated successfully
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        
        if plugin.state != PluginState.LOADED:
            return False
        
        # Activate dependencies first
        if plugin.metadata and plugin.metadata.dependencies:
            for dep in plugin.metadata.dependencies:
                dep_plugin = self._plugins.get(dep)
                if dep_plugin and dep_plugin.state != PluginState.ACTIVE:
                    if not self.activate_plugin(dep):
                        return False
        
        if plugin.activate():
            self._signals.plugin_activated.emit(plugin_id)
            return True
        
        return False
    
    def deactivate_plugin(self, plugin_id: str) -> bool:
        """
        Deactivate a plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if deactivated successfully
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin or plugin.state != PluginState.ACTIVE:
            return False
        
        # Check if other active plugins depend on this one
        for other_id, other_plugin in self._plugins.items():
            if other_id == plugin_id or other_plugin.state != PluginState.ACTIVE:
                continue
            if other_plugin.metadata and other_plugin.metadata.dependencies:
                if plugin_id in other_plugin.metadata.dependencies:
                    self._signals.plugin_error.emit(
                        other_id,
                        f"Cannot deactivate: {plugin_id} is a dependency"
                    )
                    return False
        
        if plugin.deactivate():
            self._signals.plugin_deactivated.emit(plugin_id)
            return True
        
        return False
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)
    
    def get_active_plugins(self) -> List[Plugin]:
        """Get all active plugins."""
        return [
            p for p in self._plugins.values()
            if p.state == PluginState.ACTIVE
        ]
    
    def load_all(self, configs: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """
        Load all registered plugins.
        
        Args:
            configs: Optional configurations for each plugin
        """
        configs = configs or {}
        
        # Load in dependency order
        for plugin_id in self._load_order:
            config = configs.get(plugin_id)
            self.load_plugin(plugin_id, config)
        
        # Activate in order
        for plugin_id in self._load_order:
            plugin = self._plugins.get(plugin_id)
            if plugin and plugin.state == PluginState.LOADED:
                self.activate_plugin(plugin_id)
        
        self._signals.all_plugins_loaded.emit()
    
    def unload_all(self) -> None:
        """Unload all plugins in reverse order."""
        # Deactivate in reverse order
        for plugin_id in reversed(self._load_order):
            plugin = self._plugins.get(plugin_id)
            if plugin and plugin.state == PluginState.ACTIVE:
                plugin.deactivate()
        
        # Unload in reverse order
        for plugin_id in reversed(self._load_order):
            plugin = self._plugins.get(plugin_id)
            if plugin:
                plugin.unload()
        
        self._plugins.clear()
        self._load_order.clear()
    
    def reload_plugin(self, plugin_id: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Reload a plugin."""
        if plugin_id in self._plugins:
            self.unload_plugin(plugin_id)
        
        return self.load_plugin(plugin_id, config)