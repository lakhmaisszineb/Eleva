import { useEffect, useState } from "react";
import Layout, { type Screen } from "./components/Layout";
import AnalysePage from "./pages/AnalysePage";
import ImportPage from "./pages/ImportPage";
import HistoriquePage from "./pages/HistoriquePage";
import ParametresPage from "./pages/ParametresPage";
import { elevaApi } from "./api/client";
import type { AnalyzeResponse } from "./types";
import type { HistoryEntry } from "./lib/storage";

export default function App() {
  const [screen, setScreen] = useState<Screen>("analyse");
  const [healthOk, setHealthOk] = useState(false);
  const [healthLabel, setHealthLabel] = useState("Vérification de l'API…");
  const [externalResult, setExternalResult] = useState<AnalyzeResponse | null>(null);

  async function checkHealth() {
    try {
      const res = await elevaApi.health();
      setHealthOk(true);
      setHealthLabel(`API connectée (v${res.version})`);
    } catch {
      setHealthOk(false);
      setHealthLabel("API injoignable — voir Paramètres");
    }
  }

  useEffect(() => {
    checkHealth();
  }, []);

  function openHistoryEntry(entry: HistoryEntry) {
    setExternalResult(entry.response);
    setScreen("analyse");
  }

  return (
    <Layout active={screen} onNavigate={setScreen} healthOk={healthOk} healthLabel={healthLabel}>
      {screen === "analyse" && (
        <AnalysePage externalResult={externalResult} onConsumeExternal={() => setExternalResult(null)} />
      )}
      {screen === "import" && <ImportPage />}
      {screen === "historique" && <HistoriquePage onOpen={openHistoryEntry} />}
      {screen === "parametres" && <ParametresPage onSaved={checkHealth} />}
    </Layout>
  );
}
