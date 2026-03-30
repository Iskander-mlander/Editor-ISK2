"""
AI Panel Widget
==============
Panel for AI assistant chat and file operations.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
    QSplitter, QGroupBox, QLineEdit, QMessageBox, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QAction, QTextCursor


# Restricted commands that cannot be executed
BLOCKED_COMMANDS = [
    "rm -rf", "del /f /s /q", "mkfs", "dd if=",  # File destruction
    "shutdown", "reboot", "halt",  # System shutdown
    "curl http", "wget http", "nc ", "ncat",  # Network downloads
    ":(){ :|:& };:", "fork()",  # Fork bombs
    "chmod 777", "chown",  # Permission changes
    ">", "2>", ">>"  # Redirection to system files
]

# Project directory for security
PROJECT_ROOT = Path.cwd()  # Will be set dynamically

# Input validation constants
MIN_COMMAND_LENGTH = 1
MAX_COMMAND_LENGTH = 10000
MAX_ARGUMENTS = 20

# Dangerous patterns that bypass simple string matching
DANGEROUS_PATTERNS = [
    r"\$\([^)]+\)",  # Command substitution $(...)
    r"`[^`]+`",  # Backtick command substitution
    r"&&\s*rm",  # Chain with rm
    r"&&\s*del",  # Chain with del
    r";\s*rm\s",  # Semicolon rm
    r"\|\s*xargs",  # Pipe to xargs
    r"--no-[a-z-]+",  # Potential flag abuse
]

# AI Configuration - To be configured by user
AI_CONFIG = {
    "enabled": False,
    "endpoint": "",  # e.g., "http://localhost:11434/api/generate"
    "model": "llama2",  # Default model
    "api_key": "",  # Optional API key
    "timeout": 60,  # Request timeout in seconds
}


class AIInferenceThread(QThread):
    """Thread for running AI inference without blocking UI."""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, prompt: str, context: Dict, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.context = context
    
    def run(self):
        """Run AI inference."""
        import sys
        
        try:
            print("[DEBUG AI Thread] Iniciando inference...", file=sys.stderr)
            self.progress.emit("Iniciando inference...")
            
            # Load configuration from ConfigManager
            config = self._load_ai_config()
            
            print(f"[DEBUG AI Thread] Config cargada: {config}", file=sys.stderr)
            
            if not config.get("enabled"):
                raise RuntimeError("AI deshabilitado. Habilítalo en la configuración.")
            
            provider = config.get("provider", "")
            model = config.get("model", "")
            api_key = config.get("api_key", "")
            base_url = config.get("base_url", "").rstrip("/")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 4096)
            system_prompt = config.get("system_prompt", "Eres un asistente de programación útil.")
            
            print(f"[DEBUG AI Thread] Provider: {provider}, Model: {model}, Temp: {temperature}, MaxTokens: {max_tokens}", file=sys.stderr)
            print(f"[DEBUG AI Thread] API Key presente: {bool(api_key)}, Longitud: {len(api_key) if api_key else 0}", file=sys.stderr)
            print(f"[DEBUG AI Thread] Base URL: {base_url}", file=sys.stderr)
            
            # Build the prompt
            full_prompt = self._build_prompt(self.prompt, self.context)
            print(f"[DEBUG AI Thread] Prompt construido (primeros 100 chars): {full_prompt[:100]}...", file=sys.stderr)
            
            self.progress.emit(f"Consultando {provider}...")
            
            # Route to appropriate provider
            if provider == "Ollama":
                response = self._call_ollama(base_url, model, full_prompt, temperature, max_tokens)
            elif provider == "LM Studio":
                response = self._call_openai_compatible(base_url, model, full_prompt, system_prompt, api_key, temperature, max_tokens)
            elif provider == "OAI Compatible":
                response = self._call_openai_compatible(base_url, model, full_prompt, system_prompt, api_key, temperature, max_tokens)
            elif provider == "OpenAI":
                response = self._call_openai(model, full_prompt, system_prompt, api_key, temperature, max_tokens)
            elif provider == "Together AI":
                response = self._call_together(model, full_prompt, api_key, temperature, max_tokens)
            elif provider == "KoboldCPP":
                response = self._call_koboldcpp(base_url, model, full_prompt, temperature, max_tokens)
            
            elif provider == "Hugging Face":
                response = self._call_huggingface(model, full_prompt, api_key, temperature, max_tokens)
            
            else:
                raise RuntimeError(f"Proveedor desconocido: {provider}")
            
            print(f"[DEBUG AI Thread] Respuesta recibida (primeros 100 chars): {str(response)[:100]}...", file=sys.stderr)
            self.finished.emit(response)
            
        except Exception as e:
            print(f"[DEBUG AI Thread] Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.error.emit(str(e))
    
    def _load_ai_config(self) -> Dict:
        """Load AI configuration from ConfigManager."""
        try:
            from core.utils.config import ConfigManager
            config = ConfigManager().load()
            if config and hasattr(config, 'get_ai_config'):
                return config.get_ai_config()
        except Exception as e:
            print(f"Error loading AI config: {e}")
        return {"enabled": False}
    
    def _call_ollama(self, base_url: str, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Ollama API."""
        import requests
        
        endpoint = f"{base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(endpoint, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Sin respuesta")
    
    def _call_openai_compatible(self, base_url: str, model: str, prompt: str, system_prompt: str, api_key: str, temperature: float, max_tokens: int) -> str:
        """Call OpenAI-compatible API (LM Studio, etc.)."""
        import requests
        
        endpoint = f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _call_openai(self, model: str, prompt: str, system_prompt: str, api_key: str, temperature: float, max_tokens: int) -> str:
        """Call OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai no instalado. Ejecuta: pip install openai")
        
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def _call_huggingface(self, model: str, prompt: str, api_key: str, temperature: float, max_tokens: int) -> str:
        """Call Hugging Face Inference API using huggingface_hub library."""
        import sys
        
        print(f"[DEBUG HF] Iniciando conexión con model={model}, temp={temperature}, max_tokens={max_tokens}", file=sys.stderr)
        
        try:
            from huggingface_hub import InferenceClient
        except ImportError:
            print("[DEBUG HF] ERROR: huggingface_hub no instalado", file=sys.stderr)
            raise RuntimeError("huggingface_hub no instalado. Ejecuta: pip install huggingface-hub")
        
        # Clean model name if it has prefix from settings (e.g., "[Código] modelname")
        clean_model = model
        if model.startswith("["):
            clean_model = model.split("]", 1)[1].strip()
        
        print(f"[DEBUG HF] Modelo limpio: {clean_model}", file=sys.stderr)
        
        # Use default code model if not specified
        if not clean_model or clean_model == "default":
            clean_model = "meta-llama/CodeLlama-7b-hf"
            print(f"[DEBUG HF] Usando modelo por defecto: {clean_model}", file=sys.stderr)
        
        # Initialize client with API key if available
        if api_key:
            print(f"[DEBUG HF] Usando API key (longitud: {len(api_key)})", file=sys.stderr)
            client = InferenceClient(token=api_key)
        else:
            print("[DEBUG HF] Sin API key, usando cliente público", file=sys.stderr)
            client = InferenceClient()
        
        self.progress.emit("Conectando a Hugging Face...")
        print("[DEBUG HF] Cliente inicializado, enviando solicitud...", file=sys.stderr)
        
        # Format prompt for better code generation
        code_prompt = f"""Write Python code for the following task. Include necessary imports and comments:

Task: {prompt}

Requirements:
- Use best practices
- Add error handling where appropriate  
- Include docstrings

Python code:"""
        
        print(f"[DEBUG HF] Prompt (primeros 200 chars): {code_prompt[:200]}...", file=sys.stderr)
        
        try:
            # Use chat_completion for better results with code models
            print(f"[DEBUG HF] Llamando chat_completion con modelo: {clean_model}", file=sys.stderr)
            response = client.chat_completion(
                model=clean_model,
                messages=[{"role": "user", "content": code_prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            print(f"[DEBUG HF] Respuesta recibida: {response}", file=sys.stderr)
            
            result = response.choices[0].message.content
            print(f"[DEBUG HF] Resultado (primeros 200 chars): {result[:200]}...", file=sys.stderr)
            
            # Clean markdown formatting from response
            if "```python" in result:
                result = result.split("```python")[1]
                if "```" in result:
                    result = result.split("```")[0]
            elif result.startswith("```"):
                lines = result.split("\n")
                result = "\n".join(lines[1:])  # Skip ```python line
                if result.endswith("```"):
                    result = result[:-3]
            
            print(f"[DEBUG HF] Resultado limpio (primeros 200 chars): {result[:200]}...", file=sys.stderr)
            return result.strip()
            
        except Exception as e:
            print(f"[DEBUG HF] Error en chat_completion: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            # Fallback to old inference API
            print("[DEBUG HF] Intentando fallback con API legacy...", file=sys.stderr)
            import requests
            endpoint = f"https://api-inference.huggingface.co/models/{clean_model}"
            
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            payload = {
                "inputs": code_prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "return_full_text": False
                }
            }
            
            print(f"[DEBUG HF] POST a {endpoint}", file=sys.stderr)
            response = requests.post(endpoint, json=payload, headers=headers, timeout=180)
            print(f"[DEBUG HF] Respuesta legacy: status={response.status_code}", file=sys.stderr)
            response.raise_for_status()
            result = response.json()
            print(f"[DEBUG HF] Resultado legacy: {result}", file=sys.stderr)
            
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                if generated_text.startswith(code_prompt):
                    generated_text = generated_text[len(code_prompt):].strip()
                return generated_text
            elif isinstance(result, dict):
                return result.get("generated_text", "Sin respuesta")
            else:
                return str(result)
    
    def _call_together(self, model: str, prompt: str, api_key: str, temperature: float, max_tokens: int) -> str:
        """Call Together AI API."""
        import requests
        
        endpoint = "https://api.together.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _call_koboldcpp(self, base_url: str, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call KoboldCPP API."""
        import requests
        
        endpoint = f"{base_url}/v1/generate"
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": model or ""  # KoboldCPP may not require model
        }
        
        response = requests.post(endpoint, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("results", [{}])[0].get("text", "Sin respuesta")
    
    def _build_prompt(self, prompt: str, context: Dict) -> str:
        """Build a prompt with context for the AI."""
        project_path = context.get("project_path", "Unknown")
        files = context.get("files", [])
        
        file_list = "\n".join(f"- {f}" for f in files[:20])  # Limit to 20 files
        
        return f"""
Proyecto: {project_path}
Archivos disponibles:
{file_list}

Pregunta del usuario: {prompt}

Responde de manera helpful y técnica.
"""
    
    def _generate_placeholder_response(self) -> str:
        """Generate a placeholder response when AI is not configured."""
        return """🤖 **Asistente IA - No configurado**

La integración con IA aún no está configurada. Para habilitar el asistente:

1. **Ollama (local):**
   - Instala Ollama desde https://ollama.ai
   - Configura el endpoint en AI_CONFIG
   
2. **OpenAI:**
   - Obtén una API key de https://platform.openai.com
   - Configura tu API key en AI_CONFIG

3. **Otros modelos:**
   - Compatible con cualquier API REST que siga el formato de OpenAI

--- 
Tu mensaje: """ + self.prompt[:100] + ("..." if len(self.prompt) > 100 else "") + """

*Esta es una respuesta de marcador de posición. Implementa la integración con IA para obtener respuestas reales.*
"""


class AIPanelWidget(QWidget):
    """
    Panel for AI assistant with chat and file operations.
    """
    
    # Signal when panel is closed
    panel_closed = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None, project_path: Optional[Path] = None):
        super().__init__(parent)
        
        self._project_root = project_path or Path.cwd()
        self._current_directory = self._project_root
        self._history: List[Dict] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self._clear_btn = QPushButton("🗑️ Limpiar")
        self._clear_btn.clicked.connect(self._clear_chat)
        toolbar.addWidget(self._clear_btn)
        
        self._refresh_btn = QPushButton("🔄 Actualizar Archivos")
        self._refresh_btn.clicked.connect(self._refresh_files)
        toolbar.addWidget(self._refresh_btn)
        
        toolbar.addStretch()
        
        main_layout.addLayout(toolbar)
        
        # Chat area splitter
        chat_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Read-only output area
        output_group = QGroupBox("Mensajes de IA")
        output_layout = QVBoxLayout(output_group)
        
        self._output_edit = QTextEdit()
        self._output_edit.setReadOnly(True)
        self._output_edit.setFont(QFont("Monospace", 10))
        self._output_edit.setPlaceholderText("Aquí aparecerán las respuestas de la IA...")
        output_layout.addWidget(self._output_edit)
        
        chat_splitter.addWidget(output_group)
        
        # Input area
        input_group = QGroupBox("Entrada")
        input_layout = QVBoxLayout(input_group)
        
        # Command/chat input
        self._input_edit = QTextEdit()
        self._input_edit.setPlaceholderText("Escribe tu mensaje o comando...\n\nComandos especiales:\n- /leer [archivo] - Leer archivo\n- /escribir [ruta] [contenido] - Escribir archivo\n- /crear_dir [ruta] - Crear directorio\n- /listar [ruta] - Listar directorio\n- /ejecutar [comando] - Ejecutar comando\n- /chat [mensaje] - Chat normal con IA")
        self._input_edit.setMaximumHeight(120)
        self._input_edit.setFont(QFont("Monospace", 10))
        input_layout.addWidget(self._input_edit)
        
        # Send button
        send_layout = QHBoxLayout()
        
        self._send_btn = QPushButton("📤 Enviar")
        self._send_btn.clicked.connect(self._send_message)
        send_layout.addWidget(self._send_btn)
        
        send_layout.addStretch()
        
        input_layout.addLayout(send_layout)
        
        chat_splitter.addWidget(input_group)
        
        # Set sizes
        chat_splitter.setSizes([400, 150])
        
        main_layout.addWidget(chat_splitter)
        
        # Status bar
        self._status_label = QLabel("Listo")
        main_layout.addWidget(self._status_label)
    
    def _clear_chat(self) -> None:
        """Clear the chat history."""
        self._output_edit.clear()
        self._history.clear()
        self._status_label.setText("Chat limpiado")
    
    def _refresh_files(self) -> None:
        """Refresh file list."""
        try:
            files = list(self._project_root.rglob("*"))
            count = len([f for f in files if f.is_file()])
            dirs = len([f for f in files if f.is_dir()])
            self._status_label.setText(f"Archivos: {count}, Directorios: {dirs}")
        except Exception as e:
            self._status_label.setText(f"Error: {e}")
    
    def _send_message(self) -> None:
        """Send message or command."""
        text = self._input_edit.toPlainText().strip()
        if not text:
            return
        
        # Add user message to chat
        self._append_to_chat(f"👤 Tú: {text}\n", "user")
        self._input_edit.clear()
        
        # Parse command
        if text.startswith("/"):
            self._handle_command(text)
        else:
            # Default to chat
            self._handle_chat(text)
    
    def _handle_command(self, command: str) -> None:
        """Handle special commands."""
        parts = command.split(None, 2)
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            if cmd == "/leer":
                self._cmd_read(args)
            elif cmd == "/escribir":
                self._cmd_write(args)
            elif cmd == "/crear_dir":
                self._cmd_mkdir(args)
            elif cmd == "/listar":
                self._cmd_list(args)
            elif cmd == "/ejecutar":
                self._cmd_execute(args)
            elif cmd == "/chat":
                self._handle_chat(" ".join(args) if args else "")
            elif cmd == "/ayuda":
                self._show_help()
            else:
                self._append_to_chat(f"⚠️ Comando desconocido: {cmd}\nUsa /ayuda para ver comandos disponibles\n", "error")
        except Exception as e:
            self._append_to_chat(f"❌ Error: {e}\n", "error")
    
    def _cmd_read(self, args: List[str]) -> None:
        """Read a file."""
        if not args:
            self._append_to_chat("⚠️ Uso: /leer [archivo]\n", "error")
            return
        
        file_path = self._resolve_path(args[0])
        
        if not file_path.exists():
            self._append_to_chat(f"❌ Archivo no encontrado: {file_path}\n", "error")
            return
        
        if not file_path.is_file():
            self._append_to_chat(f"❌ No es un archivo: {file_path}\n", "error")
            return
        
        try:
            content = file_path.read_text(encoding="utf-8")
            preview = content[:500] + "..." if len(content) > 500 else content
            self._append_to_chat(f"📄 {file_path.relative_to(self._project_root)}:\n```\n{preview}\n```\n", "system")
        except Exception as e:
            self._append_to_chat(f"❌ Error leyendo: {e}\n", "error")
    
    def _cmd_write(self, args: List[str]) -> None:
        """Write to a file."""
        if len(args) < 2:
            self._append_to_chat("⚠️ Uso: /escribir [archivo] [contenido]\n", "error")
            return
        
        file_path = self._resolve_path(args[0])
        
        # Security check
        if not self._is_safe_path(file_path):
            self._append_to_chat("❌ Acceso denegado: Ruta fuera del proyecto\n", "error")
            return
        
        content = args[1]
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            self._append_to_chat(f"✅ Archivo guardado: {file_path.relative_to(self._project_root)}\n", "system")
        except Exception as e:
            self._append_to_chat(f"❌ Error escribiendo: {e}\n", "error")
    
    def _cmd_mkdir(self, args: List[str]) -> None:
        """Create a directory."""
        if not args:
            self._append_to_chat("⚠️ Uso: /crear_dir [directorio]\n", "error")
            return
        
        dir_path = self._resolve_path(args[0])
        
        # Security check
        if not self._is_safe_path(dir_path):
            self._append_to_chat("❌ Acceso denegado: Ruta fuera del proyecto\n", "error")
            return
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            self._append_to_chat(f"✅ Directorio creado: {dir_path.relative_to(self._project_root)}\n", "system")
        except Exception as e:
            self._append_to_chat(f"❌ Error creando directorio: {e}\n", "error")
    
    def _cmd_list(self, args: List[str]) -> None:
        """List directory contents."""
        if args:
            dir_path = self._resolve_path(args[0])
        else:
            dir_path = self._current_directory
        
        if not dir_path.exists():
            self._append_to_chat(f"❌ Directorio no encontrado: {dir_path}\n", "error")
            return
        
        try:
            items = []
            for item in sorted(dir_path.iterdir()):
                prefix = "📁" if item.is_dir() else "📄"
                items.append(f"{prefix} {item.name}")
            
            if items:
                result = f"📁 {dir_path.relative_to(self._project_root)}:\n" + "\n".join(f"  {i}" for i in items)
            else:
                result = f"📁 Directorio vacío: {dir_path.name}"
            
            self._append_to_chat(result + "\n", "system")
        except Exception as e:
            self._append_to_chat(f"❌ Error listando: {e}\n", "error")
    
    def _cmd_execute(self, args: List[str]) -> None:
        """Execute a command."""
        if not args:
            self._append_to_chat("⚠️ Uso: /ejecutar [comando]\n", "error")
            return
        
        command = " ".join(args)
        
        # Run comprehensive validation first
        can_execute, message = self._validate_and_execute(command)
        if not can_execute:
            self._append_to_chat(f"{message}\n", "error")
            return
        
        # Always run in project directory
        try:
            # Use shlex.split for safer command parsing (no shell=True)
            import shlex
            cmd_list = shlex.split(command) if command else []
            
            result = subprocess.run(
                cmd_list,
                shell=False,
                cwd=str(self._project_root),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout or result.stderr or "Comando ejecutado (sin salida)"
            self._append_to_chat(f"⚡ Ejecutando: {command}\n```\n{output}\n```\n", "system")
        except subprocess.TimeoutExpired:
            self._append_to_chat("❌ Timeout: El comando tardó más de 30 segundos\n", "error")
        except Exception as e:
            self._append_to_chat(f"❌ Error: {e}\n", "error")
    
    def _handle_chat(self, message: str) -> None:
        """Handle chat message with AI."""
        if not message:
            self._append_to_chat("⚠️ Escribe un mensaje para chatear con la IA\n", "error")
            return
        
        self._status_label.setText("IA procesando...")
        self._send_btn.setEnabled(False)
        
        # Build context
        context = {
            "project_path": str(self._project_root),
            "files": [str(f) for f in self._project_root.rglob("*") if f.is_file()][:50]
        }
        
        # Start inference thread
        self._inference_thread = AIInferenceThread(message, context)
        self._inference_thread.finished.connect(self._on_inference_finished)
        self._inference_thread.error.connect(self._on_inference_error)
        self._inference_thread.start()
    
    def _on_inference_finished(self, response: str) -> None:
        """Handle inference finished."""
        self._append_to_chat(f"🤖 IA:\n{response}\n", "assistant")
        self._status_label.setText("Listo")
        self._send_btn.setEnabled(True)
    
    def _on_inference_error(self, error: str) -> None:
        """Handle inference error."""
        self._append_to_chat(f"❌ Error: {error}\n", "error")
        self._status_label.setText("Error")
        self._send_btn.setEnabled(True)
    
    def _show_help(self) -> None:
        """Show help message."""
        help_text = """
📖 Comandos disponibles:

🗂️ Lectura/Escritura:
  /leer [archivo] - Leer contenido de un archivo
  /escribir [ruta] [contenido] - Escribir en archivo
  /crear_dir [ruta] - Crear directorio
  /listar [ruta] - Listar contenido de directorio

⚡ Ejecución:
  /ejecutar [comando] - Ejecutar comando en terminal
  /chat [mensaje] - Chat con IA

📋 Utilidades:
  /ayuda - Mostrar esta ayuda
  (sin prefijo) - Chat con IA

⚠️ Seguridad:
  - No puedes salir del directorio del proyecto
  - Comandos peligrosos bloqueados
"""
        self._append_to_chat(help_text, "system")
    
    def _append_to_chat(self, text: str, role: str = "system") -> None:
        """Append text to chat output."""
        self._output_edit.moveCursor(QTextCursor.MoveOperation.End)
        self._output_edit.insertPlainText(text)
        self._output_edit.moveCursor(QTextCursor.MoveOperation.End)
    
    def _resolve_path(self, path_str: str) -> Path:
        """Resolve a path relative to project root."""
        path = Path(path_str)
        if path.is_absolute():
            return path
        return self._project_root / path
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is within project root."""
        try:
            path.resolve().relative_to(self._project_root.resolve())
            return True
        except ValueError:
            return False
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute."""
        # First run basic blocked commands check
        command_lower = command.lower()
        
        # Check blocked commands
        for blocked in BLOCKED_COMMANDS:
            if blocked in command_lower:
                return False
        
        # Check for pipe to dangerous commands
        if "|" in command:
            parts = command.split("|")
            for part in parts[1:]:
                if any(b in part.lower() for b in ["sh", "bash", "cmd", "powershell"]):
                    return False
        
        # Run comprehensive input validation
        return self._validate_command_input(command)
    
    def _validate_command_input(self, command: str) -> tuple[bool, str]:
        """
        Comprehensive input validation for command execution.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        import re
        
        # Check for empty or whitespace-only input
        if not command or not command.strip():
            return False, "El comando no puede estar vacío"
        
        # Check length constraints
        if len(command) < MIN_COMMAND_LENGTH:
            return False, f"El comando es demasiado corto (mínimo {MIN_COMMAND_LENGTH} carácter)"
        
        if len(command) > MAX_COMMAND_LENGTH:
            return False, f"El comando es demasiado largo (máximo {MAX_COMMAND_LENGTH} caracteres)"
        
        # Count arguments to prevent overflow
        parts = command.split()
        if len(parts) > MAX_ARGUMENTS:
            return False, f"Demasiados argumentos (máximo {MAX_ARGUMENTS})"
        
        # Check for dangerous patterns using regex
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Patrón potencialmente peligroso detectado: {pattern}"
        
        # Check for null bytes or control characters
        if any(ord(c) < 32 and c not in '\t\n\r' for c in command):
            return False, "El comando contiene caracteres de control no válidos"
        
        # Check for path traversal patterns
        if ".." in command:
            return False, "Patrón de navegación de directorios no permitido"
        
        # Check for potential environment variable injection
        if "${" in command or command.startswith("export "):
            return False, "Inyección de variables de entorno no permitida"
        
        # Check for here-documents and here-strings
        if re.search(r"<<\s*\w+", command):
            return False, "Here-document no permitido"
        
        return True, ""
    
    def _validate_and_execute(self, command: str) -> tuple[bool, str]:
        """
        Validate command and return tuple of (success, message).
        
        Returns:
            Tuple of (can_execute, message)
        """
        is_valid, error_msg = self._validate_command_input(command)
        
        if not is_valid:
            return False, f"⚠️ Validación fallida: {error_msg}"
        
        # Also check against blocked commands
        if not self._is_safe_command(command):
            return False, "❌ Comando bloqueado por seguridad"
        
        return True, ""
    
    def focus_input(self) -> None:
        """Focus the input area."""
        self._input_edit.setFocus()
