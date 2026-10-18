# TESTING.md — Eleva test suite

**What this is:** an offline, reproducible test suite (unit + integration) plus an optional live smoke suite.
**What it is not:** proof that the real Groq model gives *good* advice. See "Limits" at the end.

Results of the last run and the list of bugs found: see **[TEST_REPORT.md](TEST_REPORT.md)**.

---

## 1. Prerequisites

| Need | Detail |
|------|--------|
| Python | 3.12 (what the README targets; the suite was run on 3.12.3) |
| Internet | only for `pip install`. The default suite makes **no** network call |
| Groq API key | **not needed** for the default suite. Only for the optional live tests |
| Your real DB / Chroma | never touched (see section 3) |

## 2. Setup (from the project root, the folder containing `main.py`)

```bash
# Linux / macOS                                   # Windows PowerShell
python3.12 -m venv .venv                          py -3.12 -m venv .venv
source .venv/bin/activate                         .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt               pip install -r requirements-dev.txt
```

`requirements-dev.txt` = your `requirements.txt` + `pytest` + `pytest-cov`. Production dependencies are unchanged.
Always use `python -m pytest ...` (works even if `pytest` is not on PATH).

## 3. How your data is protected

`tests/conftest.py` sets the environment **before** any Eleva module is imported:

* `GROQ_API_KEY` = a dummy value → no real/paid call is possible in default mode
* `DATA_DIR`, `CHROMA_PERSIST_DIR` → throw-away temp folders
* an autouse fixture gives **every test its own fresh SQLite file**
* a test (`test_tests_never_use_the_real_development_database`) fails if this ever breaks

Your `data/sample_data/eleva.db`, `chroma_db/`, `data/uploads/` and `.env` are never read or written by the default suite.
The demo JSON files in `data/sample_data/` are only **read** (migrated into a temp DB).

## 4. Commands

| Goal | Command | Expected |
|------|---------|----------|
| Whole default suite | `python -m pytest` | `334 passed, 11 xfailed` in ~10 s |
| Unit tests only | `python -m pytest tests/unit` | `274 passed, 7 xfailed` |
| Integration tests only | `python -m pytest tests/integration` | `60 passed, 4 xfailed` |
| One file | `python -m pytest tests/unit/test_services_rfm_metrics.py -v` | one line per test |
| One test by name | `python -m pytest -k "abandonment_threshold" -v` | only matching tests |
| Show the known bugs | `python -m pytest -rx` | lists every `XFAIL` with its reason |
| Run the known-bug tests *as real failures* (evidence for your report) | `python -m pytest --runxfail -q` | 11 failures, each showing the actual wrong behaviour |
| Coverage | `python -m pytest --cov=api --cov=config --cov=core --cov=data --cov=engine --cov=knowledge --cov=llm --cov=services --cov-report=term-missing` | ~96 % lines (a by-product, not a goal) |
| **Optional live tests** | see section 6 | skipped unless you opt in |

### Optional live tests (real Groq + real embedding model)

```bash
# Linux / macOS                                          # Windows PowerShell
export GROQ_API_KEY=gsk_...    # or put it in .env      $env:GROQ_API_KEY="gsk_..."
ELEVA_LIVE_TESTS=1 python -m pytest tests/live -v        $env:ELEVA_LIVE_TESTS="1"; python -m pytest tests/live -v
```
Needs internet; the embedding test downloads an ONNX model (~80 MB) on first use; the LLM tests use a few Groq calls.
Without `ELEVA_LIVE_TESTS=1` the 4 live tests are collected and **skipped** (`python -m pytest tests/live -rs`).

## 5. Reading the results

| Symbol | Meaning | What to do |
|--------|---------|-----------|
| `passed` | behaviour matches the explicit expectation | nothing |
| `XFAIL` | **known application bug / limitation**. The assertion states the *correct* behaviour and currently fails on purpose (`strict=True`) | cite it in your report; fix the app later |
| `FAILED ... [XPASS(strict)]` | a known bug **no longer fails** → you fixed it | delete the `xfail` marker on that test |
| `FAILED` (anything else) | a regression or an environment problem | read the assertion; see troubleshooting |
| `skipped` | live test not enabled | expected by default |

## 6. Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `ModuleNotFoundError: No module named 'config'` | run from the project root, not from `tests/` |
| `No module named pytest` / `pytest: command not found` | venv not activated, or use `python -m pytest`; re-run `pip install -r requirements-dev.txt` |
| `ValidationError ... groq_api_key Field required` when running `python main.py` / `uvicorn` | normal: the app requires `GROQ_API_KEY` in `.env`. The tests set a dummy one themselves |
| `UsageError: ELEVA_LIVE_TESTS=1 but no GROQ_API_KEY found` | you enabled live mode without a key |
| Live embedding test fails with `ConnectError` / `sha256` / `onnx` | no internet or a corrupted model download; delete `~/.cache/chroma/onnx_models` and retry |
| Live LLM tests fail with 401 / 429 | invalid key / rate limit |
| `PermissionError` on temp files (Windows) | close apps locking `%TEMP%\eleva_tests_*`; they are removed at exit |
| Different counts than section 4 | you changed tests/app code; compare with `python -m pytest --collect-only -q` |

## 7. Test-to-functionality map

| Functionality (real module) | Unit tests | Integration tests |
|-----------------------------|-----------|-------------------|
| Settings, models, exceptions (`config/`, `core/`) | `unit/test_config_models.py` | — |
| SQLite layer, `CompanyStore`, company creation, JSON catalog (`data/db.py`, `company_store.py`, `company_admin.py`, `catalog.py`) | `unit/test_db_store_admin.py` | `integration/test_import_to_store.py` |
| CSV cleaning, validation, report (`data/importer/cleaner, validator, report`) | `unit/test_cleaner_validator.py` | `integration/test_import_to_store.py` |
| LLM column mapping + alias fallback (`column_mapper.py`) | `unit/test_column_mapper.py` | `integration/test_import_to_store.py` |
| CSV import orchestration (`csv_importer.py`) | — | `integration/test_import_to_store.py` |
| KPIs and RFM (`services/metrics.py`, `rfm.py`) | `unit/test_services_rfm_metrics.py` | `integration/test_decision_pipeline.py` |
| Per-customer rules (`services/client_recommendations.py`) | `unit/test_client_recommendations.py` | `integration/test_customer_actions_flow.py` |
| Detect / Decide rules (`engine/nodes/detect.py`, `decide.py`) | `unit/test_engine_detect_decide.py` | `integration/test_decision_pipeline.py` |
| Reason / Plan / Recommend with good, malformed, failing LLM (`engine/nodes/*`) | `unit/test_engine_llm_nodes.py` | `integration/test_decision_pipeline.py` |
| Understand / Observe / Retrieve nodes + whole `DecisionEngine` | — | `integration/test_decision_pipeline.py` |
| Explainability (`engine/explain.py`) | `unit/test_engine_explain_groq.py` | `integration/test_api_end_to_end.py` |
| Groq wrapper (`llm/groq_client.py`) | `unit/test_engine_explain_groq.py` | `live/test_live_smoke.py` (optional) |
| Playbook loading (`knowledge/loader.py`) | `unit/test_knowledge_api_ui_scripts.py` | `integration/test_rag_retrieval.py` |
| RAG indexing / retrieval mechanics (`knowledge/rag.py`) | text builder only | `integration/test_rag_retrieval.py` |
| RAG *relevance* with the real model | — | `live/test_live_smoke.py` (optional) |
| FastAPI `/health`, `/analyze` (`api/`) | `unit/test_knowledge_api_ui_scripts.py` (engine mocked) | `integration/test_api_end_to_end.py` |
| UI error messages (`ui/errors.py`) | `unit/test_knowledge_api_ui_scripts.py` | — |
| JSON→SQLite migration (`scripts/migrate_json_to_sqlite.py`) | `unit/test_knowledge_api_ui_scripts.py` | `integration/test_sample_data_pipeline.py` |
| Committed demo data (`data/sample_data/*`) | — | `integration/test_sample_data_pipeline.py` |
| Multi-tenant isolation (`company_id`) | `test_store_multi_tenant_isolation` | pipeline + API isolation tests |
| Human-in-the-loop (`pending_approval`) | `test_recommend_always_requires_human_approval` | pipeline + API tests |

**Not covered:** Streamlit UI (`streamlit_app.py`, `ui/views.py`, `pipeline_view.py`, `components.py`, `theme.py`, `state.py`), `main.py` (manual script), `scripts` CLI flags, real CORS/uvicorn serving.

## 8. Known bugs found (details, evidence and suggested fixes in TEST_REPORT.md)

| ID | Where | Problem |
|----|-------|---------|
| BUG-1 | `engine/nodes/detect.py` | low-ROI campaigns are **never** reported as an issue (`"faible ROI"` searched in a lower-cased string) |
| BUG-2 | `data/importer/csv_importer.py` ↔ `ui/views.py` | `import_csv()` returns `None`, UI reads `result["report"]` → error banner after a *successful* import |
| BUG-3 | `data/importer/cleaner.py` | `"1,234.56"` parses to `None` → silently becomes `0.0` |
| BUG-4 | `engine/nodes/reason.py` | hypothesis without `issue_title` is linked to **all** issues |
| BUG-5 | `data/company_store.py` | `CompanyStore(data_dir=...)` ignores its argument |
| BUG-6 | `reason.py`, `recommend.py` | one `null` field in the LLM JSON discards the whole LLM answer (silent fallback) |
| BUG-7 | `csv_importer.py` + `db.replace_*` | header-only CSV is accepted and **deletes all existing rows** of that entity |

## 9. Limits (read before the defense)

* Fake LLM tests prove Eleva's **handling** of good/bad/failed LLM output, not the quality of real answers.
* The hash embedder proves retrieval **mechanics**; relevance with the real model is only a live smoke check (1 query).
* Synthetic data is tiny and hand-computed; thresholds (25 % abandonment, churn ≥ 0.7, ROI < 1.5, 30 % repeat) are tested for being applied as coded, **not** for being business-appropriate.
* No load, concurrency, security or UI testing was done.

## 10. Step-by-step guide for your repository

1. `cd` to the folder containing `main.py`, activate your venv.
2. `pip install -r requirements-dev.txt` → ends with "Successfully installed ..." (pytest, pytest-cov).
3. `python -m pytest --collect-only -q | tail -3` → "345 tests collected" (no test is executed yet).
4. `python -m pytest tests/unit -q` → `274 passed, 7 xfailed`. Business logic and LLM-failure handling work as coded.
5. `python -m pytest tests/integration -q` → `60 passed, 4 xfailed`. Components work together on a temp DB.
6. `python -m pytest -rx` → prints the 11 `XFAIL` lines = your documented bug list.
7. `python -m pytest --runxfail -q` → 11 real failures with tracebacks: screenshot-worthy evidence of each bug.
8. (Optional) set `GROQ_API_KEY`, then `ELEVA_LIVE_TESTS=1 python -m pytest tests/live -v` → 4 passed if Groq and the embedding download work.
9. Put the numbers in your report **only for commands you actually ran on your machine**.

> Do **not** run `python -m scripts.migrate_json_to_sqlite` against your real DB just to "prepare" tests: it replaces that company's rows (including data you imported from CSV). The tests never need it.
