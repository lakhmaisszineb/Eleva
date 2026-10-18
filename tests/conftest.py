"""
Fixtures partagées pour tous les tests.
"""
import pytest
from pathlib import Path
import pytest
from config import settings

@pytest.fixture(autouse=True)
def fix_test_paths(monkeypatch):
    """Force les tests à utiliser le vrai dossier knowledge."""
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    monkeypatch.setattr(settings, "knowledge_dir", project_root / "knowledge" / "playbooks")


@pytest.fixture
def sample_customers():
    """Données de test : clients."""
    return [
        {
            "customer_id": "C001",
            "total_orders": 5,
            "total_spent": 500.0,
            "days_since_last_order": 10,
            "churn_risk_score": 0.2,
            "email": "alice@test.com",
            "segment": "Champions",
        },
        {
            "customer_id": "C002",
            "total_orders": 1,
            "total_spent": 50.0,
            "days_since_last_order": 120,
            "churn_risk_score": 0.85,
            "email": "bob@test.com",
            "segment": "At Risk",
        },
        {
            "customer_id": "C003",
            "total_orders": 0,
            "total_spent": 0.0,
            "days_since_last_order": 200,
            "churn_risk_score": 0.9,
            "email": "carol@test.com",
            "segment": "Lost / Churned",
        },
    ]


@pytest.fixture
def sample_orders():
    """Données de test : commandes."""
    return [
        {
            "order_id": "O001",
            "customer_id": "C001",
            "status": "completed",
            "total": 100.0,
            "order_date": "2026-09-15",
        },
        {
            "order_id": "O002",
            "customer_id": "C001",
            "status": "completed",
            "total": 150.0,
            "order_date": "2026-09-25",
        },
        {
            "order_id": "O003",
            "customer_id": "C002",
            "status": "abandoned",
            "total": 50.0,
            "order_date": "2026-08-01",
        },
        {
            "order_id": "O004",
            "customer_id": "C002",
            "status": "completed",
            "total": 50.0,
            "order_date": "2026-06-01",
        },
    ]


@pytest.fixture
def sample_campaigns():
    """Données de test : campagnes."""
    return [
        {
            "campaign_id": "CAMP001",
            "name": "Promo Été",
            "type": "email",
            "conversion_rate": 0.05,
            "roi": 2.5,
        },
        {
            "campaign_id": "CAMP002",
            "name": "Black Friday",
            "type": "ads",
            "conversion_rate": 0.02,
            "roi": 1.2,
        },
    ]


@pytest.fixture
def test_db(tmp_path):
    """
    Crée une base SQLite temporaire avec des données de test.
    """
    from data.db import init_db, get_connection, upsert_profile, replace_customers, replace_orders

    db_path = tmp_path / "eleva.db"
    init_db(db_path)
    conn = get_connection(db_path)

    # Profil entreprise
    upsert_profile(conn, "test_company", {
        "name": "Test Co",
        "industry": "e-commerce",
        "description": "Entreprise de test",
        "current_focus": "fidélisation",
        "goals": ["réduire le churn"],
        "metadata": {},
    })

    # Clients
    replace_customers(conn, "test_company", [
        {
            "customer_id": "C001",
            "total_orders": 5,
            "total_spent": 500.0,
            "days_since_last_order": 10,
            "churn_risk_score": 0.2,
            "email": "alice@test.com",
            "segment": "Champions",
        },
        {
            "customer_id": "C002",
            "total_orders": 1,
            "total_spent": 50.0,
            "days_since_last_order": 120,
            "churn_risk_score": 0.85,
            "email": "bob@test.com",
            "segment": "At Risk",
        },
    ])

    # Commandes
    replace_orders(conn, "test_company", [
        {
            "order_id": "O001",
            "customer_id": "C001",
            "status": "completed",
            "total": 100.0,
            "order_date": "2026-09-15",
        },
        {
            "order_id": "O002",
            "customer_id": "C002",
            "status": "abandoned",
            "total": 50.0,
            "order_date": "2026-08-01",
        },
    ])

    conn.commit()
    conn.close()

    yield db_path