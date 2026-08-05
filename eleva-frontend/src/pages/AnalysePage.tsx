import { useEffect, useState } from "react";
import AnalyseForm, { type AnalyseFormValues } from "../components/AnalyseForm";
import ResultsPanel from "../components/ResultsPanel";
import ExplanationDrawer from "../components/ExplanationDrawer";
import ErrorBanner from "../components/ErrorBanner";
import { elevaApi, ApiError } from "../api/client";
import type { AnalyzeResponse, RecommendationOut } from "../types";
import { addKnownCompany, getLocalDecisions, saveHistoryEntry, setLocalDecision, type LocalDecision } from "../lib/storage";
import { Loader2 } from "lucide-react";

export default function AnalysePage({
  externalResult,
  onConsumeExternal,
}: {
  externalResult?: AnalyzeResponse | null;
  onConsumeExternal?: () => void;
}) {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [explainRec, setExplainRec] = useState<RecommendationOut | null>(null);
  const [explainNotice, setExplainNotice] = useState<string | null>(null);
  const [decisions, setDecisions] = useState<Record<string, LocalDecision>>(getLocalDecisions());

  async function handleSubmit(values: AnalyseFormValues) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await elevaApi.analyze({
        company_id: values.company_id,
        question: values.question,
        focus_areas: values.focus_areas.length ? values.focus_areas : undefined,
        max_recommendations: values.max_recommendations,
      });
      setResult(response);
      addKnownCompany(values.company_id);
      saveHistoryEntry({
        id: crypto.randomUUID(),
        company_id: values.company_id,
        question: values.question,
        timestamp: new Date().toISOString(),
        response,
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur inattendue lors de l'analyse.");
    } finally {
      setLoading(false);
    }
  }

  function handleExplain(rec: RecommendationOut) {
    if (result?.explanation && result.explanation.recommendation_id === rec.id) {
      setExplainNotice(null);
      setExplainRec(rec);
    } else {
      // Limitation actuelle du backend : /analyze n'explique que la 1ère recommandation
      // (engine/explain.py::explain_recommendation appelé sans recommendation_id).
      setExplainNotice(
        "L'explication détaillée n'est aujourd'hui calculée par le backend que pour la recommandation prioritaire de l'analyse. Pour explorer le « pourquoi » de chaque recommandation individuellement, il faudra exposer explain_recommendation(state, recommendation_id) via un futur endpoint POST /analyze/{id}/explain."
      );
      setTimeout(() => setExplainNotice(null), 7000);
    }
  }

  function handleDecide(recId: string, decision: LocalDecision) {
    setLocalDecision(recId, decision);
    setDecisions((prev) => ({ ...prev, [recId]: decision }));
  }

  useEffect(() => {
    if (externalResult) {
      setResult(externalResult);
      setError(null);
      setExplainRec(null);
      onConsumeExternal?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalResult]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <header className="mb-6">
        <h1 className="text-xl font-semibold">Analyse de la performance</h1>
        <p className="text-sm text-gray-500 mt-1">
          Interrogez Eleva sur une entreprise : KPIs, segments, problèmes détectés, playbooks et
          recommandations argumentées — validation humaine requise avant toute action.
        </p>
      </header>

      <div className="mb-6">
        <AnalyseForm loading={loading} onSubmit={handleSubmit} />
      </div>

      {explainNotice && (
        <div className="mb-4">
          <ErrorBanner message={explainNotice} />
        </div>
      )}

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-2 text-gray-500 text-sm py-16">
          <Loader2 size={18} className="animate-spin" />
          Eleva observe, détecte et raisonne…
        </div>
      )}

      {!loading && result && (
        <ResultsPanel
          result={result}
          decisions={decisions}
          onExplain={handleExplain}
          onDecide={handleDecide}
        />
      )}

      {!loading && !result && !error && (
        <div className="card p-10 text-center text-sm text-gray-500">
          Lancez une analyse pour voir apparaître les KPIs, segments, problèmes détectés et
          recommandations d'Eleva.
        </div>
      )}

      {explainRec && result?.explanation && (
        <ExplanationDrawer explanation={result.explanation} onClose={() => setExplainRec(null)} />
      )}
    </div>
  );
}
