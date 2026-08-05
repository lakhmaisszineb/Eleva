import type { KPIOut } from "../types";
import { formatKpiValue } from "../lib/format";
import { Minus } from "lucide-react";

function trendIcon() {
  // Le backend n'expose pas encore de champ "trend" via l'API (présent dans le modèle interne KPI
  // mais absent de KPIOut). On affiche une icône neutre par défaut.
  return <Minus size={14} className="text-gray-400" />;
}

export default function KpiGrid({ kpis }: { kpis: KPIOut[] }) {
  if (!kpis.length) {
    return (
      <div className="card p-6 text-sm text-gray-500">Aucun KPI retourné pour cette analyse.</div>
    );
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
      {kpis.map((kpi) => (
        <div key={kpi.name} className="card p-4 fade-in">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{kpi.name}</span>
            {trendIcon()}
          </div>
          <div className="text-xl font-semibold text-[var(--color-ink)]">
            {formatKpiValue(kpi.value, kpi.unit)}
          </div>
        </div>
      ))}
    </div>
  );
}
