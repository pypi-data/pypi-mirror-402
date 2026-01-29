# 📊 Git Commit Summary Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

A powerful, high-performance CLI tool to summarize git commits with rich visual feedback.

> **Author**: Sai Annam (mr_ask_chay)  
> **Handle**: @otaku0304  

---

## 📦 Installation

You can install this tool directly from the source to use it globally on your system.

```bash
# Clone the repository
git clone https://github.com/otaku0304/git-commit-summary.git
cd git-commit-summary

# Install globally
pip install .
```

Once installed, you can use it as a native git command!

```bash
# This now works anywhere in your terminal
git commit-summary
```

## 🌟 Previous Projects by Author
*   **[PDF Password Remover](https://pdf-fe-kappa.vercel.app/)**: A secure Angular + Flask application.
*   **[StartMyDev Dashboard](https://start-my-dev-dashboard.vercel.app/)**: Advanced automation for full-stack environments.
*   **Angular i18n SPA**: Best-in-class Internationalization demo.

---

## 🚀 Usage

If you installed it globally:
```powershell
git show HEAD | git-commit-summary
```

Or run via python directly:
```powershell
git show HEAD | python summary.py
```

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
