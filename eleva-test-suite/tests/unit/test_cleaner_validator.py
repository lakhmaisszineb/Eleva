"""Unit tests: data/importer/cleaner.py, validator.py, report.py (pure functions)."""
import pytest

from data.importer import cleaner as cl
from data.importer.validator import validate_row, validate_dataset
from data.importer.report import build_import_report, format_report


# ----------------------------- _to_float / _to_int ---------------------------
@pytest.mark.parametrize("raw,expected", [
    ("12.5", 12.5), ("12,5", 12.5), (" 1 200 ", 1200.0), ("€45", 45.0),
    (7, 7.0), (3.5, 3.5), ("-4", -4.0), ("0", 0.0),
])
def test_to_float_valid(raw, expected):
    assert cl._to_float(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "abc", "--"])
def test_to_float_returns_none_for_empty_or_unparseable(raw):
    assert cl._to_float(raw) is None


def test_to_int_truncates_toward_zero():
    assert cl._to_int("3.9") == 3
    assert cl._to_int(None) is None


@pytest.mark.xfail(strict=True, reason="BUG-3: '1,234.56' (US thousands format) -> ',' becomes '.' -> '1.234.56' -> None")
def test_to_float_us_thousands_format():
    assert cl._to_float("1,234.56") == 1234.56


# ----------------------------------- dates -----------------------------------
@pytest.mark.parametrize("raw,expected", [
    ("2026-06-28", "2026-06-28"), ("28/06/2026", "2026-06-28"), ("28-06-2026", "2026-06-28"),
    ("2026/06/28", "2026-06-28"), ("28.06.2026", "2026-06-28"),
    ("2026-06-28T10:00:00", "2026-06-28"),
])
def test_parse_date_supported_formats(raw, expected):
    assert cl._parse_date(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "not a date", "31/02/2026"])
def test_parse_date_invalid_returns_none(raw):
    assert cl._parse_date(raw) is None


def test_parse_date_datetime_object():
    from datetime import datetime
    assert cl._parse_date(datetime(2026, 1, 2, 3)) == "2026-01-02"


@pytest.mark.xfail(strict=True, reason="LIMITATION-1: '7-Sep-20' (used by data/uploads/*client.csv) is not a supported date format")
def test_parse_date_dmy_with_month_name():
    assert cl._parse_date("7-Sep-20") == "2020-09-07"


# ---------------------------------- status -----------------------------------
@pytest.mark.parametrize("raw,expected", [
    ("Completed", "completed"), ("payé", "completed"), ("Livré", "completed"),
    ("CANCELED", "cancelled"), ("annulé", "cancelled"), ("Abandonné", "abandoned"),
    ("refunded", "refunded"), ("weird_status", "weird_status"),
])
def test_normalize_status(raw, expected):
    assert cl._normalize_status(raw) == expected


def test_normalize_status_empty():
    assert cl._normalize_status(None) is None
    assert cl._normalize_status("   ") is None


# ---------------------------------- clean_row --------------------------------
def test_clean_row_customers_defaults_and_types():
    out = cl.clean_row({"customer_id": " c1 ", "total_orders": "3", "total_spent": "10,5"}, "customers")
    assert out["customer_id"] == "c1"
    assert out["total_orders"] == 3 and out["total_spent"] == 10.5
    assert out["days_since_last_order"] is None and out["email"] is None


def test_clean_row_customers_missing_numbers_become_zero():
    out = cl.clean_row({"customer_id": "c1"}, "customers")
    assert out["total_orders"] == 0 and out["total_spent"] == 0.0


def test_clean_row_orders_unknown_status_when_missing():
    out = cl.clean_row({"order_id": "o1", "customer_id": "c1", "status": None}, "orders")
    assert out["status"] == "unknown"


def test_clean_row_orders_full():
    out = cl.clean_row({"order_id": "o1", "customer_id": "c1", "status": "payé",
                        "total": "89,50", "order_date": "28/06/2026"}, "orders")
    assert out == {"order_id": "o1", "customer_id": "c1", "status": "completed",
                   "total": 89.5, "order_date": "2026-06-28"}


def test_clean_row_campaigns():
    out = cl.clean_row({"campaign_id": "A", "name": "N", "type": "email",
                        "conversion_rate": "0,05", "roi": "2"}, "campaigns")
    assert out["conversion_rate"] == 0.05 and out["roi"] == 2.0


def test_clean_row_unknown_entity_returns_empty_dict():
    assert cl.clean_row({"a": 1}, "products") == {}


# --------------------------------- validator ---------------------------------
def test_validate_row_ok():
    assert validate_row({"customer_id": "c1", "total_spent": 5}, "customers") == (True, "")


@pytest.mark.parametrize("row", [{"customer_id": None}, {"customer_id": ""}, {}])
def test_validate_row_missing_required(row):
    ok, reason = validate_row(row, "customers")
    assert not ok and "customer_id" in reason


def test_validate_row_orders_requires_both_ids():
    assert not validate_row({"order_id": "o1", "customer_id": None}, "orders")[0]
    assert not validate_row({"order_id": None, "customer_id": "c1"}, "orders")[0]


def test_validate_row_negative_amounts_rejected():
    assert validate_row({"order_id": "o", "customer_id": "c", "total": -1}, "orders") == (False, "negative total")
    assert validate_row({"customer_id": "c", "total_spent": -0.01}, "customers") == (False, "negative total_spent")


def test_validate_row_zero_amount_is_valid_boundary():
    assert validate_row({"order_id": "o", "customer_id": "c", "total": 0}, "orders")[0]


def test_validate_dataset_ratio_boundary_is_strictly_greater():
    # 1 bad of 2 = 0.5 -> NOT too many (ratio > max is required)
    rows = [{"customer_id": "c1"}, {"customer_id": None}]
    res = validate_dataset(rows, "customers", max_reject_ratio=0.5)
    assert res["reject_ratio"] == 0.5 and res["too_many_rejects"] is False
    res = validate_dataset(rows, "customers", max_reject_ratio=0.49)
    assert res["too_many_rejects"] is True


def test_validate_dataset_empty_input_does_not_divide_by_zero():
    res = validate_dataset([], "customers")
    assert res["total_read"] == 0 and res["reject_ratio"] == 0 and not res["too_many_rejects"]


def test_validate_dataset_rejected_rows_carry_index_and_reason():
    res = validate_dataset([{"customer_id": "ok"}, {"customer_id": None}], "customers")
    assert res["rejected"][0]["row_index"] == 1
    assert "customer_id" in res["rejected"][0]["reason"]


# ----------------------------------- report ----------------------------------
def test_report_build_and_format():
    validation = validate_dataset([{"customer_id": "c1"}, {"customer_id": None}], "customers", 0.9)
    rep = build_import_report("customers", "f.csv",
                              {"source": "llm", "mapping": {"customer_id": "id"}, "ignored": ["x"]}, validation)
    assert rep["accepted_count"] == 1 and rep["rejected_count"] == 1
    assert rep["mapping_source"] == "llm" and rep["ignored_columns"] == ["x"]
    text = format_report(rep)
    assert "Accepted       : 1" in text and "Reject samples" in text
