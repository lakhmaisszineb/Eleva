# TEST_REPORT.md — honest evaluation report (Eleva)

Report date: 2026-10-11. Repository state analysed: `main` @ commit `13695e4` ("interface"), fresh clone.

> **Important:** every number below comes from a run in **my sandbox** (Linux, Python 3.12.3, pytest 9.1.1, dependencies from your `requirements.txt`),
> not on your machine. Re-run the commands in TESTING.md and use *your* output in your report.

## 1. What was created (all new files; nothing existing was modified)

`pytest.ini`, `requirements-dev.txt`, `TESTING.md`, `TEST_REPORT.md`, and `tests/`:
`conftest.py`, `helpers_eleva.py`, `README.md`, `unit/` (10 files), `integration/` (6 files + conftest), `live/` (1 file), `fixtures/` (7 synthetic CSV + README).

Application source files: **0 modified**. `git status` shows only the new files above.

## 2. What was executed and the results

| Command | Result |
|---------|--------|
| `python -m pytest` (default = unit + integration) | **334 passed, 11 xfailed, 0 failed, 0 skipped** (~7 s). Run 3 times, identical |
| `python -m pytest tests/unit` | 274 passed, 7 xfailed |
| `python -m pytest tests/integration` | 60 passed, 4 xfailed |
| `python -m pytest --runxfail -q` | 11 failed, 334 passed (the 11 = the known-bug tests, each failing for the intended reason; BUG-2 and BUG-7 failure causes were inspected: `TypeError: 'NoneType' ... not subscriptable` and `assert 0 == 8`) |
| `python -m pytest tests/live` (no opt-in) | 4 collected, **4 skipped** |
| `ELEVA_LIVE_TESTS=1 python -m pytest tests/live` (no key) | stops with a clear `UsageError` (no key available) |
| Coverage (`pytest-cov`, backend packages) | 96 % of lines. **Not a quality claim.** Lowest: `scripts/migrate_json_to_sqlite.py` 48 % (CLI `main()` untested), `engine/state.py` 0 % (re-export) |

**Tests created:** 345 default + 4 live. **Skipped:** the 4 live tests (need Groq key and internet; neither available in my sandbox).
**Live tests were NOT executed**, so nothing about the real Groq API or the real embedding model is verified by me.

An `xfail` is not a pass: it is a documented failure of the application.

## 3. Application bugs and limitations found

Every item below has a test whose assertion states the correct behaviour (strict xfail; it will fail loudly if fixed, telling you to remove the marker).

| ID | Severity | File / evidence test | What happens | Suggested minimal fix (not applied) |
|----|----------|----------------------|--------------|--------------------------------------|
| **BUG-1** | High (feature silently dead) | `engine/nodes/detect.py` — `test_detect_low_roi_issue_from_the_exact_insight_text_produced_by_observe`, `test_low_roi_campaign_becomes_a_detected_issue_end_to_end` | `"faible ROI" in i.lower()` can never be true (uppercase ROI vs lower-cased text). Observe reports the campaign, Detect never creates "Campagnes sous-performantes", so the LLM and playbooks never see it | compare with `"faible roi"` |
| **BUG-2** | High (visible in UI) | `csv_importer.py` / `ui/views.py:130` — `test_import_csv_returns_report_dict_used_by_the_ui` | `import_csv` returns `None`; UI does `result["report"]` → `TypeError`, caught and shown as an error banner **after** the data was written successfully; `last_import_report` never set | `return {"report": report, "accepted": validation["accepted"]}` |
| **BUG-7** | High (data loss) | `csv_importer.py` + `db.replace_*` — `test_header_only_csv_must_not_wipe_existing_data` | CSV with a header and no rows passes validation (0 rejects) and `replace_*` deletes every existing row of that entity for the company (8 → 0 in the test) | raise `ValueError` when `total_read == 0` |
| **BUG-3** | Medium | `cleaner.py` — `test_to_float_us_thousands_format` | `"1,234.56"` → `None` → silently `0.0` revenue. (`"36,081"` becomes 36.081, a decimal-comma assumption that may be wrong for your CSVs) | detect thousands separators, or make the locale explicit |
| **BUG-6** | Medium | `reason.py`, `recommend.py` — 2 tests | `confidence: null` or `priority: null` raises inside the try → the whole valid LLM answer is dropped and the deterministic fallback is used silently | default each field individually |
| **BUG-4** | Low–Medium | `reason.py` — `test_reason_missing_issue_title_should_not_link_to_all_issues` | missing `issue_title` → `'' in title` is True → hypothesis linked to every issue | skip matching when title is empty |
| **BUG-5** | Low | `company_store.py` — `test_store_data_dir_argument_is_honoured` | `CompanyStore(data_dir=...)` ignores the argument (DB path comes from `data.db.DB_PATH`) | remove the parameter or pass it through |
| LIMITATION-1 | Medium | `test_parse_date_dmy_with_month_name` | dates like `7-Sep-20` (used by `data/uploads/*client.csv`) are not parsed → `order_date = None` | add `%d-%b-%y` |
| LIMITATION-2 | Medium (design) | `test_plan_LIMITATION_...` (passes, characterisation) | `plan_node` links **all** LLM strategies to hypothesis #1, so `decide_node`'s "top-3 priority issues" filter mostly sees one issue | link by the strategy's own hypothesis ids |
| LIMITATION-3 | Low (design) | `test_recommend_LIMITATION_...` (passes) | every recommendation gets the same first strategy | map recommendation → strategy |
| LIMITATION-4 | Low | `test_LIMITATION_empty_company_...` (passes) | company with no data is flagged "Taux de réachat faible" (0 % repeat) | skip rate-based issues when there are no orders |
| DATA-1 | Data quality | `test_demo_orders_reference_existing_customers` | `company_001`: 350 customers (ids 101…) but only 4 orders, referencing `c1…c4` that do not exist; order KPIs (abandonment = 4 orders) and per-customer RFM are not linked to customers | align demo ids |

Observations without a test (judgement, not bugs): RFM "quintiles" are ranks among *distinct* values, not population quintiles; `datetime.utcnow()` is deprecated in Python 3.12; `data/uploads/` contains `bank-full.csv` imported as customers/orders/campaigns (wrong dataset type for those entities) and large CSVs (≈15 MB) that are committed to git.

## 4. What the passing tests do verify

* KPI formulas and RFM scoring against **hand-computed** values; all segment rules, thresholds and boundaries (0.25, 0.30, 0.7, 1.5, 15 %).
* CSV import end to end: mapping (LLM + fallback), cleaning, rejection ratio, atomic replace, scoping per company/entity.
* LLM resilience: valid / fenced / malformed / truncated JSON, timeouts and API errors at each stage → pipeline still completes with fallback recommendations; recommendations are always `pending_approval`.
* Context really flows detection → retrieval → reason → plan → recommend prompts.
* Multi-tenant isolation, unknown-company handling (400), partial errors (200), `max_recommendations`.
* The demo data in `data/sample_data/` migrates with exact row counts and runs through the full pipeline.

## 5. Not covered / untestable here

Streamlit UI (all of `ui/` except `errors.py`, plus `streamlit_app.py`), `main.py`, migration CLI flags (`--delete-json`), real uvicorn/CORS behaviour, `eleva-frontend` (no tracked files in the clone), concurrency, performance, security testing.

## 6. External services still unverified

Groq API (`openai/gpt-oss-120b`): real output quality, JSON-compliance rate, rate limits and latency. Chroma's real default embedding model (needs a download): relevance of retrieved playbooks. Both are covered only by the 4 optional live tests, **not run**.

## 7. Limits of this evaluation

Mocked tests do not prove the real agent works. The fake embedder proves mechanics, not relevance. Tests check functional correctness, **not** the usefulness or accuracy of generated advice (needs human review of real outputs, e.g. a rubric over 10–20 real answers). Business thresholds are tested as coded, not validated as correct. Synthetic data is tiny.
