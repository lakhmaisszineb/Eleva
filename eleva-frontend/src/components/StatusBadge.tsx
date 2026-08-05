import { statusLabel, statusColor } from "../lib/format";

export default function StatusBadge({ status }: { status: string }) {
  const color = statusColor[status] || "#374151";
  return (
    <span className="badge" style={{ color, background: `${color}1a`, border: `1px solid ${color}33` }}>
      <span style={{ width: 6, height: 6, borderRadius: 999, background: color, display: "inline-block" }} />
      {statusLabel[status] || status}
    </span>
  );
}
