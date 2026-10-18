# tests/

```
unit/          one file per area, pure logic, LLM + DB isolated      (python -m pytest tests/unit)
integration/   real components wired together on a temp DB/Chroma    (python -m pytest tests/integration)
live/          OPTIONAL, real Groq/embeddings, opt-in only           (ELEVA_LIVE_TESTS=1 ...)
fixtures/      tiny SYNTHETIC CSV files (see fixtures/README.md)
conftest.py    environment isolation + fake LLM + fake embeddings
helpers_eleva.py   FakeLLM + hand-computable synthetic company
```

Conventions
* Known application bugs are written as `@pytest.mark.xfail(strict=True, reason="BUG-n: ...")`: the assertion states the **correct** behaviour; it is never weakened.
* `LIMITATION-n` tests are characterisation tests: they pass and document current behaviour.
* Fake LLM stages: `mapper`, `reason`, `plan`, `recommend` — override with `fake_llm.set(stage, "text" | Exception)`.
* Full instructions: `../TESTING.md`; results and bug details: `../TEST_REPORT.md`.
