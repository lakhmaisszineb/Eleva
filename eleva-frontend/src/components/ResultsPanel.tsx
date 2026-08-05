import type { AnalyzeResponse, RecommendationOut } from "../types";
import KpiGrid from "./KpiGrid";
import SegmentsChart from "./SegmentsChart";
import IssueCard from "./IssueCard";
import PlaybooksList from "./PlaybooksList";
import RecommendationCard from "./RecommendationCard";
import ErrorBanner from "./ErrorBanner";
import { priorityRank } from "../lib/format";
import type { LocalDecision } from "../lib/storage";
import { Building2, Lightbulb } from "lucide-react";

export default function ResultsPanel({
  result,
  decisions,
  onExplain,
  onDecide,
}: {
  result: AnalyzeResponse;
  decisions: Record<string, LocalDecision>;
  onExplain: (rec: RecommendationOut) => void;
  onDecide: (recId: string, decision: LocalDecision) => void;
}) {
  const sortedIssues = [...result.issues].sort((a, b) => priorityRank(a.priority) - priorityRank(b.priority));
  const sortedRecs = [...result.recommendations].sort(
    (a, b) => priorityRank(a.priority) - priorityRank(b.priority)
  );

  return (
    <div className="space-y-6">
      {result.errors.length > 0 && (
        <div className="space-y-2">
          {result.errors.map((e, i) => (
            <ErrorBanner key={i} message={e} />
          ))}
        </div>
      )}

      {(result.company_name || result.industry) && (
        <div className="card p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[var(--color-brand-soft)] flex items-center justify-center shrink-0">
            <Building2 size={18} className="text-[var(--color-brand)]" />
          </div>
          <div>
            <div className="text-sm font-semibold">{result.company_name || result.company_id}</div>
            <div className="text-xs text-gray-500">{result.industry}</div>
          </div>
        </div>
      )}

      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2.5">Indicateurs clés (KPIs)</h3>
        <KpiGrid kpis={result.kpis} />
      </section>

      <div className="grid lg:grid-cols-2 gap-5">
        <section>
          <h3 className="text-sm font-semibold text-gray-700 mb-2.5">Segments RFM</h3>
          <SegmentsChart segments={result.segments} />
        </section>

        <section>
          <h3 className="text-sm font-semibold text-gray-700 mb-2.5">Insights</h3>
          <div className="card p-4 h-full">
            {result.insights.length === 0 ? (
              <p className="text-sm text-gray-500">Aucun insight généré.</p>
            ) : (
              <ul className="space-y-2">
                {result.insights.map((insight, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-700">
                    <Lightbulb size={14} className="text-amber-500 mt-0.5 shrink-0" />
                    {insight}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>

      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2.5">
          Problèmes &amp; opportunités détectés ({sortedIssues.length})
        </h3>
        {sortedIssues.length === 0 ? (
          <div className="card p-6 text-sm text-gray-500">Aucun problème ou opportunité détecté.</div>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {sortedIssues.map((issue) => (
              <IssueCard key={issue.id} issue={issue} />
            ))}
          </div>
        )}
      </section>

      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2.5">Playbooks marketing mobilisés</h3>
        <PlaybooksList playbooks={result.playbooks} />
      </section>

      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2.5">
          Recommandations ({sortedRecs.length})
        </h3>
        {sortedRecs.length === 0 ? (
          <div className="card p-6 text-sm text-gray-500">Aucune recommandation produite.</div>
        ) : (
          <div className="space-y-3">
            {sortedRecs.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                decision={decisions[rec.id]}
                onExplain={() => onExplain(rec)}
                onDecide={(d) => onDecide(rec.id, d)}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
