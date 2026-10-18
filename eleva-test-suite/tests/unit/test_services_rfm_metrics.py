"""Unit tests: services/rfm.py and services/metrics.py (pure, deterministic)."""
from datetime import datetime

import pytest

from services.metrics import compute_core_metrics
from services.rfm import compute_rfm, _rfm_segment
from helpers_eleva import (SYNTHETIC_CUSTOMERS, SYNTHETIC_ORDERS, SYNTHETIC_CAMPAIGNS, EXPECTED_KPIS)

REF = datetime(2026, 10, 1)


def _orders(cid, n, each, last):
    return [{"order_id": f"{cid}-{i}", "customer_id": cid, "status": "completed",
             "total": each, "order_date": last} for i in range(n)]


# ================================ METRICS ====================================
def test_metrics_match_hand_computed_values():
    m = compute_core_metrics(SYNTHETIC_CUSTOMERS, SYNTHETIC_ORDERS, SYNTHETIC_CAMPAIGNS)
    assert m == EXPECTED_KPIS


def test_metrics_all_empty_inputs_are_zero_not_errors():
    m = compute_core_metrics([], [], [])
    assert m["total_customers"] == 0 and m["average_order_value"] == 0.0
    assert m["cart_abandonment_rate"] == 0.0 and m["approx_clv"] == 0.0
    assert m["repeat_purchase_rate"] == 0.0 and m["low_roi_campaign_names"] == []


def test_metrics_aov_only_counts_completed_orders():
    orders = [{"status": "completed", "total": 10}, {"status": "abandoned", "total": 1000}]
    assert compute_core_metrics([], orders, [])["average_order_value"] == 10.0


def test_metrics_none_and_garbage_values_do_not_crash():
    customers = [{"customer_id": "c", "total_spent": None, "churn_risk_score": "abc"}]
    orders = [{"status": "completed", "total": None, "customer_id": "c"},
              {"status": "completed", "total": "x", "customer_id": "c"}]
    campaigns = [{"name": None, "roi": None}, {"name": "ok", "roi": "bad"}]
    m = compute_core_metrics(customers, orders, campaigns)
    assert m["average_order_value"] == 0.0 and m["approx_clv"] == 0.0
    assert m["high_churn_risk_count"] == 0


def test_metrics_churn_threshold_is_inclusive_at_0_7():
    cs = [{"churn_risk_score": 0.7}, {"churn_risk_score": 0.6999}]
    assert compute_core_metrics(cs, [], [])["high_churn_risk_count"] == 1


def test_metrics_roi_threshold_exclusive_at_1_5():
    cs = [{"name": "x", "roi": 1.5}, {"name": "y", "roi": 1.49}, {"name": None, "roi": 0}]
    m = compute_core_metrics([], [], cs)
    assert m["low_roi_campaigns_count"] == 2 and m["low_roi_campaign_names"] == ["y", "Unknown"]


def test_metrics_repeat_rate_single_buyer_with_two_orders():
    orders = _orders("c1", 2, 10, "2026-01-01") + _orders("c2", 1, 10, "2026-01-01")
    assert compute_core_metrics([], orders, [])["repeat_purchase_rate"] == 0.5


def test_metrics_orders_without_customer_id_are_ignored_for_repeat_rate():
    orders = [{"status": "completed", "total": 1, "customer_id": None}] * 3
    assert compute_core_metrics([], orders, [])["repeat_purchase_rate"] == 0.0


# ================================== RFM ======================================
def test_rfm_empty_customers_returns_empty_list():
    assert compute_rfm([], [], REF) == []


def test_rfm_three_customer_hand_computed_scores_and_segments():
    customers = [{"customer_id": x} for x in "ABC"]
    orders = (_orders("A", 3, 100, "2026-09-30") + _orders("B", 2, 50, "2026-08-01")
              + _orders("C", 1, 10, "2026-01-01"))
    res = {r["customer_id"]: r for r in compute_rfm(customers, orders, REF)}
    # recency days: A=1, B=61, C=273 ; frequency 3/2/1 ; monetary 300/100/10
    assert (res["A"]["recency_days"], res["B"]["recency_days"], res["C"]["recency_days"]) == (1, 61, 273)
    assert (res["A"]["r_score"], res["A"]["f_score"], res["A"]["m_score"]) == (5, 5, 5)
    assert (res["B"]["r_score"], res["B"]["f_score"], res["B"]["m_score"]) == (3, 3, 3)
    assert (res["C"]["r_score"], res["C"]["f_score"], res["C"]["m_score"]) == (1, 1, 1)
    assert [res[k]["rfm_segment"] for k in "ABC"] == ["Champions", "Loyal", "Lost / Churned"]
    assert res["A"]["monetary"] == 300.0


def test_rfm_more_recent_is_always_a_higher_r_score():
    customers = [{"customer_id": "new"}, {"customer_id": "old"}]
    orders = _orders("new", 1, 5, "2026-09-29") + _orders("old", 1, 5, "2025-01-01")
    res = {r["customer_id"]: r for r in compute_rfm(customers, orders, REF)}
    assert res["new"]["r_score"] > res["old"]["r_score"]


def test_rfm_single_customer_gets_neutral_scores():
    res = compute_rfm([{"customer_id": "solo"}], _orders("solo", 1, 10, "2026-09-01"), REF)
    assert (res[0]["r_score"], res[0]["f_score"], res[0]["m_score"]) == (3, 3, 3)
    assert res[0]["rfm_segment"] == "Loyal"


def test_rfm_ignores_non_completed_orders():
    customers = [{"customer_id": "c", "total_orders": 0, "total_spent": 0}]
    orders = [{"customer_id": "c", "status": "abandoned", "total": 999, "order_date": "2026-09-30"}]
    r = compute_rfm(customers, orders, REF)[0]
    assert r["frequency"] == 0 and r["monetary"] == 0.0


def test_rfm_falls_back_to_customer_columns_when_no_orders():
    customers = [{"customer_id": "c", "total_orders": 4, "total_spent": 99.5, "days_since_last_order": 12}]
    r = compute_rfm(customers, [], REF)[0]
    assert (r["recency_days"], r["frequency"], r["monetary"]) == (12, 4, 99.5)


def test_rfm_null_fields_after_csv_import_are_safe():
    customers = [{"customer_id": "c", "total_orders": None, "total_spent": None, "days_since_last_order": None}]
    r = compute_rfm(customers, [], REF)[0]
    assert (r["recency_days"], r["frequency"], r["monetary"]) == (999, 0, 0.0)


def test_rfm_unparseable_order_date_is_skipped_not_fatal():
    customers = [{"customer_id": "c", "days_since_last_order": 7}]
    orders = [{"customer_id": "c", "status": "completed", "total": 5, "order_date": "garbage"}]
    r = compute_rfm(customers, orders, REF)[0]
    assert r["recency_days"] == 7 and r["frequency"] == 1


def test_rfm_future_order_date_clamps_recency_to_zero():
    r = compute_rfm([{"customer_id": "c"}], _orders("c", 1, 5, "2027-01-01"), REF)[0]
    assert r["recency_days"] == 0


def test_rfm_is_deterministic():
    customers = [{"customer_id": str(i)} for i in range(6)]
    orders = [o for i in range(6) for o in _orders(str(i), i + 1, 10 * (i + 1), f"2026-0{(i % 8) + 1}-15")]
    assert compute_rfm(customers, orders, REF) == compute_rfm(customers, orders, REF)


def test_rfm_scores_always_within_1_to_5():
    customers = [{"customer_id": str(i)} for i in range(12)]
    orders = [o for i in range(12) for o in _orders(str(i), (i % 4) + 1, 5 + i, f"2026-{(i % 9) + 1:02d}-10")]
    for r in compute_rfm(customers, orders, REF):
        assert all(1 <= r[k] <= 5 for k in ("r_score", "f_score", "m_score"))


def test_rfm_timezone_aware_reference_date_is_accepted():
    from datetime import timezone
    r = compute_rfm([{"customer_id": "c"}], _orders("c", 1, 5, "2026-09-30"), datetime(2026, 10, 1, tzinfo=timezone.utc))[0]
    assert r["recency_days"] == 1


# ------------------------- segment decision table ----------------------------
@pytest.mark.parametrize("r,f,m,expected", [
    (5, 5, 5, "Champions"), (4, 4, 4, "Champions"),
    (3, 3, 3, "Loyal"), (4, 3, 3, "Loyal"),
    (4, 1, 1, "New / Promising"), (5, 2, 5, "New / Promising"),
    (2, 3, 1, "At Risk"), (1, 5, 5, "At Risk"),
    (2, 2, 3, "Hibernating (high value)"), (1, 1, 5, "Hibernating (high value)"),
    (2, 2, 2, "Lost / Churned"), (1, 1, 1, "Lost / Churned"),
    (3, 2, 1, "Potential Loyalist"),
])
def test_rfm_segment_rules(r, f, m, expected):
    assert _rfm_segment(r, f, m) == expected


def test_rfm_segment_need_attention_is_the_fallback_branch():
    # r>=3 forces f>=3 branches or f<=2; (3,3,2) fails Loyal (m<3), New (f>2), AtRisk(r>2), Potential (f>2)
    assert _rfm_segment(3, 3, 2) == "Need Attention"
