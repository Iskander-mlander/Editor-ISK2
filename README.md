# Editor ISK 2.0
# En construcción / Under construction!

A professional Python code editor with AI assistance, built with PyQt6.

## Features

### Editor Core
- **Syntax Highlighting** - Multiple language support (Python, JavaScript, TypeScript, Java, C++, Go, Rust, HTML, JSON, CSS)
- **Code Folding** - Collapse and expand code blocks
- **Minimap** - Document overview navigation
- **Multi-Cursor Editing** - Edit at multiple positions simultaneously
- **Auto-completion** - Intelligent code completion
- **Bracket Matching** - Highlight matching brackets

### AI Assistant
- **Multi-Provider Support** - Ollama, OpenAI, LM Studio compatibility
- **Code Analysis** - Analyze and explain code
- **Refactoring** - AI-powered code refactoring
- **Error Explanation** - Understand error messages

### Git Integration
- **Visual Git Panel** - Stage, unstage, commit changes
- **Branch Management** - Create, checkout, delete branches
- **Remote Operations** - Pull, push, fetch
- **Diff Viewer** - View changes before committing

### Terminal
- **PTY Terminal** - Full shell support with pseudo-terminal
- **Python Runner** - Run Python files directly
- **Command Execution** - Execute shell commands

### Code Tools
- **Snippets** - Code snippet management with trigger expansion
- **Code Actions** - Quick fixes and refactoring suggestions
- **Keyboard Shortcuts** - 40+ customizable shortcuts
- **Linting** - Pylint, Flake8, Black, ShellCheck integration

### Language Server Protocol
- **Multi-Language Support** - Python, JavaScript, TypeScript, Go, Rust, C++, Java, JSON
- **Auto-diagnostics** - Real-time error detection
- **Code Completion** - LSP-powered completions

### Themes
- **Theme Manager** - Multiple built-in themes
- **Built-in Themes**: Default Dark, Default Light, Solarized Dark, Solarized Light, GitHub Dark, VS Code Dark, VS Code Light, One Dark, One Light

### Testing
- **Unit Tests** - 61+ passing tests with pytest

### UI Components
- **Welcome Screen** - Shown when no files are open with recent files list
- **Status Bar** - Shows line, column, encoding, language, and modified indicator
- **Keyboard Shortcuts Dialog** - View and search all available shortcuts

### Extensibility
- **Plugin System** - Full plugin architecture with discovery, load/unload, activation/deactivation
- **Plugin API** - Base plugin class with signals, metadata, and lifecycle management

## Architecture

The project follows a modular architecture with clear separation of concerns:

```
Editor-ISK-V2/
├── core/                    # Core independent functionality
│   ├── editor/              # Pure editor functionality
│   │   ├── code_editor.py  # Editor widget
│   │   ├── syntax_highlighter.py  # Syntax highlighting
│   │   ├── fold.py         # Code folding
│   │   ├── minimap.py      # Minimap view
│   │   ├── multicursor.py   # Multi-cursor editing
│   │   └── languages.py     # Language definitions
│   ├── lsp/                 # Language Server Protocol
│   │   ├── client.py        # LSP client
│   │   ├── registry.py      # Server registry
│   │   └── completions.py   # Completion handling
│   ├── utils/               # Utility modules
│   │   ├── config.py        # Configuration
│   │   ├── shortcuts.py     # Keyboard shortcuts
│   │   ├── accessibility.py # Accessibility features
│   │   └── theme_manager.py  # Theme management
│   └── linting.py           # Linting integration
│
├── ui/                      # User Interface
│   ├── main_window.py       # Main window
│   ├── splash.py           # Splash screen
│   └── widgets/            # UI widgets
│
├── features/                # Internal features
│   ├── ai_assistant/       # AI assistant
│   │   ├── provider.py     # AI providers (Ollama, OpenAI)
│   │   └── chat.py         # Chat interface
│   ├── debugging/          # Debugger
│   │   └── manager.py      # Debug manager with breakpoints
│   ├── git/                # Git integration
│   │   └── client.py       # Git client
│   ├── snippets/           # Code snippets
│   │   ├── manager.py      # Snippet manager
│   │   └── expander.py     # Snippet expansion
│   └── refactoring/        # Code refactoring
│       └── actions.py      # Code actions
│
├── resources/               # Resources
│   ├── themes/            # Color themes (9 themes)
│   └── translations/       # i18n translations
│
├── plugins/                 # Plugin system
│   ├── base.py            # Base plugin class
│   └── manager.py         # Plugin manager
│
├── tests/                   # Unit tests
│   └── unit/              # Test suite (61+ tests)
│
└── config/                  # Configuration management
```

## Design Principles

- **Single Responsibility**: Each file has one clear responsibility
- **Dependency Injection**: Use signals instead of direct references
- **Static Typing**: Use typing and dataclasses
- **Documentation**: Docstrings on all classes and methods

## Requirements

- Python 3.10+
- PyQt6 6.5+

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Testing

```bash
pytest tests/
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New File | Ctrl+N |
| Open File | Ctrl+O |
| Save | Ctrl+S |
| Save As | Ctrl+Shift+S |
| Open Folder | Ctrl+Shift+O |
| Close All | Ctrl+Shift+W |
| Find | Ctrl+F |
| Replace | Ctrl+H |
| Go to Line | Ctrl+G |
| Toggle Comment | Ctrl+/ |
| Move Line Up | Alt+Up |
| Move Line Down | Alt+Down |
| Copy Line Up | Shift+Alt+Up |
| Copy Line Down | Shift+Alt+Down |
| Delete Line | Ctrl+Shift+K |
| Fold All | Ctrl+Shift+[ |
| Unfold All | Ctrl+Shift+] |
| Run File | F5 |
| Stop | Shift+F5 |
| Command Palette | Ctrl+Shift+P |
| Keyboard Shortcuts | Ctrl+K, Ctrl+S |
| File Explorer | Ctrl+B |
| Terminal | Ctrl+` |
| AI Panel | Ctrl+Shift+A |
| Git Panel | Ctrl+Shift+G |
| Settings | Ctrl+, |
| Zoom In | Ctrl++ |
| Zoom Out | Ctrl+- |
| Zoom Reset | Ctrl+0 |

## License

See LICENSE file for details.
