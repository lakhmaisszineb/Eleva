"""
Tests unitaires pour services/metrics.py
"""
from services.metrics import compute_core_metrics, _safe_float, _safe_int


class TestSafeFloat:
    """Tests pour _safe_float."""

    def test_valid_float(self):
        assert _safe_float(3.14) == 3.14

    def test_valid_string(self):
        assert _safe_float("42.5") == 42.5

    def test_none_returns_default(self):
        assert _safe_float(None) == 0.0

    def test_empty_string_returns_default(self):
        assert _safe_float("") == 0.0

    def test_invalid_string_returns_default(self):
        assert _safe_float("abc") == 0.0

    def test_custom_default(self):
        assert _safe_float(None, default=99.0) == 99.0


class TestSafeInt:
    """Tests pour _safe_int."""

    def test_valid_int(self):
        assert _safe_int(42) == 42

    def test_string_int(self):
        assert _safe_int("42") == 42

    def test_float_string(self):
        assert _safe_int("42.9") == 42  # tronqué

    def test_none_returns_default(self):
        assert _safe_int(None) == 0


class TestComputeCoreMetrics:
    """Tests pour compute_core_metrics."""

    def test_empty_data(self):
        """Listes vides → métriques à zéro."""
        result = compute_core_metrics([], [], [])
        assert result["total_customers"] == 0
        assert result["total_orders"] == 0
        assert result["completed_orders"] == 0
        assert result["abandoned_orders"] == 0
        assert result["cart_abandonment_rate"] == 0.0
        assert result["average_order_value"] == 0.0

    def test_basic_metrics(self, sample_customers, sample_orders, sample_campaigns):
        """Données de test → métriques cohérentes."""
        result = compute_core_metrics(sample_customers, sample_orders, sample_campaigns)

        assert result["total_customers"] == 3
        assert result["total_orders"] == 4
        assert result["completed_orders"] == 3   # O001, O002, O004
        assert result["abandoned_orders"] == 1    # O003

        # Taux d'abandon = 1/4 = 0.25
        assert result["cart_abandonment_rate"] == 0.25

        # AOV = (100 + 150 + 50) / 3 = 100.0
        assert result["average_order_value"] == 100.0

        # CLV = (500 + 50 + 0) / 3 ≈ 183.33
        assert result["approx_clv"] == 183.33

        # Clients à haut risque churn (≥ 0.7) : C002 (0.85), C003 (0.9) = 2
        assert result["high_churn_risk_count"] == 2

        # Campagnes faible ROI (< 1.5) : CAMP002 (1.2) = 1
        assert result["low_roi_campaigns_count"] == 1

    def test_cart_abandonment_rate(self):
        """Taux d'abandon = abandons / total."""
        orders = [
            {"status": "completed", "total": 100.0},
            {"status": "abandoned", "total": 50.0},
            {"status": "abandoned", "total": 30.0},
            {"status": "completed", "total": 200.0},
        ]
        result = compute_core_metrics([], orders, [])
        assert result["cart_abandonment_rate"] == 0.5

    def test_repeat_purchase_rate(self):
        """Taux de réachat = clients avec ≥2 commandes / total clients avec commandes."""
        orders = [
            {"status": "completed", "total": 10.0, "customer_id": "C1"},
            {"status": "completed", "total": 10.0, "customer_id": "C1"},
            {"status": "completed", "total": 10.0, "customer_id": "C2"},
        ]
        result = compute_core_metrics([], orders, [])
        # C1 a 2 commandes, C2 a 1 → 1 repeat / 2 clients = 0.5
        assert result["repeat_purchase_rate"] == 0.5

    def test_no_completed_orders(self):
        """Aucune commande complétée → AOV = 0."""
        orders = [{"status": "abandoned", "total": 50.0}]
        result = compute_core_metrics([], orders, [])
        assert result["average_order_value"] == 0.0