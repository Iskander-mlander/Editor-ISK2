"""
Internationalization Module
===========================
Translation and localization support.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List

from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class Translation:
    """Represents a translation."""
    locale: str
    name: str
    data: Dict[str, str]


class I18nSignals(QObject):
    """Signals for i18n events."""
    locale_changed = pyqtSignal(str)
    translation_loaded = pyqtSignal(str)


class I18n:
    """
    Internationalization support.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        # Create signals object with parent if provided
        if parent is not None:
            self._signals = I18nSignals(parent)
        else:
            self._signals = I18nSignals()
        
        self._translations: Dict[str, Translation] = {}
        self._current_locale: str = "en"
        self._fallback_locale: str = "en"
        self._parent = parent
    
    @property
    def signals(self) -> I18nSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def current_locale(self) -> str:
        """Get the current locale."""
        return self._current_locale
    
    def load_translation(self, locale: str, file_path: Path) -> bool:
        """
        Load a translation file.
        
        Args:
            locale: Locale code (e.g., "en", "es")
            file_path: Path to the translation file
            
        Returns:
            True if loaded successfully
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            name = data.get("name", locale)
            
            # Handle nested structure: {"name": "...", "translations": {"menu": {...}}}
            if "translations" in data:
                translation_data = data["translations"]
            else:
                # Handle flat structure
                translation_data = data
            
            translation = Translation(
                locale=locale,
                name=name,
                data=translation_data
            )
            
            self._translations[locale] = translation
            self._signals.translation_loaded.emit(locale)
            return True
            
        except Exception as e:
            print(f"Error loading translation: {e}")
            return False
    
    def set_locale(self, locale: str) -> bool:
        """Set the current locale."""
        if locale in self._translations:
            self._current_locale = locale
            self._signals.locale_changed.emit(locale)
            return True
        return False
    
    def translate(self, key: str, default: str = "") -> str:
        """
        Translate a key.
        
        Args:
            key: Translation key (supports nested like "menu.file")
            default: Default value if not found
            
        Returns:
            Translated string
        """
        parts = key.split('.')
        
        # Try current locale
        translation = self._translations.get(self._current_locale)
        if translation:
            result = self._get_nested_value(translation.data, parts)
            if result:
                return result
        
        # Try fallback locale
        if self._fallback_locale != self._current_locale:
            fallback = self._translations.get(self._fallback_locale)
            if fallback:
                result = self._get_nested_value(fallback.data, parts)
                if result:
                    return result
        
        return default or key
    
    def _get_nested_value(self, data: dict, keys: list) -> Optional[str]:
        """Get value from nested dictionary."""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current if isinstance(current, str) else None
    
    def get_available_locales(self) -> List[str]:
        """Get list of available locales."""
        return list(self._translations.keys())
    
    def add_translation(self, translation: Translation) -> None:
        """Add a translation programmatically."""
        self._translations[translation.locale] = translation