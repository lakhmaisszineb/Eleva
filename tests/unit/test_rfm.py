"""
Tests unitaires pour services/rfm.py
"""
from datetime import datetime, timezone
from services.rfm import compute_rfm, _rfm_segment


class TestRFMSegment:
    """Tests pour _rfm_segment (règles de segmentation)."""

    def test_champions(self):
        assert _rfm_segment(5, 5, 5) == "Champions"
        assert _rfm_segment(4, 4, 4) == "Champions"

    def test_loyal(self):
        assert _rfm_segment(3, 3, 3) == "Loyal"

    def test_at_risk(self):
        assert _rfm_segment(1, 4, 2) == "At Risk"
        assert _rfm_segment(2, 3, 2) == "At Risk"

    def test_lost_churned(self):
        assert _rfm_segment(1, 1, 1) == "Lost / Churned"
        assert _rfm_segment(2, 2, 2) == "Lost / Churned"

    def test_new_promising(self):
        assert _rfm_segment(4, 1, 1) == "New / Promising"


class TestComputeRFM:
    """Tests pour compute_rfm."""

    def test_empty_data(self):
        """Listes vides → liste vide."""
        result = compute_rfm([], [])
        assert result == []

    def test_single_customer_single_order(self):
        """Un client, une commande récente → segment cohérent."""
        customers = [{"customer_id": "C1", "total_orders": 1, "total_spent": 100.0}]
        orders = [
            {
                "customer_id": "C1",
                "status": "completed",
                "total": 100.0,
                "order_date": "2026-10-01",
            }
        ]
        result = compute_rfm(customers, orders)
        assert len(result) == 1
        assert result[0]["customer_id"] == "C1"
        assert result[0]["frequency"] == 1
        assert result[0]["monetary"] == 100.0

    def test_champion_customer(self):
        """Client avec commandes récentes et fréquentes → Champions."""
        customers = [{"customer_id": "C1"}]
        orders = [
            {"customer_id": "C1", "status": "completed", "total": 100.0, "order_date": "2026-10-01"},
            {"customer_id": "C1", "status": "completed", "total": 100.0, "order_date": "2026-10-05"},
            {"customer_id": "C1", "status": "completed", "total": 100.0, "order_date": "2026-10-08"},
        ]
        result = compute_rfm(customers, orders)
        assert result[0]["rfm_segment"] in ["Champions", "Loyal"]

    def test_abandoned_orders_ignored(self):
        """Les commandes abandonnées ne comptent pas."""
        customers = [{"customer_id": "C1"}]
        orders = [
            {"customer_id": "C1", "status": "abandoned", "total": 100.0, "order_date": "2026-10-01"},
        ]
        result = compute_rfm(customers, orders)
        # Pas de commande complétée → frequency = 0 (ou valeur du customer)
        assert result[0]["frequency"] == 0

    def test_null_customer_id_ignored(self):
        """Les commandes sans customer_id sont ignorées."""
        customers = [{"customer_id": "C1"}]
        orders = [
            {"customer_id": None, "status": "completed", "total": 100.0, "order_date": "2026-10-01"},
            {"customer_id": "C1", "status": "completed", "total": 50.0, "order_date": "2026-10-02"},
        ]
        result = compute_rfm(customers, orders)
        assert len(result) == 1
        assert result[0]["frequency"] == 1