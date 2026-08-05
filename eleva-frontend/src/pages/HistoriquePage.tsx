import { useState } from "react";
import { clearHistory, getHistory, type HistoryEntry } from "../lib/storage";
import { Trash2, Clock } from "lucide-react";
import PriorityBadge from "../components/PriorityBadge";

export default function HistoriquePage({ onOpen }: { onOpen: (entry: HistoryEntry) => void }) {
  const [entries, setEntries] = useState<HistoryEntry[]>(getHistory());

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Historique des analyses</h1>
          <p className="text-sm text-gray-500 mt-1">
            Conservé localement dans ce navigateur (30 dernières analyses). Aucun endpoint backend
            d'historique n'existe encore — à envisager si Eleva doit centraliser les analyses passées.
          </p>
        </div>
        {entries.length > 0 && (
          <button
            onClick={() => {
              clearHistory();
              setEntries([]);
            }}
            className="text-xs font-medium text-red-600 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-100 hover:bg-red-50"
          >
            <Trash2 size={13} /> Vider
          </button>
        )}
      </header>

      {entries.length === 0 ? (
        <div className="card p-10 text-center text-sm text-gray-500">
          Aucune analyse enregistrée pour l'instant.
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <button
              key={entry.id}
              onClick={() => onOpen(entry)}
              className="card w-full text-left p-4 hover:border-[var(--color-brand)] transition-colors"
            >
              <div className="flex items-center justify-between gap-3 mb-1">
                <span className="text-sm font-medium">
                  {entry.response.company_name || entry.company_id}
                </span>
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <Clock size={12} />
                  {new Date(entry.timestamp).toLocaleString("fr-FR")}
                </span>
              </div>
              <p className="text-sm text-gray-600 line-clamp-1">{entry.question}</p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <span className="text-xs text-gray-500">
                  {entry.response.recommendations.length} recommandation(s)
                </span>
                {entry.response.recommendations.slice(0, 3).map((r) => (
                  <PriorityBadge key={r.id} priority={r.priority} />
                ))}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
