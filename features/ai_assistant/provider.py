"""
AI Provider Module
=================
Handles connection to AI providers (Ollama, OpenAI, etc.).
"""

import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal


class ProviderType(Enum):
    """AI provider types."""
    OLLAMA = auto()
    OPENAI = auto()
    ANTHROPIC = auto()


@dataclass
class AIRequest:
    """Represents an AI API request."""
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False


@dataclass
class AIResponse:
    """Represents an AI API response."""
    content: str
    model: str
    finish_reason: str = "stop"
    usage: Dict[str, int] = None


class ProviderSignals(QObject):
    """Signals for provider events."""
    response_received = pyqtSignal(object)  # AIResponse
    error_occurred = pyqtSignal(str)
    streaming_chunk = pyqtSignal(str)


class OllamaProvider(QObject):
    """
    Ollama provider implementation.
    Connects to local Ollama server for AI interactions.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = ProviderSignals()
        self._base_url: str = "http://localhost:11434"
        self._model: str = "llama3.2"
        self._timeout: int = 120
    
    @property
    def signals(self) -> ProviderSignals:
        """Get provider signals."""
        return self._signals
    
    @property
    def base_url(self) -> str:
        """Get base URL."""
        return self._base_url
    
    @base_url.setter
    def base_url(self, url: str) -> None:
        """Set base URL."""
        self._base_url = url.rstrip('/')
    
    @property
    def model(self) -> str:
        """Get model name."""
        return self._model
    
    @model.setter
    def model(self, name: str) -> None:
        """Set model name."""
        self._model = name
    
    @property
    def timeout(self) -> int:
        """Get timeout in seconds."""
        return self._timeout
    
    @timeout.setter
    def timeout(self, seconds: int) -> None:
        """Set timeout."""
        self._timeout = seconds
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        import urllib.request
        import urllib.error
        
        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/tags",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """List available models."""
        import urllib.request
        import urllib.error
        
        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/tags",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return [m.get('name', '') for m in data.get('models', [])]
        except Exception:
            return []
    
    def generate(self, prompt: str, system: str = "") -> Optional[AIResponse]:
        """Generate a response using /api/generate endpoint."""
        import urllib.request
        import urllib.error
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.7,
            }
        }
        
        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/generate",
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                return AIResponse(
                    content=data.get('response', ''),
                    model=self._model,
                    finish_reason=data.get('done', True) and "stop" or "length"
                )
                
        except urllib.error.URLError as e:
            self._signals.error_occurred.emit(f"Connection error: {str(e)}")
        except Exception as e:
            self._signals.error_occurred.emit(f"Error: {str(e)}")
        
        return None
    
    def chat(self, messages: List[Dict[str, str]]) -> Optional[AIResponse]:
        """Generate a response using /api/chat endpoint."""
        import urllib.request
        import urllib.error
        
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
        }
        
        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/chat",
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                message = data.get('message', {})
                return AIResponse(
                    content=message.get('content', ''),
                    model=self._model,
                    finish_reason=data.get('done', True) and "stop" or "length"
                )
                
        except urllib.error.URLError as e:
            self._signals.error_occurred.emit(f"Connection error: {str(e)}")
        except Exception as e:
            self._signals.error_occurred.emit(f"Error: {str(e)}")
        
        return None


class OpenAIProvider(QObject):
    """
    OpenAI provider implementation.
    Connects to OpenAI API for AI interactions.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = ProviderSignals()
        self._api_key: str = ""
        self._model: str = "gpt-3.5-turbo"
        self._base_url: str = "https://api.openai.com/v1"
        self._timeout: int = 60
    
    @property
    def signals(self) -> ProviderSignals:
        """Get provider signals."""
        return self._signals
    
    @property
    def api_key(self) -> str:
        """Get API key."""
        return self._api_key
    
    @api_key.setter
    def api_key(self, key: str) -> None:
        """Set API key."""
        self._api_key = key
    
    @property
    def model(self) -> str:
        """Get model name."""
        return self._model
    
    @model.setter
    def model(self, name: str) -> None:
        """Set model name."""
        self._model = name
    
    def is_available(self) -> bool:
        """Check if API key is set."""
        return bool(self._api_key)
    
    def chat(self, messages: List[Dict[str, str]], 
             temperature: float = 0.7,
             max_tokens: int = 4096) -> Optional[AIResponse]:
        """Generate a response using OpenAI chat API."""
        import urllib.request
        import urllib.error
        
        if not self._api_key:
            self._signals.error_occurred.emit("API key not set")
            return None
        
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            req = urllib.request.Request(
                f"{self._base_url}/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                choice = data.get('choices', [{}])[0]
                message = choice.get('message', {})
                
                return AIResponse(
                    content=message.get('content', ''),
                    model=self._model,
                    finish_reason=choice.get('finish_reason', 'stop'),
                    usage=data.get('usage', {})
                )
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                msg = error_data.get('error', {}).get('message', str(e))
            except Exception:
                msg = str(e)
            self._signals.error_occurred.emit(f"API error: {msg}")
        except Exception as e:
            self._signals.error_occurred.emit(f"Error: {str(e)}")
        
        return None


class AIProviderFactory:
    """Factory for creating AI providers."""
    
    @staticmethod
    def create_provider(provider_type: ProviderType) -> QObject:
        """Create a provider instance."""
        if provider_type == ProviderType.OLLAMA:
            return OllamaProvider()
        elif provider_type == ProviderType.OPENAI:
            return OpenAIProvider()
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")