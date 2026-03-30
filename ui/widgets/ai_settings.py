"""
AI Settings Widget
==================
Widget for configuring AI assistant settings.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QDialogButtonBox,
    QGroupBox, QLineEdit, QPushButton, QCheckBox, QComboBox, QTextEdit,
    QMessageBox, QSplitter, QApplication
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


# Supported AI Providers
AI_PROVIDERS = {
    "OpenAI": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
        "free": False
    },
    "Ollama": {
        "models": ["llama3.2", "llama3.1", "mistral", "codellama", "phi3", "qwen2", "deepseek-coder"],
        "api_key_env": None,
        "default_model": "llama3.2",
        "free": True,
        "local": True,
        "base_url": "http://localhost:11434"
    },
    "LM Studio": {
        "models": ["*local models*"],
        "api_key_env": None,
        "default_model": "",
        "free": True,
        "local": True,
        "base_url": "http://localhost:1234/v1"
    },
    "KoboldCPP": {
        "models": ["*local models*"],
        "api_key_env": None,
        "default_model": "",
        "free": True,
        "local": True,
        "base_url": "http://localhost:5001"
    },
    "Hugging Face": {
        "models": ["microsoft/Phi-3-mini-128k-instruct", "Qwen/Qwen2-7B-Instruct", "meta-llama/Meta-Llama-3-8B-Instruct"],
        "api_key_env": "HF_TOKEN",
        "default_model": "microsoft/Phi-3-mini-128k-instruct",
        "free": True,
        "base_url": "https://api-inference.huggingface.co"
    },
    "Together AI": {
        "models": ["meta-llama/Llama-3.2-90B-Instruct-Turbo", "Qwen/Qwen2-72B-Instruct", "mistralai/Mixtral-8x22B-Instruct-v0.1"],
        "api_key_env": "TOGETHER_API_KEY",
        "default_model": "meta-llama/Llama-3.2-90B-Instruct-Turbo",
        "free": False
    },
    "OAI Compatible": {
        "models": ["*custom*"],
        "api_key_env": None,
        "default_model": "",
        "free": False,
        "base_url": "https://api.openai.com/v1"
    }
}


class AISettingsWidget(QWidget):
    """
    Widget for configuring AI settings.
    """
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._settings: Dict = {}
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Enable AI checkbox
        self._enable_ai_check = QCheckBox("Activar Asistente IA")
        self._enable_ai_check.stateChanged.connect(self._on_enable_changed)
        main_layout.addWidget(self._enable_ai_check)
        
        # Content splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Provider selection
        left_group = QGroupBox("Proveedor de IA")
        left_layout = QVBoxLayout(left_group)
        
        # Provider combo
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Proveedor:"))
        self._provider_combo = QComboBox()
        for provider in AI_PROVIDERS:
            provider_info = AI_PROVIDERS[provider]
            label = f"{provider} {'(Local)' if provider_info.get('local') else '⭐' if provider_info.get('free') else '💰'}"
            self._provider_combo.addItem(label, provider)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self._provider_combo)
        left_layout.addLayout(provider_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Modelo:"))
        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        # Make the combo box taller to better display long model names
        self._model_combo.setMinimumHeight(35)
        self._model_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                min-height: 150px;
                font-size: 11px;
            }
        """)
        model_layout.addWidget(self._model_combo)
        left_layout.addLayout(model_layout)
        
        # Custom model hint
        self._custom_model_label = QLabel("Escribe el nombre del modelo personalizado")
        self._custom_model_label.setStyleSheet("color: gray; font-size: 10px;")
        left_layout.addWidget(self._custom_model_label)
        
        # Test connection button
        self._test_btn = QPushButton("🔗 Probar Conexión")
        self._test_btn.clicked.connect(self._test_connection)
        left_layout.addWidget(self._test_btn)
        
        # Connection status
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self._status_label)
        
        left_layout.addStretch()
        content_splitter.addWidget(left_group)
        
        # Right panel - Configuration
        right_group = QGroupBox("Configuración")
        right_layout = QVBoxLayout(right_group)
        
        # API Key
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("API Key:"))
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setPlaceholderText("Tu API key (opcional para locales)")
        api_key_layout.addWidget(self._api_key_edit)
        right_layout.addLayout(api_key_layout)
        
        # Base URL (for custom endpoints)
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL Base:"))
        self._base_url_edit = QLineEdit()
        self._base_url_edit.setPlaceholderText("http://localhost:11434")
        url_layout.addWidget(self._base_url_edit)
        right_layout.addLayout(url_layout)
        
        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperatura:"))
        self._temperature_edit = QLineEdit()
        self._temperature_edit.setText("0.7")
        self._temperature_edit.setMaximumWidth(60)
        temp_layout.addWidget(self._temperature_edit)
        temp_layout.addWidget(QLabel("(0.0 - 1.0)"))
        temp_layout.addStretch()
        right_layout.addLayout(temp_layout)
        
        # Max tokens
        tokens_layout = QHBoxLayout()
        tokens_layout.addWidget(QLabel("Máx Tokens:"))
        self._max_tokens_edit = QLineEdit()
        self._max_tokens_edit.setText("4096")
        self._max_tokens_edit.setMaximumWidth(80)
        tokens_layout.addWidget(self._max_tokens_edit)
        tokens_layout.addStretch()
        right_layout.addLayout(tokens_layout)
        
        # System prompt
        prompt_label = QLabel("Prompt del Sistema:")
        right_layout.addWidget(prompt_label)
        
        self._system_prompt_edit = QTextEdit()
        self._system_prompt_edit.setPlaceholderText("Eres un asistente de programación útil...")
        self._system_prompt_edit.setMaximumHeight(100)
        right_layout.addWidget(self._system_prompt_edit)
        
        right_layout.addStretch()
        content_splitter.addWidget(right_group)
        
        # Set sizes
        content_splitter.setSizes([350, 450])
        
        main_layout.addWidget(content_splitter)
        
        # Save button
        self._save_btn = QPushButton("💾 Guardar Configuración")
        self._save_btn.clicked.connect(self._save_settings)
        main_layout.addWidget(self._save_btn)
    
    def _on_provider_changed(self, index: int) -> None:
        """Handle provider change."""
        import sys
        
        provider = self._provider_combo.currentData()
        
        # Special handling for Hugging Face - load available models
        if provider == "Hugging Face":
            self._load_huggingface_models()
            return
        
        if provider in AI_PROVIDERS:
            provider_info = AI_PROVIDERS[provider]
            
            # Update model combo
            self._model_combo.clear()
            models = provider_info.get("models", [])
            for model in models:
                self._model_combo.addItem(model, model)
            
            # Set default
            default = provider_info.get("default_model", "")
            if default:
                idx = self._model_combo.findData(default)
                if idx >= 0:
                    self._model_combo.setCurrentIndex(idx)
            
            # Update base URL
            if provider_info.get("local"):
                self._base_url_edit.setText(provider_info.get("base_url", ""))
                self._base_url_edit.setEnabled(True)
            else:
                self._base_url_edit.setText("")
                self._base_url_edit.setEnabled(False)
            
            # Update custom model hint visibility
            self._custom_model_label.setVisible("*" in models)
    
    def _load_huggingface_models(self) -> None:
        """Load available Hugging Face models."""
        import sys
        
        self._model_combo.clear()
        self._model_combo.addItem("Cargando modelos...", "")
        QApplication.processEvents()
        
        try:
            from huggingface_hub import HfApi
            
            print("[DEBUG] Cargando modelos de Hugging Face...", file=sys.stderr)
            api = HfApi()
            
            # Get models using inference provider for free models
            modelos_generator = api.list_models(
                inference_provider="hf-inference",
                limit=50
            )
            
            # Convert generator to list
            modelos = list(modelos_generator)
            
            print(f"[DEBUG] Obtenidos {len(modelos)} modelos", file=sys.stderr)
            
            # Filter for code-related models
            code_keywords = [
                "code", "coder", "starcoder", "codellama", "CodeLlama",
                "coder-instruct", "phi", "deepseek-coder", "qwen-coder"
            ]
            code_models = []
            other_models = []
            
            for m in modelos:
                model_id = m.id.lower()
                pipeline_tag = getattr(m, 'pipeline_tag', 'other')
                if any(kw in model_id for kw in code_keywords):
                    code_models.append(m.id)
                elif len(other_models) < 30:  # Limit non-code models
                    other_models.append(m.id)
            
            # Add code models first
            for m in code_models:
                self._model_combo.addItem(f"[Código] {m}", m)
            
            # Add other models
            for m in other_models:
                self._model_combo.addItem(m, m)
            
            if self._model_combo.count() > 0:
                self._status_label.setText(f"✓ {self._model_combo.count()} modelos cargados")
                self._status_label.setStyleSheet("font-weight: bold; color: green;")
            else:
                self._status_label.setText("⚠ No hay modelos disponibles")
                self._status_label.setStyleSheet("font-weight: bold; color: orange;")
                
        except ImportError:
            self._model_combo.clear()
            # Fallback to static models if library not available
            fallback_models = [
                "meta-llama/CodeLlama-7b-hf",
                "bigcode/starcoder-7b",
                "microsoft/phi-2",
                "Qwen/Qwen2.5-Coder-7B-Instruct"
            ]
            for m in fallback_models:
                self._model_combo.addItem(f"[Código] {m}", m)
            self._status_label.setText("⚠ huggingface_hub no instalado, usando modelos por defecto")
            self._status_label.setStyleSheet("font-weight: bold; color: orange;")
        except Exception as e:
            print(f"[DEBUG] Error cargando modelos HF: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self._model_combo.clear()
            # Fallback to static models
            fallback_models = [
                "meta-llama/CodeLlama-7b-hf",
                "bigcode/starcoder-7b",
                "microsoft/phi-2",
                "Qwen/Qwen2.5-Coder-7B-Instruct"
            ]
            for m in fallback_models:
                self._model_combo.addItem(f"[Código] {m}", m)
            self._status_label.setText(f"⚠ Error: {str(e)[:50]}")
            self._status_label.setStyleSheet("font-weight: bold; color: orange;")
        
        # Base URL for Hugging Face
        self._base_url_edit.setText("https://api-inference.huggingface.co")
        self._base_url_edit.setEnabled(False)
    
    def _on_enable_changed(self, state: int) -> None:
        """Handle enable checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self._provider_combo.setEnabled(enabled)
        self._model_combo.setEnabled(enabled)
        self._api_key_edit.setEnabled(enabled)
        self._base_url_edit.setEnabled(enabled)
        self._temperature_edit.setEnabled(enabled)
        self._max_tokens_edit.setEnabled(enabled)
        self._system_prompt_edit.setEnabled(enabled)
        self._save_btn.setEnabled(enabled)
        self._test_btn.setEnabled(enabled)
    
    def _test_connection(self) -> None:
        """Test connection to the AI provider."""
        provider = self._provider_combo.currentData()
        model = self._model_combo.currentText()
        api_key = self._api_key_edit.text().strip()
        base_url = self._base_url_edit.text().strip()
        
        self._status_label.setText("Probando...")
        self._status_label.setStyleSheet("font-weight: bold; color: blue;")
        
        # Simple test - try to make a request
        try:
            if provider == "Ollama":
                import requests
                response = requests.get(f"{base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    self._status_label.setText("✓ Conexión exitosa!")
                    self._status_label.setStyleSheet("font-weight: bold; color: green;")
                else:
                    self._status_label.setText(f"Error: {response.status_code}")
                    self._status_label.setStyleSheet("font-weight: bold; color: red;")
            
            elif provider == "LM Studio" or provider == "OAI Compatible":
                import requests
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                response = requests.get(f"{base_url}/models", headers=headers, timeout=5)
                if response.status_code == 200:
                    self._status_label.setText("✓ Conexión exitosa!")
                    self._status_label.setStyleSheet("font-weight: bold; color: green;")
                else:
                    self._status_label.setText(f"Error: {response.status_code}")
                    self._status_label.setStyleSheet("font-weight: bold; color: red;")
            
            elif provider == "OpenAI":
                # For API providers, just check if we have the key
                if api_key:
                    self._status_label.setText("✓ Configuración válida (API Key presente)")
                    self._status_label.setStyleSheet("font-weight: bold; color: green;")
                else:
                    self._status_label.setText("⚠ Falta API Key")
                    self._status_label.setStyleSheet("font-weight: bold; color: orange;")
            
            elif provider == "Hugging Face":
                import sys
                try:
                    from huggingface_hub import HfApi
                    
                    print("[DEBUG HF Settings] Iniciando API...", file=sys.stderr)
                    api = HfApi()
                    
                    # Get models using inference provider for free models
                    modelos_generator = api.list_models(
                        inference_provider="hf-inference",
                        limit=50
                    )
                    
                    # Convert generator to list
                    modelos = list(modelos_generator)
                    
                    print(f"[DEBUG HF Settings] Tipo de modelos: {type(modelos)}", file=sys.stderr)
                    print(f"[DEBUG HF Settings] Cantidad de modelos: {len(modelos)}", file=sys.stderr)
                    
                    # Filter code models
                    codigo_keywords = [
                        "code", "coder", "starcoder", "codellama", "CodeLlama",
                        "coder-instruct", "phi", "deepseek-coder", "qwen-coder"
                    ]
                    code_models = []
                    other_models = []
                    
                    for m in modelos:
                        model_id = str(m.id).lower()
                        pipeline_tag = getattr(m, 'pipeline_tag', 'other')
                        if any(kw in model_id for kw in codigo_keywords):
                            code_models.append(m.id)
                        elif len(other_models) < 30:
                            other_models.append(m.id)
                    
                    print(f"[DEBUG HF Settings] Modelos de código encontrados: {len(code_models)}", file=sys.stderr)
                    
                    total_models = len(code_models) + len(other_models)
                    if total_models > 0:
                        msg = f"✓ {total_models} modelos disponibles"
                        if code_models:
                            msg += f" ({len(code_models)} para código)"
                        self._status_label.setText(msg)
                        self._status_label.setStyleSheet("font-weight: bold; color: green;")
                        
                        # Update model combo with available models
                        self._model_combo.clear()
                        # Add code models first
                        for m in code_models[:10]:
                            self._model_combo.addItem(f"[Código] {m}", m)
                        # Add general models
                        for m in other_models[:15]:
                            if str(m) not in code_models:
                                self._model_combo.addItem(str(m), str(m))
                    else:
                        self._status_label.setText("⚠ No hay modelos disponibles")
                        self._status_label.setStyleSheet("font-weight: bold; color: orange;")
                        
                except ImportError as ie:
                    print(f"[DEBUG HF Settings] ImportError: {ie}", file=sys.stderr)
                    # Fallback to simple connectivity test
                    import requests
                    headers = {}
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"
                    try:
                        response = requests.get("https://api-inference.huggingface.co", headers=headers, timeout=5)
                        self._status_label.setText("✓ Conexión exitosa (huggingface_hub no instalado)")
                        self._status_label.setStyleSheet("font-weight: bold; color: green;")
                    except Exception as e:
                        self._status_label.setText(f"Error: {str(e)}")
                        self._status_label.setStyleSheet("font-weight: bold; color: red;")
                except Exception as e:
                    print(f"[DEBUG HF Settings] Error: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    self._status_label.setText(f"Error: {str(e)}")
                    self._status_label.setStyleSheet("font-weight: bold; color: red;")
            
            elif provider == "Together AI":
                import requests
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get("https://api.together.ai/v1/models", headers=headers, timeout=10)
                if response.status_code == 200:
                    models_data = response.json()
                    all_models = models_data.get("data", [])
                    
                    # Filter for code models
                    code_models = [m for m in all_models if any(kw in m.get("id", "").lower() for kw in ["code", "coder", "llama", "mistral", "qwen", "deepseek"])]
                    
                    if all_models:
                        msg = f"✓ {len(all_models)} modelos disponibles"
                        if code_models:
                            msg += f" ({len(code_models)} relevantes)"
                        self._status_label.setText(msg)
                        self._status_label.setStyleSheet("font-weight: bold; color: green;")
                        
                        # Update model combo
                        self._model_combo.clear()
                        for m in code_models[:10]:
                            self._model_combo.addItem(m["id"], m["id"])
                        for m in all_models[:20]:
                            if m["id"] not in [x["id"] for x in code_models[:10]]:
                                self._model_combo.addItem(m["id"], m["id"])
                    else:
                        self._status_label.setText("⚠ No hay modelos disponibles")
                        self._status_label.setStyleSheet("font-weight: bold; color: orange;")
                else:
                    self._status_label.setText(f"Error: {response.status_code}")
                    self._status_label.setStyleSheet("font-weight: bold; color: red;")
            
            else:
                self._status_label.setText("Probando...")
                # Generic test
                self._status_label.setText("✓ Configuración guardada. Prueba en el editor.")
                self._status_label.setStyleSheet("font-weight: bold; color: green;")
                
        except ImportError as e:
            if provider == "Hugging Face":
                self._status_label.setText("⚠ huggingface_hub no disponible")
                self._status_label.setStyleSheet("font-weight: bold; color: orange;")
            else:
                self._status_label.setText("⚠ requests no disponible")
                self._status_label.setStyleSheet("font-weight: bold; color: orange;")
        except Exception as e:
            self._status_label.setText(f"Error: {str(e)[:30]}")
            self._status_label.setStyleSheet("font-weight: bold; color: red;")
    
    def _load_settings(self) -> None:
        """Load settings from config."""
        try:
            from core.utils.config import ConfigManager
            config = ConfigManager().load()
            if config:
                ai_config = config.get_ai_config() if hasattr(config, 'get_ai_config') else {}
                
                self._settings = ai_config
                
                # Apply settings
                self._enable_ai_check.setChecked(ai_config.get("enabled", True))
                
                # Provider - handle both predefined and custom providers
                provider = ai_config.get("provider", "Ollama")
                idx = self._provider_combo.findData(provider)
                if idx >= 0:
                    self._provider_combo.setCurrentIndex(idx)
                else:
                    # Add custom provider if not in list
                    self._provider_combo.addItem(provider, provider)
                    self._provider_combo.setCurrentIndex(self._provider_combo.count() - 1)
                
                # Model - handle both predefined and custom models
                model = ai_config.get("model", "")
                if model:
                    idx = self._model_combo.findText(model)
                    if idx >= 0:
                        self._model_combo.setCurrentIndex(idx)
                    else:
                        # Add custom model if not in list
                        self._model_combo.addItem(model)
                        self._model_combo.setCurrentIndex(self._model_combo.count() - 1)
                
                # API Key
                self._api_key_edit.setText(ai_config.get("api_key", ""))
                
                # Base URL
                self._base_url_edit.setText(ai_config.get("base_url", ""))
                
                # Other settings
                self._temperature_edit.setText(str(ai_config.get("temperature", 0.7)))
                self._max_tokens_edit.setText(str(ai_config.get("max_tokens", 4096)))
                self._system_prompt_edit.setPlainText(ai_config.get("system_prompt", ""))
        except Exception as e:
            print(f"Error loading AI settings: {e}")
    
    def _save_settings(self) -> None:
        """Save settings to config."""
        provider = self._provider_combo.currentData()
        
        settings = {
            "enabled": self._enable_ai_check.isChecked(),
            "provider": provider,
            "model": self._model_combo.currentText(),
            "api_key": self._api_key_edit.text().strip(),
            "base_url": self._base_url_edit.text().strip(),
            "temperature": float(self._temperature_edit.text() or 0.7),
            "max_tokens": int(self._max_tokens_edit.text() or 4096),
            "system_prompt": self._system_prompt_edit.toPlainText()
        }
        
        try:
            from core.utils.config import ConfigManager
            config = ConfigManager().load()
            if config:
                # Save to config
                if hasattr(config, 'set_ai_config'):
                    config.set_ai_config(settings)
                else:
                    # Store as dict
                    config._ai_config = settings
                
                ConfigManager().save(config)
                
                self._settings = settings
                self.settings_changed.emit(settings)
        except Exception as e:
            print(f"Error saving AI settings: {e}")
    
    def get_settings(self) -> Dict:
        """Get current settings."""
        return self._settings.copy()


class AISettingsDialog(QDialog):
    """
    Dialog for AI settings.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configuración de IA")
        self.setMinimumSize(850, 650)
        
        layout = QVBoxLayout(self)
        
        self._widget = AISettingsWidget(self)
        layout.addWidget(self._widget)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close | QDialogButtonBox.StandardButton.Apply)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self._widget._save_settings)
        
        # Connect Apply button explicitly
        apply_button = buttons.button(QDialogButtonBox.StandardButton.Apply)
        if apply_button:
            apply_button.clicked.connect(self._widget._save_settings)
            
        layout.addWidget(buttons)
    
