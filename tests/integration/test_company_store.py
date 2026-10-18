"""
Tests d'intégration pour CompanyStore.
"""
import pytest
from data.company_store import CompanyStore


class TestCompanyStore:
    """Tests de CompanyStore avec base de test."""

    def test_get_company_context(self, test_db):
        store = CompanyStore(data_dir=test_db.parent)
        ctx = store.get_company_context("test_company")
        assert ctx.name == "Test Co"
        assert ctx.industry == "e-commerce"

    def test_get_customers(self, test_db):
        store = CompanyStore(data_dir=test_db.parent)
        customers = store.get_customers("test_company")
        assert len(customers) == 2
        assert customers[0]["customer_id"] == "C001"

    def test_get_orders(self, test_db):
        store = CompanyStore(data_dir=test_db.parent)
        orders = store.get_orders("test_company")
        assert len(orders) == 2

    def test_get_nonexistent_company(self, test_db):
        store = CompanyStore(data_dir=test_db.parent)
        with pytest.raises(Exception):
            store.get_company_context("nonexistent")

    def test_list_available_companies(self, test_db):
        store = CompanyStore(data_dir=test_db.parent)
        companies = store.list_available_companies()
        assert "test_company" in companies