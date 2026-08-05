import type { Explanation } from "../types";
import { X, ShieldCheck } from "lucide-react";
import PriorityBadge from "./PriorityBadge";
import StatusBadge from "./StatusBadge";

export default function ExplanationDrawer({
  explanation,
  onClose,
}: {
  explanation: Explanation;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-full max-w-xl bg-white h-full overflow-y-auto shadow-2xl fade-in">
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-start justify-between z-10">
          <div>
            <div className="text-xs font-semibold text-[var(--color-brand)] uppercase tracking-wide mb-1">
              Explicabilité
            </div>
            <h3 className="text-base font-semibold leading-snug pr-4">{explanation.recommendation_title}</h3>
            <div className="flex items-center gap-2 mt-2">
              <PriorityBadge priority={explanation.priority} />
              <StatusBadge status={explanation.status} />
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 shrink-0">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <section>
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Pourquoi cette recommandation ?</h4>
            <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 rounded-lg p-3">
              {explanation.narrative}
            </p>
          </section>

          {explanation.company?.name && (
            <section>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Contexte entreprise</h4>
              <div className="text-sm text-gray-700 space-y-1">
                <div><span className="text-gray-500">Nom :</span> {explanation.company.name}</div>
                <div><span className="text-gray-500">Secteur :</span> {explanation.company.industry}</div>
                {explanation.company.focus && (
                  <div><span className="text-gray-500">Focus actuel :</span> {explanation.company.focus}</div>
                )}
                {explanation.company.goals && explanation.company.goals.length > 0 && (
                  <div><span className="text-gray-500">Objectifs :</span> {explanation.company.goals.join(", ")}</div>
                )}
              </div>
            </section>
          )}

          {explanation.signals?.length > 0 && (
            <section>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                Signaux observés ({explanation.signals.length})
              </h4>
              <ul className="text-sm text-gray-700 space-y-1 max-h-48 overflow-y-auto pr-1">
                {explanation.signals.map((s, i) => (
                  <li key={i} className="flex gap-1.5"><span className="text-gray-300">•</span>{s}</li>
                ))}
              </ul>
            </section>
          )}

          {explanation.detected_issues?.length > 0 && (
            <section>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Problèmes / opportunités liés</h4>
              <div className="space-y-2">
                {explanation.detected_issues.map((iss, i) => (
                  <div key={i} className="border border-gray-100 rounded-lg p-2.5">
                    <div className="flex items-center gap-2 mb-1">
                      <PriorityBadge priority={iss.priority} />
                      <span className="text-sm font-medium">{iss.title}</span>
                    </div>
                    <p className="text-xs text-gray-600">{iss.description}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {explanation.hypotheses?.length > 0 && (
            <section>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Hypothèses de raisonnement</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                {explanation.hypotheses.map((h, i) => (
                  <li key={i} className="flex gap-1.5"><span className="text-gray-300">•</span>{h}</li>
                ))}
              </ul>
            </section>
          )}

          {explanation.strategies?.length > 0 && (
            <section>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Stratégies envisagées</h4>
              <div className="space-y-2">
                {explanation.strategies.map((s, i) => (
                  <div key={i} className="border border-gray-100 rounded-lg p-2.5">
                    <div className="text-sm font-medium">{s.name}</div>
                    <p className="text-xs text-gray-600 mt-0.5">{s.description}</p>
                    <div className="flex gap-3 mt-1 text-[11px] text-gray-500">
                      {s.expected_impact && <span>Impact attendu : {s.expected_impact}</span>}
                      {s.effort && <span>Effort : {s.effort}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {explanation.playbooks_used?.length > 0 && (
            <section>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Playbooks mobilisés</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                {explanation.playbooks_used.map((pb, i) => (
                  <li key={i} className="flex gap-1.5">
                    <span className="text-gray-300">•</span>
                    {pb.technique} {pb.for_issue && <span className="text-gray-500">(lié à : {pb.for_issue})</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="flex items-start gap-2 bg-blue-50 rounded-lg p-3">
            <ShieldCheck size={16} className="text-[var(--color-brand)] mt-0.5 shrink-0" />
            <p className="text-xs text-gray-700 leading-relaxed">{explanation.gdpr_note}</p>
          </section>
        </div>
      </div>
    </div>
  );
}
