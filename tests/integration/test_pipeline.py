"""
Tests d'intégration pour le pipeline complet.
"""

from engine.decision_engine import DecisionEngine
from core.models import AnalysisRequest


class TestFullPipeline:
    """Tests du pipeline complet."""

    def test_pipeline_with_valid_company(self, test_db, monkeypatch):
        """Pipeline complet avec données de test."""

        from config import settings
        import engine.nodes.understand as understand_module
        from data.company_store import CompanyStore

        monkeypatch.setattr(settings, "data_dir", test_db.parent)

        monkeypatch.setattr(
            understand_module,
            "CompanyStore",
            lambda: CompanyStore(data_dir=test_db.parent),
        )

        engine = DecisionEngine()

        request = AnalysisRequest(
            company_id="test_company",
            question="Analyse la situation",
            max_recommendations=3,
        )

        state = engine.run(request)

        assert state.company_context is not None
        assert state.company_context.name == "Test Co"

        assert state.observation is not None
        assert len(state.observation.kpis) > 0

        assert state.current_step == "done"
        assert len(state.errors) == 0

    def test_pipeline_with_invalid_company(self, test_db, monkeypatch):
        """Pipeline avec entreprise inexistante → erreur."""

        from config import settings
        import engine.nodes.understand as understand_module
        from data.company_store import CompanyStore

        monkeypatch.setattr(settings, "data_dir", test_db.parent)

        monkeypatch.setattr(
            understand_module,
            "CompanyStore",
            lambda: CompanyStore(data_dir=test_db.parent),
        )

        engine = DecisionEngine()

        request = AnalysisRequest(
            company_id="nonexistent",
            question="Test",
        )

        state = engine.run(request)

        assert len(state.errors) > 0
        assert "understand" in state.errors[0].lower()
