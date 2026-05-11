import type { HeatmapResponse } from "../../api/types";
import { Fragment } from "react";

function colorFor(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "rgba(148, 163, 184, 0.18)";
  }
  const clamped = Math.max(0, Math.min(1, value));
  const hue = 130 - clamped * 110;
  return `hsl(${hue} 80% 78%)`;
}

export function HeatmapChart({ title = "Тепловая карта proxy-ASR", data }: { title?: string; data: HeatmapResponse }) {
  if (!data.rows.length || !data.columns.length) {
    return (
      <section className="panel">
        <h3>{title}</h3>
        <p className="muted">Недостаточно данных для heatmap.</p>
      </section>
    );
  }

  return (
    <section className="panel chart-panel">
      <h3>{title}</h3>
      <div className="heatmap" style={{ gridTemplateColumns: `minmax(150px, 1.2fr) repeat(${data.columns.length}, minmax(82px, 1fr))` }}>
        <div className="heatmap__head">Модель</div>
        {data.columns.map((column) => (
          <div key={column} className="heatmap__head">
            {column}
          </div>
        ))}
        {data.rows.map((row, rowIndex) => (
          <Fragment key={row}>
            <div key={`${row}-label`} className="heatmap__label">
              {row}
            </div>
            {data.columns.map((column, columnIndex) => {
              const value = data.values[rowIndex]?.[columnIndex] ?? null;
              return (
                <div key={`${row}-${column}`} className="heatmap__cell" style={{ background: colorFor(value) }}>
                  {value === null ? "—" : value.toFixed(3)}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
      <div className="heatmap__scale">
        <span>Низкий proxy-ASR</span>
        <div />
        <span>Высокий proxy-ASR</span>
      </div>
    </section>
  );
}
