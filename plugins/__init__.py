"""
Plugins Package
================
Plugin system for extending editor functionality.
"""

from .base import Plugin, PluginMetadata
from .manager import PluginManager

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginManager",
]