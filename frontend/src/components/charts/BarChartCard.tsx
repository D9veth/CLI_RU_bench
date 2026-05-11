import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface BarChartCardProps {
  title: string;
  data: Array<Record<string, string | number | null>>;
  xKey: string;
  yKey: string;
  yLabel?: string;
}

export function BarChartCard({ title, data, xKey, yKey, yLabel }: BarChartCardProps) {
  return (
    <section className="panel chart-panel">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey={xKey} tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} label={yLabel ? { value: yLabel, angle: -90, position: "insideLeft" } : undefined} />
          <Tooltip />
          <Bar dataKey={yKey} fill="#2563eb" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
