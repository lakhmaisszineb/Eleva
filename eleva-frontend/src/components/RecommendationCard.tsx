import { useState } from "react";
import type { RecommendationOut } from "../types";
import PriorityBadge from "./PriorityBadge";
import StatusBadge from "./StatusBadge";
import { ChevronDown, ChevronUp, CheckCircle2, XCircle, HelpCircle } from "lucide-react";
import type { LocalDecision } from "../lib/storage";

interface Props {
  recommendation: RecommendationOut;
  decision?: LocalDecision;
  onExplain: () => void;
  onDecide: (decision: LocalDecision) => void;
}

export default function RecommendationCard({ recommendation: r, decision, onExplain, onDecide }: Props) {
  const [open, setOpen] = useState(false);
  const effectiveStatus = decision || r.status;

  return (
    <div className="card p-4 fade-in">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <PriorityBadge priority={r.priority} />
            <StatusBadge status={effectiveStatus} />
          </div>
          <h4 className="text-sm font-semibold leading-snug">{r.title}</h4>
          <p className="text-sm text-gray-600 mt-1 leading-relaxed">{r.summary}</p>
        </div>
      </div>

      <button
        onClick={() => setOpen((o) => !o)}
        className="mt-3 text-xs font-medium text-[var(--color-brand)] flex items-center gap-1 hover:underline"
      >
        {open ? "Réduire les détails" : "Voir la justification et les prochaines étapes"}
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {open && (
        <div className="mt-3 pt-3 border-t border-gray-100 space-y-3 fade-in">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Justification</div>
            <p className="text-sm text-gray-700 leading-relaxed">{r.justification}</p>
          </div>
          {r.expected_outcomes.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Résultats attendus</div>
              <ul className="text-sm text-gray-700 space-y-1">
                {r.expected_outcomes.map((o, i) => (
                  <li key={i} className="flex gap-1.5"><span className="text-emerald-500">✓</span>{o}</li>
                ))}
              </ul>
            </div>
          )}
          {r.next_steps.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Prochaines étapes</div>
              <ol className="text-sm text-gray-700 space-y-1 list-decimal list-inside">
                {r.next_steps.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2 pt-3 border-t border-gray-100">
        <button
          onClick={onExplain}
          className="text-xs font-medium px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 flex items-center gap-1.5"
        >
          <HelpCircle size={14} /> Pourquoi cette recommandation ?
        </button>
        <div className="flex-1" />
        <button
          disabled={effectiveStatus !== "pending_approval" && effectiveStatus !== "draft"}
          onClick={() => onDecide("approved")}
          className="text-xs font-medium px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
        >
          <CheckCircle2 size={14} /> Approuver
        </button>
        <button
          disabled={effectiveStatus !== "pending_approval" && effectiveStatus !== "draft"}
          onClick={() => onDecide("rejected")}
          className="text-xs font-medium px-3 py-1.5 rounded-lg border border-gray-200 text-red-600 hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
        >
          <XCircle size={14} /> Rejeter
        </button>
      </div>
    </div>
  );
}
