"""Unit tests: data/db.py, data/company_store.py, data/company_admin.py, data/catalog.py.
All run against a throw-away SQLite file (see conftest.isolated_db)."""
import json
import sqlite3
from pathlib import Path

import pytest

import data.db as db
from core.exceptions import DataNotFoundError
from data.company_admin import company_exists, create_company
from data.company_store import CompanyStore
from helpers_eleva import seed_company, SYNTHETIC_CUSTOMERS


# ---------------------------------- safety -----------------------------------
def test_tests_never_use_the_real_development_database(isolated_db):
    real = Path(__file__).resolve().parents[2] / "data" / "sample_data" / "eleva.db"
    assert Path(db.DB_PATH).resolve() != real.resolve()
    assert Path(db.DB_PATH).parent == isolated_db.parent


# ----------------------------------- db.py -----------------------------------
def _tables(path):
    c = sqlite3.connect(path)
    try:
        return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        c.close()


def test_init_db_creates_schema_and_is_idempotent(isolated_db):
    db.init_db(); db.init_db()
    assert {"company_profile", "customers", "orders", "campaigns"} <= _tables(isolated_db)


def test_get_connection_creates_parent_dir_and_row_factory(tmp_path):
    path = tmp_path / "nested" / "dir" / "x.db"
    conn = db.get_connection(path)
    try:
        assert path.parent.exists() and conn.row_factory is sqlite3.Row
    finally:
        conn.close()


def test_dumps_loads_roundtrip_keeps_unicode():
    s = db.dumps({"a": "é à ñ"})
    assert "é" in s and db.loads(s) == {"a": "é à ñ"}


@pytest.mark.parametrize("empty", [None, ""])
def test_loads_empty_returns_empty_dict(empty):
    assert db.loads(empty) == {}


def test_split_core_extra():
    core, extra = db.split_core_extra({"customer_id": "c", "foo": 1}, db.CUSTOMER_CORE_FIELDS)
    assert core["customer_id"] == "c" and core["email"] is None
    assert extra == {"foo": 1}


def test_replace_customers_replaces_only_that_company():
    conn = db.get_connection()
    db.replace_customers(conn, "A", [{"customer_id": "a1"}, {"customer_id": "a2"}])
    db.replace_customers(conn, "B", [{"customer_id": "b1"}])
    n = db.replace_customers(conn, "A", [{"customer_id": "a3"}])     # replace, not append
    conn.commit()
    assert n == 1
    rows = conn.execute("SELECT company_id, customer_id FROM customers ORDER BY id").fetchall()
    conn.close()
    assert [(r[0], r[1]) for r in rows] == [("B", "b1"), ("A", "a3")]


def test_replace_with_empty_list_deletes_existing_rows():
    conn = db.get_connection()
    db.replace_orders(conn, "A", [{"order_id": "o1", "customer_id": "c"}])
    db.replace_orders(conn, "A", [])
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
    conn.close()


def test_extra_fields_are_preserved_in_extra_json():
    conn = db.get_connection()
    db.replace_campaigns(conn, "A", [{"campaign_id": "1", "name": "n", "channel": "sms"}])
    conn.commit()
    row = conn.execute("SELECT extra_json FROM campaigns").fetchone()
    conn.close()
    assert json.loads(row[0]) == {"channel": "sms"}


def test_upsert_profile_inserts_then_updates_without_duplicates():
    conn = db.get_connection()
    db.upsert_profile(conn, "A", {"name": "N1", "industry": "beauty"})
    db.upsert_profile(conn, "A", {"name": "N2", "industry": "food", "goals": ["g"]})
    conn.commit()
    rows = conn.execute("SELECT * FROM company_profile").fetchall()
    conn.close()
    assert len(rows) == 1 and rows[0]["name"] == "N2" and json.loads(rows[0]["goals_json"]) == ["g"]


def test_upsert_profile_requires_name_and_industry():
    conn = db.get_connection()
    with pytest.raises(KeyError):
        db.upsert_profile(conn, "A", {"name": "only name"})
    conn.close()


def test_replace_by_entity_registry():
    assert set(db.REPLACE_BY_ENTITY) == {"customers", "orders", "campaigns"}


# ------------------------------- company_store -------------------------------
def test_store_company_context_roundtrip():
    seed_company("co1")
    ctx = CompanyStore().get_company_context("co1")
    assert ctx.company_id == "co1" and ctx.industry == "fashion"
    assert ctx.goals == ["Reduce churn", "Reduce cart abandonment"]
    assert ctx.metadata == {"currency": "EUR"}


def test_store_unknown_company_raises_data_not_found():
    with pytest.raises(DataNotFoundError, match="nope"):
        CompanyStore().get_company_context("nope")


def test_store_returns_empty_lists_for_company_without_data():
    s = CompanyStore()
    assert s.get_customers("ghost") == [] and s.get_orders("ghost") == [] and s.get_campaigns("ghost") == []


def test_store_customers_roundtrip_core_and_extra():
    conn = db.get_connection()
    db.replace_customers(conn, "co", [{"customer_id": "c1", "total_spent": 5.5, "country": "MA"}])
    conn.commit(); conn.close()
    (row,) = CompanyStore().get_customers("co")
    assert row["customer_id"] == "c1" and row["total_spent"] == 5.5 and row["country"] == "MA"


def test_store_multi_tenant_isolation():
    seed_company("A"); seed_company("B", customers=SYNTHETIC_CUSTOMERS[:2])
    s = CompanyStore()
    assert len(s.get_customers("A")) == 8 and len(s.get_customers("B")) == 2


def test_store_list_available_companies():
    seed_company("A"); seed_company("B")
    assert sorted(CompanyStore().list_available_companies()) == ["A", "B"]


@pytest.mark.xfail(strict=True, reason="BUG-5: CompanyStore(data_dir=...) accepts a data_dir but ignores it (always uses data.db.DB_PATH)")
def test_store_data_dir_argument_is_honoured(tmp_path):
    other = tmp_path / "other_dir"            # does not exist yet
    CompanyStore(data_dir=other)              # a store pointed at data_dir should create/use <data_dir>/eleva.db
    assert (other / "eleva.db").exists()


# ------------------------------- company_admin -------------------------------
def test_create_company_then_exists():
    assert not company_exists("new_co")
    create_company("new_co", "New Co", "beauty", goals=["g"])
    assert company_exists("new_co")
    assert CompanyStore().get_company_context("new_co").goals == ["g"]


def test_create_company_duplicate_is_rejected_without_overwrite():
    create_company("dup", "First", "beauty")
    with pytest.raises(ValueError, match="existe déjà"):
        create_company("dup", "Second", "food")
    assert CompanyStore().get_company_context("dup").name == "First"


@pytest.mark.parametrize("bad", ["", "   ", None])
def test_create_company_empty_id_rejected(bad):
    with pytest.raises(ValueError):
        create_company(bad, "N", "i")


def test_create_company_strips_whitespace_for_the_duplicate_check():
    create_company("  padded  ", "N", "i")
    assert company_exists("padded")


# --------------------------------- catalog -----------------------------------
def test_catalog_list_companies_scans_json_dirs(tmp_path, monkeypatch):
    from config import settings
    import data.catalog as cat

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    (tmp_path / "co_a").mkdir()
    (tmp_path / "co_a" / "customers.json").write_text(json.dumps([{"x": 1}, {"x": 2}]))
    (tmp_path / "co_a" / "profile.json").write_text(json.dumps({"name": "Alpha"}))
    (tmp_path / "co_b").mkdir()
    (tmp_path / "co_b" / "orders.json").write_text("{not json")
    (tmp_path / "stray_file.txt").write_text("x")

    out = {c["company_id"]: c for c in cat.list_companies()}
    assert set(out) == {"co_a", "co_b"}
    assert out["co_a"]["name"] == "Alpha" and out["co_a"]["counts"]["customers"] == 2
    assert out["co_a"]["has_customers"] and not out["co_a"]["has_orders"]
    assert out["co_b"]["counts"]["orders"] == "?" and out["co_b"]["name"] == "co_b"


def test_catalog_missing_data_dir_returns_empty(tmp_path, monkeypatch):
    from config import settings
    import data.catalog as cat
    monkeypatch.setattr(settings, "data_dir", tmp_path / "missing")
    assert cat.list_companies() == []
