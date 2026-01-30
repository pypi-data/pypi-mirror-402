# cmdexy

**AI-powered CLI assistant with automatic error recovery and code fixing.**

[![GitHub](https://img.shields.io/badge/GitHub-akhilesh2220%2Fcmdexy-blue)](https://github.com/akhilesh2220/cmdexy)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ✨ Features

- 🤖 **AI-Powered Intent Analysis** - Understands what you want to do
- 🔧 **Automatic Error Recovery** - Detects failures and suggests fixes
- 📝 **Code Auto-Fixing** - Patches your files automatically
- 💻 **Shell Command Wrapper** - Monitor any command with AI assistance
- 🍎 **OS-Aware** - Generates platform-specific commands (macOS, Linux, Windows)
- 🔐 **Secure Config** - API keys stored safely in `~/.cmdexy/`

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- [Cohere API Key](https://dashboard.cohere.com/api-keys) (free tier available)

### Install from source

```bash
# Clone the repository
git clone https://github.com/akhilesh2220/cmdexy.git
cd cmdexy

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure your API key
cmdexy config
```

---

## 📖 Usage

### Configure API Key (First Time)
```bash
cmdexy config
```

### Interactive Mode
Start an AI-powered shell session:
```bash
cmdexy int
```

Example session:
```
cmdexy > create a python file that prints hello world
Intent detected: SYSTEM_COMMAND
Generated Command: cat <<EOF > hello.py
print("Hello, World!")
EOF
Execute on HOST? (y/n): y
```

### Run Single Instructions
```bash
cmdexy run "list all files in current directory"
cmdexy run "create a flask app with one endpoint"
```

### Shell Wrapper (Error Recovery)
Run any command with AI-powered error monitoring:
```bash
cmdexy shell python3 script.py
cmdexy shell ansible-playbook deploy.yml
cmdexy shell npm run build
```

If the command fails, cmdexy will:
1. Analyze the error using AI
2. Suggest a fix (code patch or install command)
3. Apply the fix automatically (with your permission)
4. Retry the command

### Check Version
```bash
cmdexy --version
```

---

## 🎯 Commands

| Command | Description |
|---------|-------------|
| `cmdexy config` | Configure API key and settings |
| `cmdexy int` | Start interactive AI session |
| `cmdexy run "<instruction>"` | Execute a single AI-powered instruction |
| `cmdexy shell <command>` | Run command with error recovery |
| `cmdexy --version` | Show version |
| `cmdexy --help` | Show help |

---

## 🔄 Error Recovery Flow

```
┌─────────────────┐
│  Run Command    │
└────────┬────────┘
         │
         ▼
   ┌───────────┐    Success
   │  Execute  │────────────► Done
   └─────┬─────┘
         │ Failure
         ▼
┌─────────────────┐
│ Analyze Error?  │──── No ───► Exit
└────────┬────────┘
         │ Yes
         ▼
┌─────────────────┐
│  AI Analysis    │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ Code  │ │ Cmd   │
│ Fix   │ │ Fix   │
└───┬───┘ └───┬───┘
    │         │
    ▼         ▼
┌─────────────────┐
│  Apply & Retry  │
└─────────────────┘
```

---

## 📁 Project Structure

```
cmdexy/
├── cmdexy/
│   ├── main.py           # CLI entry point
│   ├── cli/
│   │   ├── interactive.py  # Interactive mode
│   │   ├── run.py          # Single instruction mode
│   │   └── wrapper.py      # Shell wrapper
│   └── core/
│       ├── ai_engine.py    # Cohere AI integration
│       ├── config.py       # Configuration manager
│       ├── controller.py   # Main orchestration logic
│       └── execution.py    # Command execution
├── pyproject.toml
└── README.md
```

---

## ⚙️ Configuration

Config is stored in `~/.cmdexy/config.json`:

```json
{
  "api_key": "your-cohere-api-key"
}
```

You can also use environment variable:
```bash
export COHERE_API_KEY="your-key"
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Cohere](https://cohere.com/) for the AI API
- [Typer](https://typer.tiangolo.com/) for the CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
