import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface LineChartCardProps {
  title: string;
  data: Array<Record<string, string | number | null>>;
  xKey: string;
  series: Array<{ key: string; name: string; color: string }>;
}

export function LineChartCard({ title, data, xKey, series }: LineChartCardProps) {
  return (
    <section className="panel chart-panel">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey={xKey} tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} />
          <Tooltip />
          {series.map((item) => (
            <Line key={item.key} dataKey={item.key} name={item.name} stroke={item.color} strokeWidth={2.5} dot={{ r: 3 }} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
