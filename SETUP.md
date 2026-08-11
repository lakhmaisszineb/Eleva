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
```


### 6. Configure environment

```bash
cp .env.example .env

Windows (CMD):
```bash
copy .env.example .env

Edit .env and set at least:

envGROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
DATA_DIR=./data/sample_data
KNOWLEDGE_DIR=./knowledge/playbooks
CHROMA_PERSIST_DIR=./chroma_db


Never commit the real .env file.

### 7. Run the project
Always from the project root (eleva/), with the virtualenv activated.
Terminal 1 — API (backend)
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
Health: http://127.0.0.1:8000/health
Swagger: http://127.0.0.1:8000/docs

Terminal 2 — UI (Streamlit)

```bash
streamlit run ui/app.py
```
UI: http://localhost:8501

```bash
export ELEVA_API_URL=http://127.0.0.1:8000
```
### 8. First analysis (smoke test)

Open http://localhost:8501
Check that the status dot shows Agent disponible (API must be running)
Go to Analyse → select company_001 → choose a question → Lancer l’analyse
Open Résultats, then Explication

Or via API:

```bash
curl -s -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "company_001",
    "question": "Analyse la situation actuelle et propose les actions prioritaires.",
    "max_recommendations": 3
  }' | python -m json.tool
```