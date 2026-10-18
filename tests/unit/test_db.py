"""
Tests unitaires pour data/db.py
"""
import pytest
from data.db import (
    loads, dumps, split_core_extra,
    init_db, get_connection,
    CUSTOMER_CORE_FIELDS,
)


class TestSerialization:
    """Tests pour dumps/loads."""

    def test_dumps_dict(self):
        result = dumps({"a": 1, "b": "test"})
        assert result == '{"a": 1, "b": "test"}'

    def test_loads_valid_json(self):
        result = loads('{"a": 1, "b": "test"}')
        assert result == {"a": 1, "b": "test"}

    def test_loads_empty_returns_empty_dict(self):
        assert loads("") == {}
        assert loads(None) == {}


class TestSplitCoreExtra:
    """Tests pour split_core_extra."""

    def test_split_basic(self):
        row = {
            "customer_id": "C1",
            "total_orders": 5,
            "extra_field": "value",
        }
        core, extra = split_core_extra(row, ["customer_id", "total_orders"])
        assert core == {"customer_id": "C1", "total_orders": 5}
        assert extra == {"extra_field": "value"}

    def test_split_missing_core(self):
        row = {"customer_id": "C1"}
        core, extra = split_core_extra(row, ["customer_id", "total_orders"])
        assert core == {"customer_id": "C1", "total_orders": None}
        assert extra == {}


class TestInitDb:
    """Tests pour init_db."""

    def test_init_creates_database(self, tmp_path):
        """init_db crée une base si elle n'existe pas."""
        db_path = tmp_path / "test.db"
        result = init_db(db_path)
        assert db_path.exists()
        assert result["status"] == "new"

    def test_init_idempotent(self, tmp_path):
        """init_db appelé 2 fois ne plante pas."""
        db_path = tmp_path / "test.db"
        init_db(db_path)
        result = init_db(db_path)
        assert result["status"] == "ok"


class TestGetConnection:
    """Tests pour get_connection."""

    def test_connection_returns_sqlite(self, tmp_path):
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        assert conn is not None
        conn.close()