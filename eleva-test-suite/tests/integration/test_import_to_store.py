"""Integration: CSV file -> column mapping -> cleaning -> validation -> SQLite -> CompanyStore.
Real code for every component except the LLM (fake) and the DB (temp file)."""
import json
import shutil
from pathlib import Path

import pytest

from data.company_store import CompanyStore
from data.importer.csv_importer import import_csv
from helpers_eleva import seed_company

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def _rows(entity, company="co"):
    s = CompanyStore()
    return {"customers": s.get_customers, "orders": s.get_orders, "campaigns": s.get_campaigns}[entity](company)


def test_customers_csv_with_llm_mapping_is_persisted_and_retrievable(fake_llm):
    import_csv(FIX / "customers_clean.csv", "customers", "co")
    rows = {r["customer_id"]: r for r in _rows("customers")}
    assert set(rows) == {"c1", "c2", "c3"}
    assert rows["c1"]["total_spent"] == 150.5 and rows["c1"]["total_orders"] == 3 and rows["c1"]["segment"] == "VIP"
    assert rows["c2"]["churn_risk_score"] == 0.9 and rows["c2"]["email"] is None
    assert rows["c3"]["days_since_last_order"] is None and rows["c3"]["total_spent"] == 0.0
    assert fake_llm.calls_for("mapper")            # the LLM path really was used


def test_french_orders_csv_via_alias_fallback_when_llm_is_down(llm_down):
    import_csv(FIX / "orders_french_headers.csv", "orders", "co")
    o = {r["order_id"]: r for r in _rows("orders")}
    assert (o["CMD1"]["status"], o["CMD1"]["total"], o["CMD1"]["order_date"]) == ("completed", 89.5, "2026-06-28")
    assert (o["CMD2"]["status"], o["CMD2"]["total"], o["CMD2"]["order_date"]) == ("abandoned", 74.0, "2026-07-20")
    assert (o["CMD3"]["status"], o["CMD3"]["order_date"]) == ("cancelled", "2026-08-05")
    assert (o["CMD4"]["status"], o["CMD4"]["total"], o["CMD4"]["order_date"]) == ("completed", 20.25, "2026-09-01")


def test_llm_mapping_with_unusual_headers(fake_llm, tmp_path):
    f = tmp_path / "weird.csv"
    f.write_text("Ref Client;Dépenses\n".replace(";", ",") + "k1,10\nk2,20\n", encoding="utf-8")
    fake_llm.set("mapper", json.dumps({"mapping": {"customer_id": "Ref Client", "total_spent": "Dépenses"}, "ignored": []}))
    import_csv(f, "customers", "co")
    assert {(r["customer_id"], r["total_spent"]) for r in _rows("customers")} == {("k1", 10.0), ("k2", 20.0)}


def test_utf8_bom_header_is_handled(fake_llm, tmp_path):
    f = tmp_path / "bom.csv"
    f.write_bytes("\ufeffcustomer_id,total_spent\nb1,5\n".encode("utf-8"))
    import_csv(f, "customers", "co")
    assert [r["customer_id"] for r in _rows("customers")] == ["b1"]


def test_reject_ratio_exactly_at_limit_still_imports_valid_rows(fake_llm):
    import_csv(FIX / "orders_half_bad.csv", "orders", "co")       # 3 of 6 rejected = 0.5, limit is "> 0.5"
    assert sorted(r["order_id"] for r in _rows("orders")) == ["o1", "o3", "o5"]


def test_too_many_rejected_rows_aborts_and_writes_nothing(fake_llm):
    with pytest.raises(ValueError, match="Too many rejected rows"):
        import_csv(FIX / "orders_mostly_bad.csv", "orders", "co")
    assert _rows("orders") == []


def test_custom_reject_threshold(fake_llm):
    with pytest.raises(ValueError, match="Too many rejected rows"):
        import_csv(FIX / "orders_half_bad.csv", "orders", "co", max_reject_ratio=0.4)


def test_failed_import_does_not_destroy_previously_imported_data(fake_llm):
    import_csv(FIX / "customers_clean.csv", "customers", "co")
    with pytest.raises(ValueError):
        import_csv(FIX / "orders_mostly_bad.csv", "customers", "co")      # wrong entity -> mapping error
    assert len(_rows("customers")) == 3


def test_missing_required_column_raises_mapping_error(llm_down):
    with pytest.raises(ValueError, match="Column mapping incomplete"):
        import_csv(FIX / "customers_no_id_column.csv", "customers", "co")
    assert _rows("customers") == []


def test_empty_file_and_missing_file_errors(fake_llm, tmp_path):
    with pytest.raises(ValueError, match="no header"):
        import_csv(FIX / "empty.csv", "customers", "co")
    with pytest.raises(FileNotFoundError):
        import_csv(tmp_path / "absent.csv", "customers", "co")


def test_write_false_is_a_dry_run(fake_llm):
    import_csv(FIX / "customers_clean.csv", "customers", "co", write=False)
    assert _rows("customers") == []


def test_reimport_replaces_instead_of_appending(fake_llm):
    for _ in range(2):
        import_csv(FIX / "customers_clean.csv", "customers", "co")
    assert len(_rows("customers")) == 3


def test_import_is_scoped_to_one_company_and_one_entity(fake_llm):
    seed_company("other")
    before_c, before_o = len(_rows("customers", "other")), len(_rows("orders", "other"))
    import_csv(FIX / "customers_clean.csv", "customers", "co")
    assert len(_rows("customers", "other")) == before_c and len(_rows("orders", "other")) == before_o


@pytest.mark.xfail(strict=True, reason="BUG-2: import_csv() is documented to return {report,...} and ui/views.py reads result['report'], but it returns None -> the UI shows an error banner AFTER a successful import")
def test_import_csv_returns_report_dict_used_by_the_ui(fake_llm):
    result = import_csv(FIX / "customers_clean.csv", "customers", "co")
    assert result["report"]["accepted_count"] == 3 and result["report"]["total_read"] == 3


@pytest.mark.xfail(strict=True, reason="BUG-7: a header-only CSV is accepted (0 rows, 0 rejects) and replace_*() then DELETES every existing row of that entity for the company")
def test_header_only_csv_must_not_wipe_existing_data(fake_llm):
    seed_company("co")
    before = len(_rows("customers"))
    try:
        import_csv(FIX / "header_only.csv", "customers", "co")
    except ValueError:
        pass                                     # refusing the import would also be acceptable
    assert len(_rows("customers")) == before
