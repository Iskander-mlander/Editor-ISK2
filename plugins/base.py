"""
Plugin Base Module
==================
Base class for editor plugins.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal


class PluginState(Enum):
    """Plugin states."""
    UNLOADED = auto()
    LOADING = auto()
    LOADED = auto()
    ACTIVE = auto()
    ERROR = auto()


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    id: str
    name: str
    version: str
    author: str = ""
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    license: str = ""
    website: str = ""


class PluginSignals(QObject):
    """Signals for plugin events."""
    state_changed = pyqtSignal(PluginState)
    loaded = pyqtSignal()
    activated = pyqtSignal()
    deactivated = pyqtSignal()
    error = pyqtSignal(str)


class Plugin(QObject):
    """
    Base class for all plugins.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = PluginSignals()
        self._metadata: Optional[PluginMetadata] = None
        self._state = PluginState.UNLOADED
        self._config: Dict[str, Any] = {}
    
    @property
    def signals(self) -> PluginSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def metadata(self) -> Optional[PluginMetadata]:
        """Get plugin metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, metadata: PluginMetadata) -> None:
        """Set plugin metadata."""
        self._metadata = metadata
    
    @property
    def state(self) -> PluginState:
        """Get plugin state."""
        return self._state
    
    @property
    def id(self) -> str:
        """Get plugin ID."""
        return self._metadata.id if self._metadata else ""
    
    @property
    def name(self) -> str:
        """Get plugin name."""
        return self._metadata.name if self._metadata else ""
    
    def _set_state(self, state: PluginState) -> None:
        """Set plugin state."""
        self._state = state
        self._signals.state_changed.emit(state)
    
    def load(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load the plugin.
        
        Args:
            config: Plugin configuration
            
        Returns:
            True if loaded successfully
        """
        if self._state not in (PluginState.UNLOADED, PluginState.ERROR):
            return False
        
        self._set_state(PluginState.LOADING)
        
        try:
            if config:
                self._config = config
            
            result = self._on_load(config or {})
            
            if result:
                self._set_state(PluginState.LOADED)
                self._signals.loaded.emit()
                return True
            else:
                self._set_state(PluginState.ERROR)
                return False
                
        except Exception as e:
            self._set_state(PluginState.ERROR)
            self._signals.error.emit(str(e))
            return False
    
    def unload(self) -> bool:
        """
        Unload the plugin.
        
        Returns:
            True if unloaded successfully
        """
        if self._state not in (PluginState.LOADED, PluginState.ACTIVE):
            return False
        
        try:
            self._on_unload()
            self._set_state(PluginState.UNLOADED)
            return True
        except Exception as e:
            self._signals.error.emit(str(e))
            return False
    
    def activate(self) -> bool:
        """
        Activate the plugin.
        
        Returns:
            True if activated successfully
        """
        if self._state != PluginState.LOADED:
            return False
        
        try:
            result = self._on_activate()
            
            if result:
                self._set_state(PluginState.ACTIVE)
                self._signals.activated.emit()
                return True
            else:
                return False
                
        except Exception as e:
            self._set_state(PluginState.ERROR)
            self._signals.error.emit(str(e))
            return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the plugin.
        
        Returns:
            True if deactivated successfully
        """
        if self._state != PluginState.ACTIVE:
            return False
        
        try:
            self._on_deactivate()
            self._set_state(PluginState.LOADED)
            self._signals.deactivated.emit()
            return True
        except Exception as e:
            self._signals.error.emit(str(e))
            return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
    
    # Override these methods in subclasses
    
    def _on_load(self, config: Dict[str, Any]) -> bool:
        """Override to implement load logic."""
        return True
    
    def _on_unload(self) -> None:
        """Override to implement unload logic."""
        pass
    
    def _on_activate(self) -> bool:
        """Override to implement activation logic."""
        return True
    
    def _on_deactivate(self) -> None:
        """Override to implement deactivation logic."""
        pass