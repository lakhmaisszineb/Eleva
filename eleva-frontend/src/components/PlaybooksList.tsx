import type { PlaybookOut } from "../types";
import { BookOpen } from "lucide-react";

export default function PlaybooksList({ playbooks }: { playbooks: PlaybookOut[] }) {
  if (!playbooks.length) {
    return <div className="card p-6 text-sm text-gray-500">Aucun playbook mobilisé pour cette analyse.</div>;
  }
  return (
    <div className="card divide-y divide-gray-100">
      {playbooks.map((pb, i) => (
        <div key={i} className="p-3 flex items-start gap-2.5">
          <BookOpen size={15} className="text-[var(--color-brand)] mt-0.5 shrink-0" />
          <div>
            <div className="text-sm font-medium">{pb.technique || "Playbook"}</div>
            {pb.issue_title && (
              <div className="text-xs text-gray-500">Mobilisé pour : {pb.issue_title}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
