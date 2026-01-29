# Pytinel
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Version](https://img.shields.io/pypi/v/pytinel.svg)](https://pypi.org/project/pytinel/)

**Pytinel** (**Py**thon **T**erminal **i**n **N**atural **E**xecutable **L**anguage) is an enhanced interactive terminal tool that mimics the interface of the standard Python REPL. It elevates the traditional Python interactive experience by enabling users to **describe desired operations in natural language**—Pytinel automatically generates the corresponding Python code and executes it seamlessly.

## ✨ Key Features
1.  **Natural Language to Python Execution**
    Describe your desired operation in plain natural language, and Pytinel will silently generate and execute the corresponding Python code, returning only the final result (no intermediate code is displayed by default).
    ```
    >>> Calculate the sum of numbers from 1 to 100 and output the result
    5050

    >>> Compute the area of a circle with a radius of 5 (use pi = 3.14159)
    78.53975

    >>> Generate a list of even numbers between 20 and 40 (inclusive)
    [20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]

    >>> Convert the string "Hello World" to all uppercase letters
    'HELLO WORLD'

    >>> Calculate the factorial of 7
    5040
    ```

2.  **Safe Execution Model**
    - Generated code runs silently in the background by default, with no intermediate code exposure.
    - **High-risk operation protection**: Operations involving file system modifications, network requests, subprocess invocations, and environment variable alterations require explicit user authorization before execution. When triggering such operations, you will receive a prompt like:
      ```
      >>> Create a new text file named "demo.txt" and write the sentence "Hello Pytinel" into it
      Are you sure you want to create and write to file "demo.txt"? (Y/N):
      ```
      Only input `Y`/`y` will proceed with the operation; `N`/`n` will abort the execution immediately.

3.  **Secure Local Credential Management**
    - Configuration of an LLM API Key is required to enable natural language parsing capabilities (a guided setup wizard will launch on first run).
    - API credentials are stored locally using platform-adaptive key derivation and AES-based encryption at rest for maximum security.
    - **Zero off-device data transmission**: No credentials, prompts, generated code, or execution results are sent to external servers. Pytinel collects no telemetry, logs no session data, and performs no external communication.

4.  **In-process Python REPL Integration**
    Runs as an intelligent in-process REPL, executing code directly within your local runtime environment for consistent and reliable results.

## 📌 Project Status
This is a **toy/experimental project** created for learning and fun purposes. It is not intended for production environments or critical workloads.

## ⚠️ Disclaimer & Security Notice
### Disclaimer
This project is **not affiliated, associated, authorized, endorsed by, or in any way officially connected with the Python Software Foundation (PSF)**. Any issues, bugs, or feature requests related to Pytinel should be submitted directly to this repository's issue tracker, not to the PSF.

### Security Notice
- Code synthesized by large language models may contain logical errors, security vulnerabilities, or unintended side effects.
- Pytinel implements prompt-level risk filtering but does **not** perform static or dynamic analysis of the generated code.
- By using this tool, you acknowledge full responsibility for the safety, correctness, and consequences of all executed instructions.
- LLM API Key configuration is required for core functionality—please keep your API Key confidential and avoid sharing it in public repositories or communication channels.

## 📦 Installation
### Option 1: Install from PyPI via `pipx` (Recommended for macOS/Linux)
`pipx` isolates the package and its dependencies, avoiding conflicts with your global or project-specific Python environments—ideal for command-line tools like Pytinel.
```bash
# First, install pipx if you haven't already
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Then install Pytinel via pipx
pipx install pytinel
```

### Option 2: Install from PyPI via `pip` (Cross-platform)
The classic cross-platform installation method using `pip`, suitable for all supported Python environments:
```bash
pip install pytinel
# For Python 3.x specifically (if needed)
python3 -m pip install pytinel
```

### Option 3: Install from Source (For Development/Contribution)
If you want to modify the code or use the latest unreleased version, install in editable mode from the source repository:
```bash
# Clone the repository
git clone https://github.com/miller-owo/pytinel.git

# Navigate to project directory
cd pytinel

# Install project dependencies from requirements.txt (required step)
pip install -r requirements.txt

# Install in editable mode (changes to code take effect immediately)
pip install -e .
```

## 🔧 Build (Build from Source)
To build distributable packages (wheel/SDist) of Pytinel from the source code (e.g., for PyPI publishing or sharing), follow these steps (aligned with your project directory):

### Prerequisites (Build Dependencies)
First, install the tools required for building Python packages, and ensure project dependencies are set up:
```bash
# Upgrade pip (recommended)
python3 -m pip install --upgrade pip

# Install build tools (required for packaging)
python3 -m pip install build setuptools wheel

# Install Pytinel's project dependencies (from requirements.txt in the root directory)
pip install -r requirements.txt
```

### Build the Package
From the **project root directory** (the folder containing `main.py`, `pt_config.py`, etc.), run:
```bash
# Run the build command (automatically detects project files)
python3 -m build
```

### Build Output
After a successful build, two package types will be generated in the **`dist/` directory** (created automatically):
> Note: Replace `<version>` with your project's actual version number (e.g., `0.1.0`) in the filenames below.
1. **Wheel package** (`pytinel-<version>-py3-none-any.whl`): A pre-built, fast-installable package.
2. **Source distribution (SDist)** (`pytinel-<version>.tar.gz`): A compressed source code archive (required for PyPI publishing).

### Install from the Built Package
Test the locally built package with `pip`:
```bash
pip install dist/pytinel-<version>-py3-none-any.whl
```

## 🚀 Getting Started
### 1. First Run: Guided LLM Configuration Wizard
When you launch Pytinel for the **first time**, a step-by-step interactive setup wizard will automatically launch to help you configure your LLM credentials. No manual pre-configuration is required—follow the on-screen prompts to complete the setup:
1.  **Select LLM Provider**: Currently, only **OpenAI-compatible APIs** are supported.
2.  **Specify Model Name**: Enter the desired OpenAI model name (e.g., `gpt-4o`).
3.  **Input API Key**: Provide your valid OpenAI API Key when prompted.
4.  **Secure Storage**: Your API Key will be immediately encrypted using AES encryption (with platform-adaptive key derivation) and stored locally on your device—never transmitted externally.

### 2. Launch Pytinel
After installation, launch Pytinel directly from the terminal with a single command:
```bash
pytinel
```

### 3. Basic Usage
Once the initial configuration is complete, you can start using Pytinel immediately. Enter natural language prompts directly after the `>>>` prompt to get results:
```
>>> Calculate the result of 3 squared plus 5 cubed
134
>>> Print the current date in YYYY-MM-DD format
2026-01-18
```

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.