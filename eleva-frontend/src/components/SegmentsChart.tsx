import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { SegmentOut } from "../types";

const PALETTE = ["#3f51e8", "#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe", "#e0e7ff"];

export default function SegmentsChart({ segments }: { segments: SegmentOut[] }) {
  if (!segments.length) {
    return <div className="card p-6 text-sm text-gray-500">Aucun segment RFM disponible.</div>;
  }

  const data = [...segments].sort((a, b) => b.size - a.size);

  return (
    <div className="card p-4">
      <div style={{ width: "100%", height: 240 }}>
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="name"
              width={140}
              tick={{ fontSize: 12, fill: "#374151" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={((value: number, _name: unknown, props: any) => [
                `${value} clients (${props?.payload?.percentage}%)`,
                "Taille du segment",
              ]) as any}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Bar dataKey="size" radius={[0, 6, 6, 0]} barSize={18}>
              {data.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
