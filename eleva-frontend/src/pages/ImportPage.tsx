import { useRef, useState } from "react";
import { UploadCloud, FileSpreadsheet, Info, Lock } from "lucide-react";

function parsePreview(text: string): { headers: string[]; rows: string[][] } {
  const lines = text.trim().split(/\r?\n/).slice(0, 8);
  if (!lines.length) return { headers: [], rows: [] };
  const split = (line: string) => line.split(",").map((c) => c.trim());
  const [headerLine, ...rest] = lines;
  return { headers: split(headerLine), rows: rest.map(split) };
}

export default function ImportPage() {
  const [fileName, setFileName] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ headers: string[]; rows: string[][] } | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(file: File) {
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => setPreview(parsePreview(String(reader.result || "")));
    reader.readAsText(file);
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <header className="mb-6">
        <h1 className="text-xl font-semibold">Import de données</h1>
        <p className="text-sm text-gray-500 mt-1">
          Importez des exports CSV (clients, commandes, campagnes) pour une entreprise. Le mapping
          intelligent des colonnes et le nettoyage sont effectués côté backend.
        </p>
      </header>

      <div className="card p-4 mb-6 flex gap-3 items-start bg-amber-50 border-amber-100">
        <Lock size={16} className="text-amber-600 mt-0.5 shrink-0" />
        <div className="text-sm text-amber-800">
          <strong>Écran prêt côté frontend, à brancher côté backend.</strong> Le moteur d'import
          (mapping LLM des colonnes, nettoyage, validation, rapport) existe déjà dans le module{" "}
          <code className="bg-amber-100 px-1 rounded">data/importer/</code> mais n'est pas encore
          exposé par l'API FastAPI. Il manque un endpoint, par ex.{" "}
          <code className="bg-amber-100 px-1 rounded">POST /companies/&#123;company_id&#125;/import</code>{" "}
          acceptant un fichier CSV et renvoyant le rapport de{" "}
          <code className="bg-amber-100 px-1 rounded">data/importer/report.py</code>. En attendant,
          cet écran permet de prévisualiser un fichier localement.
        </div>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
        className={`card p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
          dragging ? "border-[var(--color-brand)] bg-[var(--color-brand-soft)]" : "border-dashed"
        }`}
      >
        <UploadCloud size={28} className="text-[var(--color-brand)] mb-2" />
        <div className="text-sm font-medium">Glissez-déposez un fichier CSV, ou cliquez pour parcourir</div>
        <div className="text-xs text-gray-500 mt-1">clients.csv, orders.csv, campaigns.csv…</div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </div>

      {fileName && preview && (
        <div className="card mt-6 fade-in overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
            <FileSpreadsheet size={16} className="text-gray-500" />
            <span className="text-sm font-medium">{fileName}</span>
            <span className="text-xs text-gray-400">— aperçu local, {preview.rows.length} lignes affichées</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  {preview.headers.map((h, i) => (
                    <th key={i} className="text-left px-3 py-2 font-medium text-gray-600 whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, ri) => (
                  <tr key={ri} className="border-t border-gray-100">
                    {row.map((cell, ci) => (
                      <td key={ci} className="px-3 py-2 text-gray-700 whitespace-nowrap">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t border-gray-100 flex items-center gap-2 text-xs text-gray-500">
            <Info size={13} />
            Le mapping intelligent des colonnes (LLM) et le rapport de qualité seront affichés ici
            une fois l'endpoint d'import branché.
          </div>
          <div className="px-4 pb-4">
            <button
              disabled
              title="Nécessite l'endpoint backend d'import (non exposé actuellement)"
              className="text-sm font-medium px-4 py-2 rounded-lg bg-gray-200 text-gray-500 cursor-not-allowed"
            >
              Confirmer l'import
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
