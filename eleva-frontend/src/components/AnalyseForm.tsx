import { useState } from "react";
import { Play, X } from "lucide-react";
import { getKnownCompanies } from "../lib/storage";

const FOCUS_SUGGESTIONS = [
  "cart_abandonment",
  "churn",
  "acquisition",
  "retention",
  "upsell",
  "loyalty",
  "email_marketing",
  "seasonality",
];

const QUESTION_SUGGESTIONS = [
  "Analyse la situation actuelle et propose les actions prioritaires.",
  "Quels segments de clients sont les plus à risque de churn ?",
  "Quelles opportunités de croissance identifies-tu ce trimestre ?",
];

export interface AnalyseFormValues {
  company_id: string;
  question: string;
  focus_areas: string[];
  max_recommendations: number;
}

export default function AnalyseForm({
  loading,
  onSubmit,
}: {
  loading: boolean;
  onSubmit: (values: AnalyseFormValues) => void;
}) {
  const companies = getKnownCompanies();
  const [companyId, setCompanyId] = useState(companies[0] || "company_001");
  const [question, setQuestion] = useState(QUESTION_SUGGESTIONS[0]);
  const [focusAreas, setFocusAreas] = useState<string[]>([]);
  const [focusInput, setFocusInput] = useState("");
  const [maxRecs, setMaxRecs] = useState(3);

  function addFocus(value: string) {
    const v = value.trim();
    if (v && !focusAreas.includes(v)) setFocusAreas([...focusAreas, v]);
    setFocusInput("");
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ company_id: companyId, question, focus_areas: focusAreas, max_recommendations: maxRecs });
      }}
      className="card p-5 space-y-4"
    >
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase mb-1.5 block">
            Entreprise (company_id)
          </label>
          <input
            list="known-companies"
            value={companyId}
            onChange={(e) => setCompanyId(e.target.value)}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]/30 focus:border-[var(--color-brand)]"
            placeholder="company_001"
          />
          <datalist id="known-companies">
            {companies.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </div>

        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase mb-1.5 block">
            Nombre de recommandations
          </label>
          <input
            type="number"
            min={1}
            max={10}
            value={maxRecs}
            onChange={(e) => setMaxRecs(Math.min(10, Math.max(1, Number(e.target.value) || 1)))}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]/30 focus:border-[var(--color-brand)]"
          />
        </div>
      </div>

      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase mb-1.5 block">Question à Eleva</label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={2}
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]/30 focus:border-[var(--color-brand)] resize-none"
        />
        <div className="flex flex-wrap gap-1.5 mt-1.5">
          {QUESTION_SUGGESTIONS.map((q) => (
            <button
              type="button"
              key={q}
              onClick={() => setQuestion(q)}
              className="text-[11px] px-2 py-1 rounded-full bg-gray-50 border border-gray-200 text-gray-600 hover:bg-gray-100"
            >
              {q.length > 40 ? q.slice(0, 40) + "…" : q}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="text-xs font-semibold text-gray-500 uppercase mb-1.5 block">
          Zones de focus (optionnel)
        </label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {focusAreas.map((f) => (
            <span
              key={f}
              className="text-xs bg-[var(--color-brand-soft)] text-[var(--color-brand-dark)] px-2 py-1 rounded-full flex items-center gap-1"
            >
              {f}
              <button type="button" onClick={() => setFocusAreas(focusAreas.filter((x) => x !== f))}>
                <X size={11} />
              </button>
            </span>
          ))}
        </div>
        <input
          list="focus-suggestions"
          value={focusInput}
          onChange={(e) => setFocusInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              addFocus(focusInput);
            }
          }}
          placeholder="ex: churn — Entrée pour ajouter"
          className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]/30 focus:border-[var(--color-brand)]"
        />
        <datalist id="focus-suggestions">
          {FOCUS_SUGGESTIONS.map((f) => (
            <option key={f} value={f} />
          ))}
        </datalist>
      </div>

      <button
        type="submit"
        disabled={loading || !companyId || !question}
        className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-[var(--color-brand)] hover:bg-[var(--color-brand-dark)] text-white text-sm font-medium px-4 py-2.5 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Play size={15} />
        {loading ? "Analyse en cours…" : "Lancer l'analyse"}
      </button>
    </form>
  );
}
