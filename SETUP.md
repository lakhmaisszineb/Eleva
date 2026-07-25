# Setup Guide – Eleva

This document explains how to create and activate the Python virtual environment on different operating systems.

## Prerequisites

- Python 3.12 or higher
- `pip` and `venv` modules available

Check your Python version:

```bash
python3.12 --version
```

1. Create the virtual environment
Linux / macOS

```bash
python3.12 -m venv .venv
```
Windows (PowerShell or CMD)

```bash
python -m venv .venv
```


2. Activate the virtual environment
Linux / macOS (bash / zsh)

```bash
source .venv/bin/activate
```
Windows (Command Prompt)

```bash
.venv\Scripts\activate.bat
```
Windows (PowerShell)
```bash
.venv\Scripts\Activate.ps1
```
If you get an execution policy error in PowerShell, run once:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Deactivate
On all systems:

```bash
deactivate
```


Next steps
After activation, install the dependencies:
```bash
pip install -r requirements.txt
```
Then copy the environment file:
```bash
cp .env.example .env
```

Edit .env and add your GROQ_API_KEY.


### 5. Vérification rapide de sécurité (après freeze)

```bash
# Scanner les vulnérabilités des dépendances
pip-audit

# Alternative
safety check

# Analyse statique du code (quand on aura du code)
# bandit -r .
# ruff check .