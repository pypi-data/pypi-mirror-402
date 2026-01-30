# MBM - Modular CLI Platform

[![PyPI version](https://badge.fury.io/py/mbm.svg)](https://badge.fury.io/py/mbm)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/mbm/mbm-cli)

**MBM** is a powerful, modular command-line interface platform featuring the Aaryan programming language, an intelligent AI assistant, and a student birthday countdown system. Built for education, productivity, and extensibility.

## 🚀 Installation

### Step 1: Install Python (if not already installed)

Download from [python.org](https://www.python.org/downloads/) and **check "Add Python to PATH"** during installation.

### Step 2: Install MBM

```bash
pip install mbm
```

That's it! Now you can use `mbm` from any terminal.

### Verify Installation

```bash
mbm --version
```

If `mbm` is not recognized, use this alternative (always works):
```bash
python -m mbm.cli.main --version
```

### Troubleshooting PATH Issues

<details>
<summary><b>Windows</b> - If 'mbm' is not recognized</summary>

```powershell
# Find where mbm is installed
python -c "import sys, os; print(os.path.join(os.path.dirname(sys.executable), 'Scripts'))"

# Add that path to your system PATH, or use:
python -m mbm.cli.main
```
</details>

<details>
<summary><b>macOS/Linux</b> - If 'mbm' is not recognized</summary>

```bash
# Find where mbm is installed
python3 -c "import sys, os; print(os.path.join(os.path.dirname(sys.executable), 'bin'))"

# Add to PATH in ~/.bashrc or ~/.zshrc:
export PATH="$PATH:$(python3 -m site --user-base)/bin"
```
</details>

## 📖 Quick Start

### Basic Commands

```bash
# Show MBM banner and help
mbm

# Access Aaryan language
mbm aaryan

# Run an Aaryan program
mbm aaryan run program.ar

# Start AI assistant
mbm ai

# View student birthday countdown (433 students!)
mbm kanishka_singhal
mbm vidhi_dave
mbm students --upcoming

# View animations demo
mbm animate --all

# List all students
mbm students
mbm students -b CSE    # Filter by branch

# Shutdown PC (use with caution!)
mbm blast
```

## 🎯 Features

### 🖥️ CLI Platform
- Clean, intuitive command-line interface
- Rich terminal output with colors and formatting
- **Cross-platform support** (Windows, macOS, Linux)
- Works in any shell (PowerShell, CMD, Bash, Zsh, Fish)

### 🎂 Student Birthday Countdown
- **433 unique student commands** (`mbm <student_name>`)
- Real-time countdown (days, hours, minutes, seconds)
- Animated celebrations for birthdays
- Branch-wise filtering and search

### 🔤 Aaryan Language
- Custom programming language embedded in MBM
- Simple syntax for educational purposes
- File extension: `.ar`

### 🤖 AI Assistant
- **Local-first**: Uses spaCy for NLP (no cloud LLMs)
- **Intent Detection**: Understands what you're asking
- **Entity Extraction**: Identifies key terms and subjects
- **Query Cleanup**: Processes messy natural language

### 🎬 ASCII Animations
- Falling confetti with physics
- Fireworks explosions
- Birthday cakes with flickering candles
- Countdown flip animations

### 🖼️ Media Handling
- Fetches images from **legal sources only** (Wikimedia Commons)
- Opens media using system's native viewer
- Temporary files auto-cleaned

### 📚 Information Retrieval
- Wikipedia API for factual information
- Clean, concise text output
- Privacy-respecting design

## 🏗️ Architecture

```
MBM (Platform CLI)
├── aaryan (Language Module)
├── ai (AI Assistant)
├── people (Special Profiles)
│   ├── students
│   └── faculty
└── utils (Cross-platform Utilities)
```

## 🔒 Privacy & Ethics

- **No web scraping**: Only legal, public APIs
- **No Google Images**: Wikimedia Commons only
- **No cloud LLMs**: Local NLP processing
- **No tracking**: Your data stays local
- **No permanent storage**: Temp files only

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/mbm/mbm-cli.git
cd mbm-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install in development mode
pip install -e ".[dev]"

# Download spaCy model
python -m spacy download en_core_web_sm

# Run tests
pytest
```

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- MBM University, Jodhpur
- All contributors and supporters

---

**Made with ❤️ by the MBM Team**
