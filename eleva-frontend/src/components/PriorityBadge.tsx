import { priorityLabel, priorityColor, priorityBg } from "../lib/format";

export default function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className="badge"
      style={{ color: priorityColor[priority] || "#374151", background: priorityBg[priority] || "#f3f4f6" }}
    >
      {priorityLabel[priority] || priority}
    </span>
  );
}
