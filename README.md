# Eleva

**Eleva** is an AI **Decision Agent** specialized in e-commerce and retail marketing (fashion, beauty, F&B, etc.).

It acts as the **decision brain** of a future multi-agent system: it analyzes company data, detects problems and opportunities, reasons in a structured and explainable way, and produces actionable marketing recommendations.

Eleva **does not execute** actions (emails, ads, posts). Execution is left to specialized agents later, always after **human approval**.

---

## Core Principles

- **Decision Engine** (not a single prompt)
- Structured pipeline: Understand → Observe → Detect → Retrieve (RAG) → Reason → Plan → Decide → Recommend
- Strict separation: **private company data** (local) vs **marketing knowledge** (playbooks / RAG)
- Explainable recommendations (signals, issues, playbooks, narrative)
- **Human-in-the-loop** (`pending_approval`)
- Multi-tenant isolation by `company_id`
- Secure by design (local data, no centralized customer vault in V1)

---

## What V1 Can Do

| Capability | Description |
|------------|-------------|
| **On-Demand analysis** | User picks a dataset + analysis question → full decision cycle |
| **Data import** | CSV upload with LLM column mapping (flexible headers) |
| **Observation** | KPIs, RFM segmentation, insights |
| **Detection** | Problems & opportunities (rule-based) |
| **RAG** | Marketing playbooks (Chroma) |
| **Strategic recommendations** | LLM (Groq) for reason / plan / recommend |
| **Per-customer actions** | RFM + business rules (no LLM per customer) |
| **Explainability** | Why a recommendation was made |
| **API** | FastAPI (`GET /health`, `POST /analyze`) |
| **UI** | Streamlit (Import, Analyse, Résultats, Clients, Statistiques, Explication) |

---

## Tech Stack (V1)

- **Python 3.12**
- **FastAPI** + Uvicorn
- **Streamlit** (operator UI)
- **Groq** (`llama-3.3-70b-versatile`) via LangChain
- **Chroma** (RAG over YAML playbooks)
- **Pydantic**, **pandas**
- **python-dotenv**
- Modular layout ready for LangGraph later (pipeline is sequential today)

---

## Project Structure (simplified)

```text
eleva/
├── api/                 # FastAPI app
├── config/              # Settings & logging
├── core/                # Pydantic models, exceptions
├── data/                # CompanyStore, CSV importer, catalog
│   ├── sample_data/     # Per-company JSON (local)
│   └── importer/        # LLM column mapping + clean + validate
├── engine/              # Decision Engine + nodes + explain
├── knowledge/           # Playbooks + RAG
├── llm/                 # Groq client + prompts
├── services/            # RFM, metrics, client recommendations
├── ui/                  # Streamlit app
├── requirements.txt
├── .env.example
├── README.md
└── SETUP.md