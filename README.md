# Eleva

**Eleva** is an autonomous AI Decision Agent specialized in e-commerce and retail marketing (fashion, beauty, food & beverage, etc.).

It acts as the **decision brain** of a multi-agent system: it analyzes company data, detects problems and opportunities, reasons in a structured and explainable way, and produces actionable marketing recommendations.  

## Core Principles

- **Decision Engine**, not a simple prompt chain
- Structured reasoning pipeline (Observe → Detect → Reason → Plan → Decide → Recommend)
- Strict separation between private company data and marketing knowledge (RAG)
- Fully explainable recommendations
- Human-in-the-loop by design
- Multi-tenant ready (isolation by `company_id`)
- Secure by default and by design

## Tech Stack (V1)

- Python 3.12
- LangChain + LangGraph
- Groq (`llama-3.3-70b-versatile`)
- Chroma (RAG over marketing playbooks)
- pandas + scikit-learn
- Pydantic
- python-dotenv

## Project Status

**Version 1 – On Demand mode only**  
The agent receives a question or analysis request, runs the full decision cycle, and returns a structured recommendation.

## Security

- Dependency scanning with `pip-audit` and `safety`
- Static analysis with `bandit` and `ruff`
- Secrets never committed (`.env` is gitignored)
- Multi-tenant data isolation

## License

Proprietary – All rights reserved.
