import { ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import type { ParetoPoint } from "../../api/types";

export function ParetoChart({ data }: { data: ParetoPoint[] }) {
  const chartData = data
    .filter((item) => item.u_mean !== null && item.one_minus_asr !== null)
    .map((item) => ({
      ...item,
      u: item.u_mean,
      robustness: item.one_minus_asr,
    }));

  return (
    <section className="panel chart-panel">
      <h3>Pareto: полезность и устойчивость</h3>
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart margin={{ top: 20, right: 24, bottom: 24, left: 12 }}>
          <XAxis dataKey="u" type="number" name="U_mean" domain={[0, 1]} tickLine={false} axisLine={false} />
          <YAxis dataKey="robustness" type="number" name="1−proxy-ASR" domain={[0, 1]} tickLine={false} axisLine={false} />
          <ZAxis range={[80, 160]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(value, name) => [Number(value).toFixed(3), name]}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.run_id ?? ""}
          />
          <Scatter data={chartData} fill="#2563eb" />
        </ScatterChart>
      </ResponsiveContainer>
    </section>
  );
}
