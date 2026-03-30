"""
AI Assistant Feature
===================
AI-powered code assistance with multi-provider support.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum, auto
import time

from PyQt6.QtCore import QObject, pyqtSignal, QThread

from features.ai_assistant.provider import (
    OllamaProvider, 
    OpenAIProvider, 
    ProviderType,
    AIProviderFactory,
    AIResponse
)


class MessageRole(Enum):
    """Chat message roles."""
    USER = auto()
    ASSISTANT = auto()
    SYSTEM = auto()


@dataclass
class AIChatMessage:
    """Represents a chat message."""
    role: MessageRole
    content: str
    timestamp: float = 0.0


class AIAssistantSignals(QObject):
    """Signals for AI assistant events."""
    response_ready = pyqtSignal(str)
    response_error = pyqtSignal(str)
    thinking_started = pyqtSignal()
    thinking_stopped = pyqtSignal()


class AIWorker(QThread):
    """Worker thread for async AI requests."""
    
    def __init__(
        self,
        provider: QObject,
        messages: List[Dict[str, str]],
        parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        
        self._provider = provider
        self._messages = messages
        self._response: Optional[AIResponse] = None
        self._error: Optional[str] = None
    
    def run(self) -> None:
        """Execute the request."""
        # Determine which method to call based on provider type
        if isinstance(self._provider, OllamaProvider):
            self._response = self._provider.chat(self._messages)
        elif isinstance(self._provider, OpenAIProvider):
            self._response = self._provider.chat(self._messages)
    
    @property
    def response(self) -> Optional[AIResponse]:
        """Get the response."""
        return self._response
    
    @property
    def error(self) -> Optional[str]:
        """Get the error message."""
        return self._error


class AIAssistant(QObject):
    """
    AI-powered code assistant with multi-provider support.
    """
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        
        self._signals = AIAssistantSignals()
        self._messages: List[AIChatMessage] = []
        self._system_prompt: str = "Eres un asistente de programación útil."
        self._is_thinking: bool = False
        
        # Provider configuration
        self._provider_type: ProviderType = ProviderType.OLLAMA
        self._provider: QObject = AIProviderFactory.create_provider(ProviderType.OLLAMA)
        
        # Ollama defaults
        self._ollama_url: str = "http://localhost:11434"
        self._ollama_model: str = "llama3.2"
        
        # OpenAI defaults
        self._openai_api_key: str = ""
        self._openai_model: str = "gpt-3.5-turbo"
        
        # Generation settings
        self._temperature: float = 0.7
        self._max_tokens: int = 4096
        
        # Worker thread
        self._worker: Optional[AIWorker] = None
        
        # Configure provider
        self._configure_provider()
    
    @property
    def signals(self) -> AIAssistantSignals:
        """Get the signal hub."""
        return self._signals
    
    @property
    def messages(self) -> List[AIChatMessage]:
        """Get chat messages."""
        return self._messages
    
    @property
    def is_thinking(self) -> bool:
        """Check if the AI is thinking."""
        return self._is_thinking
    
    @property
    def provider_type(self) -> ProviderType:
        """Get current provider type."""
        return self._provider_type
    
    def _configure_provider(self) -> None:
        """Configure the current provider based on settings."""
        if self._provider_type == ProviderType.OLLAMA:
            if isinstance(self._provider, OllamaProvider):
                self._provider.base_url = self._ollama_url
                self._provider.model = self._ollama_model
        elif self._provider_type == ProviderType.OPENAI:
            if isinstance(self._provider, OpenAIProvider):
                self._provider.api_key = self._openai_api_key
                self._provider.model = self._openai_model
    
    def set_provider_type(self, provider_type: ProviderType) -> None:
        """Change the provider type."""
        if provider_type != self._provider_type:
            self._provider_type = provider_type
            self._provider = AIProviderFactory.create_provider(provider_type)
            self._configure_provider()
    
    def set_ollama_config(self, url: str, model: str) -> None:
        """Configure Ollama provider."""
        self._ollama_url = url
        self._ollama_model = model
        if self._provider_type == ProviderType.OLLAMA:
            self._configure_provider()
    
    def set_openai_config(self, api_key: str, model: str) -> None:
        """Configure OpenAI provider."""
        self._openai_api_key = api_key
        self._openai_model = model
        if self._provider_type == ProviderType.OPENAI:
            self._configure_provider()
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt."""
        self._system_prompt = prompt
    
    def set_generation_params(self, temperature: float, max_tokens: int) -> None:
        """Set generation parameters."""
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    def is_provider_available(self) -> bool:
        """Check if the current provider is available."""
        if self._provider_type == ProviderType.OLLAMA:
            if isinstance(self._provider, OllamaProvider):
                return self._provider.is_available()
        elif self._provider_type == ProviderType.OPENAI:
            if isinstance(self._provider, OpenAIProvider):
                return self._provider.is_available()
        return False
    
    def get_available_models(self) -> List[str]:
        """Get available models for the current provider."""
        if self._provider_type == ProviderType.OLLAMA:
            if isinstance(self._provider, OllamaProvider):
                return self._provider.list_models()
        return []
    
    def add_message(self, role: MessageRole, content: str) -> None:
        """Add a message to the conversation."""
        message = AIChatMessage(role=role, content=content, timestamp=time.time())
        self._messages.append(message)
    
    def clear_messages(self) -> None:
        """Clear all messages."""
        self._messages.clear()
    
    def ask(self, question: str, callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Ask the AI a question asynchronously.
        
        Args:
            question: The question to ask
            callback: Optional callback for the response
        """
        if self._is_thinking:
            return
        
        # Add user message
        self.add_message(MessageRole.USER, question)
        
        # Start thinking
        self._is_thinking = True
        self._signals.thinking_started.emit()
        
        # Build messages for API
        messages = []
        
        # Add system prompt
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        
        # Add conversation history
        for msg in self._messages:
            if msg.role == MessageRole.SYSTEM:
                messages.append({"role": "system", "content": msg.content})
            elif msg.role == MessageRole.USER:
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                messages.append({"role": "assistant", "content": msg.content})
        
        # Create worker thread
        self._worker = AIWorker(self._provider, messages)
        self._worker.finished.connect(lambda: self._on_response_ready(callback))
        self._worker.start()
    
    def _on_response_ready(self, callback: Optional[Callable[[str], None]]) -> None:
        """Handle response from worker thread."""
        if self._worker is None:
            return
        
        response = self._worker.response
        
        # Stop thinking
        self._is_thinking = False
        self._signals.thinking_stopped.emit()
        
        if response:
            # Add assistant response
            self.add_message(MessageRole.ASSISTANT, response.content)
            
            # Emit signals
            self._signals.response_ready.emit(response.content)
            
            if callback:
                callback(response.content)
        else:
            error_msg = "Failed to get response from AI"
            self._signals.response_error.emit(error_msg)
            
            if callback:
                callback(error_msg)
        
        self._worker = None
    
    def ask_sync(self, question: str) -> Optional[str]:
        """
        Ask the AI a question synchronously.
        
        Args:
            question: The question to ask
            
        Returns:
            The response or None on error
        """
        # Add user message
        self.add_message(MessageRole.USER, question)
        
        # Start thinking
        self._is_thinking = True
        self._signals.thinking_started.emit()
        
        # Build messages for API
        messages = []
        
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        
        for msg in self._messages:
            if msg.role == MessageRole.SYSTEM:
                messages.append({"role": "system", "content": msg.content})
            elif msg.role == MessageRole.USER:
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                messages.append({"role": "assistant", "content": msg.content})
        
        # Call provider directly
        if self._provider_type == ProviderType.OLLAMA:
            response = self._provider.chat(messages)
        elif self._provider_type == ProviderType.OPENAI:
            response = self._provider.chat(
                messages, 
                temperature=self._temperature,
                max_tokens=self._max_tokens
            )
        else:
            response = None
        
        # Stop thinking
        self._is_thinking = False
        self._signals.thinking_stopped.emit()
        
        if response:
            self.add_message(MessageRole.ASSISTANT, response.content)
            self._signals.response_ready.emit(response.content)
            return response.content
        
        self._signals.response_error.emit("Failed to get response")
        return None
    
    def analyze_code(self, code: str) -> str:
        """
        Analyze code and provide suggestions.
        
        Args:
            code: The code to analyze
            
        Returns:
            Analysis results
        """
        prompt = f"""Analiza el siguiente código y proporciona sugerencias de mejora:

```{code}
```

Proporciona:
1. Problemas potenciales (bugs, code smells)
2. Sugerencias de mejora
3. Estilo y mejores prácticas
4. Optimizaciones posibles"""

        return self.ask_sync(prompt) or "Error analyzing code"
    
    def complete_code(self, code: str, cursor_position: int) -> Optional[str]:
        """
        Provide code completion suggestions.
        
        Args:
            code: Current code
            cursor_position: Cursor position
            
        Returns:
            Completion suggestion
        """
        # Get current line context
        lines = code[:cursor_position].split('\n')
        if not lines:
            return None
        
        current_line = lines[-1]
        
        prompt = f"""Completa el siguiente código de Python. Solo devuelve la завершение(s) más probable(s) en una línea:

Código actual: {current_line}"""

        return self.ask_sync(prompt)
    
    def explain_error(self, error_message: str, code_context: str) -> str:
        """
        Explain an error message.
        
        Args:
            error_message: The error message
            code_context: The code that caused the error
            
        Returns:
            Explanation
        """
        prompt = f"""Explica el siguiente error de Python y cómo corregirlo:

Error: {error_message}

Código:
{code_context}

Proporciona:
1. Causa del error
2. Explicación clara
3. Código corregido
4. Cómo evitarlo en el futuro"""

        return self.ask_sync(prompt) or "Error explaining message"
    
    def refactor_code(self, code: str, style: str = "pythonic") -> str:
        """
        Refactor code.
        
        Args:
            code: The code to refactor
            style: Refactoring style preference
            
        Returns:
            Refactored code with explanation
        """
        prompt = f"""Refactoriza el siguiente código para hacerlo más eficiente y limpio (estilo: {style}):

{code}

Proporciona:
1. Código refactorizado
2. Explicación de los cambios
3. Beneficios de la refactorización"""

        return self.ask_sync(prompt) or "Error refactoring code"