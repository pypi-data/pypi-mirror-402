# 📊 Git Commit Summary Tool

[![PyPI Version](https://img.shields.io/pypi/v/git-commit-summary.svg)](https://pypi.org/project/git-commit-summary/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://pypi.org/project/git-commit-summary/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

A powerful, high-performance CLI tool to summarize git commits with rich visual feedback.

> **Author**: Sai Annam (mr_ask_chay)  
> **Handle**: @otaku0304  

---

## 🚀 Quick Start for Users (No Code Required)

You do **NOT** need to clone this repository to use the tool. Simply install it via pip:

```bash
pip install git-commit-summary
```

Once installed, the command `git-commit-summary` is available globally in your terminal. You can use it in any of your projects immediately.

### Usage
```bash
# 1. Go to your project folder
cd my-cool-project

# 2. Run the summary command
git show HEAD | git-commit-summary
```

---

## 🛠️ For Developers (Contributing)

Clone this repository only if you want to contribute to the source code.

```bash
git clone https://github.com/otaku0304/git-commit-summary.git
cd git-commit-summary
pip install -r requirements.txt
```

---

## ✨ Features
*   **Rich UI**: Beautiful terminal output with colors and clear formatting.
*   **Smart Analysis**: 
    *   Tracks files changed and file types (e.g., .py, .js).
    *   Calculates net changes (Added vs Removed).
    *   Detects new functions across multiple languages (Python, JS, C++).
*   **Author Branding**: Displays author credentials and portfolio links.
*   **Security Focused**: Sanitized input handling and robust error management.
*   **No Heavy Dependencies**: Runs with standard library (uses `colorama` if available, falls back gracefully).

## 🔒 Security

This tool uses sterile input processing from stdin. It does not execute external code or shell commands, ensuring your local environment remains secure against injection attacks from malicious diffs.

## 🧪 Example Output

```text
╔══════════════════════════════════════════════════════════╗
║ Git Commit Summary Tool                                  ║
║ Author: Sai Annam (mr_ask_chay / otaku0304)              ║
╚══════════════════════════════════════════════════════════╝

📊 Statistics:
  Files Changed : 2
  Lines Added   : 140
  Lines Removed : 32
  Net Change    : +108

📁 File Types:
  .py           : 1
  .md           : 1

✨ New Functions (2):
  + detect_function
  + print_banner
```

---
*Maintained with ❤️ by Sai Annam*
