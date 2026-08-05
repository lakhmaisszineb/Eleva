import type { ReactNode } from "react";
import { BarChart3, Upload, History, Settings, Sparkles } from "lucide-react";

export type Screen = "analyse" | "import" | "historique" | "parametres";

const NAV: { id: Screen; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { id: "analyse", label: "Analyse", icon: BarChart3 },
  { id: "import", label: "Import de données", icon: Upload },
  { id: "historique", label: "Historique", icon: History },
  { id: "parametres", label: "Paramètres", icon: Settings },
];

export default function Layout({
  active,
  onNavigate,
  healthLabel,
  healthOk,
  children,
}: {
  active: Screen;
  onNavigate: (s: Screen) => void;
  healthLabel: string;
  healthOk: boolean;
  children: ReactNode;
}) {
  return (
    <div className="flex h-full min-h-screen">
      <aside className="w-60 shrink-0 bg-[#101322] text-gray-200 flex flex-col">
        <div className="px-5 py-5 flex items-center gap-2 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-[var(--color-brand)] flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white leading-none">Eleva</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Agent de décision marketing</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                active === id
                  ? "bg-[var(--color-brand)] text-white font-medium"
                  : "text-gray-300 hover:bg-white/5"
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-white/10 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: healthOk ? "#16a34a" : "#dc2626" }}
            />
            {healthLabel}
          </div>
        </div>
      </aside>

      <main className="flex-1 min-w-0 bg-[var(--color-bg)]">{children}</main>
    </div>
  );
}
