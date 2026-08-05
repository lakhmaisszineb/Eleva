import { useState } from "react";
import { getApiBaseUrl, setApiBaseUrl, elevaApi, ApiError } from "../api/client";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import type { HealthResponse } from "../types";

export default function ParametresPage({ onSaved }: { onSaved: () => void }) {
  const [url, setUrl] = useState(getApiBaseUrl());
  const [checking, setChecking] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck(nextUrl?: string) {
    setChecking(true);
    setError(null);
    setHealth(null);
    setApiBaseUrl(nextUrl ?? url);
    try {
      const res = await elevaApi.health();
      setHealth(res);
      onSaved();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Impossible de vérifier la connexion.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <header className="mb-6">
        <h1 className="text-xl font-semibold">Paramètres</h1>
        <p className="text-sm text-gray-500 mt-1">
          Configurez l'URL de l'API Eleva (FastAPI / uvicorn) utilisée par ce frontend.
        </p>
      </header>

      <div className="card p-5 space-y-4">
        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase mb-1.5 block">URL de l'API</label>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="http://localhost:8000"
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]/30 focus:border-[var(--color-brand)]"
          />
          <p className="text-xs text-gray-400 mt-1">
            Correspond à l'adresse de <code>uvicorn api.main:app --host 0.0.0.0 --port 8000</code>.
          </p>
        </div>

        <button
          onClick={() => handleCheck()}
          disabled={checking}
          className="inline-flex items-center gap-2 bg-[var(--color-brand)] hover:bg-[var(--color-brand-dark)] text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {checking && <Loader2 size={14} className="animate-spin" />}
          Enregistrer et tester la connexion (/health)
        </button>

        {health && (
          <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 rounded-lg p-3">
            <CheckCircle2 size={16} />
            Connecté — service « {health.service} », version {health.version}, statut {health.status}.
          </div>
        )}
        {error && (
          <div className="flex items-start gap-2 text-sm text-red-700 bg-red-50 rounded-lg p-3">
            <XCircle size={16} className="mt-0.5 shrink-0" />
            {error}
          </div>
        )}
      </div>

      <div className="card p-5 mt-6">
        <h3 className="text-sm font-semibold mb-2">À propos</h3>
        <p className="text-sm text-gray-600 leading-relaxed">
          Eleva est un agent de décision marketing pour l'e-commerce / retail : il observe les
          données de l'entreprise, détecte des problèmes et opportunités, s'appuie sur une base de
          playbooks marketing (RAG) et produit des recommandations argumentées et explicables.
          Aucune action (email, publicité…) n'est exécutée automatiquement : toute recommandation
          reste en statut <em>pending_approval</em> jusqu'à validation humaine.
        </p>
      </div>
    </div>
  );
}
