import type { IssueOut } from "../types";
import PriorityBadge from "./PriorityBadge";
import { AlertTriangle, Sparkles } from "lucide-react";

export default function IssueCard({ issue }: { issue: IssueOut }) {
  const isOpportunity = issue.type === "opportunity";
  return (
    <div className="card p-4 fade-in">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-start gap-2">
          {isOpportunity ? (
            <Sparkles size={16} className="text-emerald-600 mt-0.5 shrink-0" />
          ) : (
            <AlertTriangle size={16} className="text-red-500 mt-0.5 shrink-0" />
          )}
          <h4 className="text-sm font-semibold leading-snug">{issue.title}</h4>
        </div>
        <PriorityBadge priority={issue.priority} />
      </div>
      <p className="text-sm text-gray-600 mb-2 leading-relaxed">{issue.description}</p>
      {issue.evidence.length > 0 && (
        <ul className="text-xs text-gray-500 space-y-1 border-t border-gray-100 pt-2 mt-2">
          {issue.evidence.map((e, i) => (
            <li key={i} className="flex gap-1.5">
              <span className="text-gray-300">•</span>
              <span>{e}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
