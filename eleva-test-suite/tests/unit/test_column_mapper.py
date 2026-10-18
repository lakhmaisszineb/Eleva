"""Unit tests: data/importer/column_mapper.py (LLM replaced by a controlled fake)."""
import json
import pytest

from data.importer import column_mapper as cm


# ------------------------------ _extract_json --------------------------------
def test_extract_json_plain():
    assert cm._extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced_with_language_tag():
    assert cm._extract_json('Voici:\n```json\n{"a": 1}\n```\nmerci') == {"a": 1}


def test_extract_json_fenced_without_language_tag():
    assert cm._extract_json('```\n{"a": 2}\n```') == {"a": 2}


def test_extract_json_garbage_raises():
    with pytest.raises(json.JSONDecodeError):
        cm._extract_json("pas du json")


# ------------------------------ alias fallback -------------------------------
def test_alias_fallback_matches_french_and_punctuation():
    m = cm._alias_fallback(["ID Client", "Statut", "Montant", "Date_Commande", "id_commande"], "orders")
    assert m == {"order_id": "id_commande", "customer_id": "ID Client", "status": "Statut",
                 "total": "Montant", "order_date": "Date_Commande"}


def test_alias_fallback_unmatched_columns_are_none():
    m = cm._alias_fallback(["foo", "bar"], "customers")
    assert all(v is None for v in m.values())


def test_alias_fallback_known_ambiguity_generic_id_maps_to_customer_id():
    # 'id' is an alias of customer_id, so on a customers file a generic 'id' is accepted.
    assert cm._alias_fallback(["id"], "customers")["customer_id"] == "id"


# ------------------------------ map_columns_with_llm -------------------------
def test_map_unknown_entity_raises_value_error():
    with pytest.raises(ValueError, match="Unknown entity"):
        cm.map_columns_with_llm(["a"], "products")


def test_map_valid_llm_response(fake_llm):
    fake_llm.set("mapper", json.dumps({"mapping": {"customer_id": "Client", "email": "Mail"}, "ignored": ["Pays"]}))
    res = cm.map_columns_with_llm(["Client", "Mail", "Pays"], "customers")
    assert res["source"] == "llm"
    assert res["mapping"]["customer_id"] == "Client" and res["mapping"]["email"] == "Mail"
    assert res["mapping"]["total_spent"] is None          # missing key -> None
    assert res["ignored"] == ["Pays"]
    assert set(res["mapping"]) == set(cm.SCHEMA["customers"])


def test_map_llm_hallucinated_source_column_is_nulled(fake_llm):
    fake_llm.set("mapper", json.dumps({"mapping": {"customer_id": "does_not_exist"}, "ignored": []}))
    res = cm.map_columns_with_llm(["Client"], "customers")
    assert res["source"] == "llm" and res["mapping"]["customer_id"] is None


def test_map_llm_unknown_target_fields_are_dropped(fake_llm):
    fake_llm.set("mapper", json.dumps({"mapping": {"customer_id": "Client", "hack": "Client"}, "ignored": ["ghost"]}))
    res = cm.map_columns_with_llm(["Client"], "customers")
    assert "hack" not in res["mapping"] and res["ignored"] == []   # 'ghost' is not a real column


def test_map_llm_fenced_json_is_accepted(fake_llm):
    fake_llm.set("mapper", '```json\n{"mapping": {"customer_id": "Client"}, "ignored": []}\n```')
    assert cm.map_columns_with_llm(["Client"], "customers")["mapping"]["customer_id"] == "Client"


@pytest.mark.parametrize("bad", ["not json at all", "", "[1, 2, 3]", '{"mapping": "oops"}'])
def test_map_malformed_llm_output_falls_back_to_aliases(fake_llm, bad):
    fake_llm.set("mapper", bad)
    res = cm.map_columns_with_llm(["customer_id", "Total_Spent"], "customers")
    assert res["source"] == "alias_fallback"
    assert res["mapping"]["customer_id"] == "customer_id"
    assert res["mapping"]["total_spent"] == "Total_Spent"


@pytest.mark.parametrize("exc", [TimeoutError("timeout"), ConnectionError("api down"), ValueError("GROQ_API_KEY missing")])
def test_map_llm_errors_fall_back_to_aliases(fake_llm, exc):
    fake_llm.set("mapper", exc)
    res = cm.map_columns_with_llm(["customer_id"], "customers")
    assert res["source"] == "alias_fallback" and res["mapping"]["customer_id"] == "customer_id"


def test_map_prompt_contains_columns_and_required_fields(fake_llm):
    cm.map_columns_with_llm(["Client", "Mail"], "customers")
    user = fake_llm.calls_for("mapper")[0]["user"]
    assert "- Client" in user and "- Mail" in user
    assert "Champs obligatoires:\ncustomer_id" in user


# ------------------------------ validate_mapping -----------------------------
def test_validate_mapping_reports_each_missing_required_field():
    errs = cm.validate_mapping({"order_id": None, "customer_id": "c"}, "orders")
    assert errs == ["Required field 'order_id' could not be mapped."]


def test_validate_mapping_ok():
    assert cm.validate_mapping({"customer_id": "id"}, "customers") == []
