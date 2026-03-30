"""
Test: AI Assistant
===================
Tests for features/ai_assistant/__init__.py and provider.py
"""

import unittest
from unittest.mock import Mock, patch, MagicMock


class TestMessageRole(unittest.TestCase):
    """Test MessageRole enum."""
    
    def test_roles_defined(self):
        """Test all message roles are defined."""
        from features.ai_assistant import MessageRole
        
        self.assertIsNotNone(MessageRole.USER)
        self.assertIsNotNone(MessageRole.ASSISTANT)
        self.assertIsNotNone(MessageRole.SYSTEM)


class TestAIChatMessage(unittest.TestCase):
    """Test AIChatMessage dataclass."""
    
    def test_creation(self):
        """Test creating an AIChatMessage."""
        from features.ai_assistant import AIChatMessage, MessageRole
        
        msg = AIChatMessage(
            role=MessageRole.USER,
            content="Hello, world!",
            timestamp=1234567890.0
        )
        
        self.assertEqual(msg.role, MessageRole.USER)
        self.assertEqual(msg.content, "Hello, world!")
        self.assertEqual(msg.timestamp, 1234567890.0)
    
    def test_default_timestamp(self):
        """Test default timestamp value."""
        from features.ai_assistant import AIChatMessage, MessageRole
        
        msg = AIChatMessage(role=MessageRole.USER, content="Test")
        
        # Timestamp should be set (won't be 0.0 if time is called)
        self.assertGreaterEqual(msg.timestamp, 0.0)


class TestAIAssistant(unittest.TestCase):
    """Test AIAssistant class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from features.ai_assistant import AIAssistant
        self.assistant = AIAssistant()
    
    def test_initialization(self):
        """Test assistant initializes correctly."""
        self.assertEqual(len(self.assistant.messages), 0)
        self.assertEqual(self.assistant._system_prompt, "Eres un asistente de programación útil.")
        self.assertFalse(self.assistant.is_thinking)
    
    def test_set_system_prompt(self):
        """Test setting system prompt."""
        self.assistant.set_system_prompt("You are a Python expert.")
        self.assertEqual(self.assistant._system_prompt, "You are a Python expert.")
    
    def test_add_message(self):
        """Test adding messages."""
        from features.ai_assistant import MessageRole
        
        self.assistant.add_message(MessageRole.USER, "Test message")
        
        self.assertEqual(len(self.assistant.messages), 1)
        self.assertEqual(self.assistant.messages[0].content, "Test message")
    
    def test_clear_messages(self):
        """Test clearing messages."""
        from features.ai_assistant import MessageRole
        
        self.assistant.add_message(MessageRole.USER, "Test")
        self.assistant.clear_messages()
        
        self.assertEqual(len(self.assistant.messages), 0)
    
    def test_set_generation_params(self):
        """Test setting generation parameters."""
        self.assistant.set_generation_params(0.5, 2048)
        
        self.assertEqual(self.assistant._temperature, 0.5)
        self.assertEqual(self.assistant._max_tokens, 2048)
    
    def test_signals_exist(self):
        """Test assistant has required signals."""
        from features.ai_assistant import AIAssistantSignals
        self.assertIsInstance(self.assistant.signals, AIAssistantSignals)


class TestProviderTypes(unittest.TestCase):
    """Test ProviderType enum."""
    
    def test_provider_types_defined(self):
        """Test all provider types are defined."""
        from features.ai_assistant.provider import ProviderType
        
        self.assertIsNotNone(ProviderType.OLLAMA)
        self.assertIsNotNone(ProviderType.OPENAI)
        self.assertIsNotNone(ProviderType.ANTHROPIC)


class TestOllamaProvider(unittest.TestCase):
    """Test OllamaProvider class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from features.ai_assistant.provider import OllamaProvider
        self.provider = OllamaProvider()
    
    def test_initialization(self):
        """Test provider initializes with defaults."""
        self.assertEqual(self.provider.base_url, "http://localhost:11434")
        self.assertEqual(self.provider.model, "llama3.2")
        self.assertEqual(self.provider.timeout, 120)
    
    def test_set_base_url(self):
        """Test setting base URL."""
        self.provider.base_url = "http://192.168.1.100:11434"
        self.assertEqual(self.provider.base_url, "http://192.168.1.100:11434")
    
    def test_set_model(self):
        """Test setting model."""
        self.provider.model = "codellama"
        self.assertEqual(self.provider.model, "codellama")
    
    def test_set_timeout(self):
        """Test setting timeout."""
        self.provider.timeout = 60
        self.assertEqual(self.provider.timeout, 60)
    
    def test_signals_exist(self):
        """Test provider has required signals."""
        from features.ai_assistant.provider import ProviderSignals
        self.assertIsInstance(self.provider.signals, ProviderSignals)


class TestAIProviderFactory(unittest.TestCase):
    """Test AIProviderFactory."""
    
    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        from features.ai_assistant.provider import (
            AIProviderFactory, ProviderType, OllamaProvider
        )
        
        provider = AIProviderFactory.create_provider(ProviderType.OLLAMA)
        self.assertIsInstance(provider, OllamaProvider)
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        from features.ai_assistant.provider import (
            AIProviderFactory, ProviderType, OpenAIProvider
        )
        
        provider = AIProviderFactory.create_provider(ProviderType.OPENAI)
        self.assertIsInstance(provider, OpenAIProvider)
    
    def test_invalid_provider_raises(self):
        """Test invalid provider type raises error."""
        from features.ai_assistant.provider import AIProviderFactory
        
        class InvalidType:
            pass
        
        with self.assertRaises(ValueError):
            AIProviderFactory.create_provider(InvalidType())


class TestAIResponse(unittest.TestCase):
    """Test AIResponse dataclass."""
    
    def test_creation(self):
        """Test creating an AIResponse."""
        from features.ai_assistant.provider import AIResponse
        
        response = AIResponse(
            content="Test response",
            model="llama3.2",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )
        
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.model, "llama3.2")
        self.assertEqual(response.finish_reason, "stop")
        self.assertEqual(response.usage["prompt_tokens"], 10)


class TestAIRequest(unittest.TestCase):
    """Test AIRequest dataclass."""
    
    def test_creation(self):
        """Test creating an AIRequest."""
        from features.ai_assistant.provider import AIRequest
        
        request = AIRequest(
            model="llama3.2",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=4096,
            stream=False
        )
        
        self.assertEqual(request.model, "llama3.2")
        self.assertEqual(len(request.messages), 1)
        self.assertEqual(request.temperature, 0.7)
        self.assertEqual(request.max_tokens, 4096)
        self.assertFalse(request.stream)


if __name__ == '__main__':
    unittest.main()