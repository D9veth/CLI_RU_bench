import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const colors = ["#2563eb", "#7c3aed", "#22c55e", "#f97316", "#94a3b8"];

export function DonutChart({ title, data }: { title: string; data: Array<{ name: string; value: number }> }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  return (
    <section className="panel chart-panel">
      <h3>{title}</h3>
      <div className="donut-layout">
        <ResponsiveContainer width="58%" height={240}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={92} paddingAngle={2}>
              {data.map((_, index) => (
                <Cell key={index} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-legend">
          <strong>{total.toLocaleString("ru-RU")}</strong>
          {data.map((item, index) => (
            <span key={item.name}>
              <i style={{ background: colors[index % colors.length] }} />
              {item.name}: {item.value}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
