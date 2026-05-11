import { useEffect, useMemo, useState } from "react";
import { Gauge, ShieldCheck, Timer, TrendingUp } from "lucide-react";
import { apiGet } from "../api/client";
import type { HeatmapResponse, ParetoPoint, ResultRow } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { HeatmapChart } from "../components/charts/HeatmapChart";
import { ParetoChart } from "../components/charts/ParetoChart";
import { errorMessage, formatDate, formatLatencySeconds, formatMetric } from "./utils";

function avg(values: Array<number | null>) {
  const filtered = values.filter((value): value is number => value !== null && value !== undefined);
  if (!filtered.length) return null;
  return filtered.reduce((sum, value) => sum + value, 0) / filtered.length;
}

export function Results() {
  const [results, setResults] = useState<ResultRow[]>([]);
  const [pareto, setPareto] = useState<ParetoPoint[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapResponse>({ rows: [], columns: [], values: [] });
  const [modelFilter, setModelFilter] = useState("");
  const [profileFilter, setProfileFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      apiGet<ResultRow[]>("/api/results/").then(setResults),
      apiGet<ParetoPoint[]>("/api/results/pareto/").then(setPareto),
      apiGet<HeatmapResponse>("/api/results/heatmap/").then(setHeatmap),
    ])
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const models = [...new Set(results.map((row) => row.model))];
  const profiles = [...new Set(results.map((row) => row.defense_profile))];
  const filtered = useMemo(
    () =>
      results.filter(
        (row) =>
          (!modelFilter || row.model === modelFilter) &&
          (!profileFilter || row.defense_profile === profileFilter),
      ),
    [modelFilter, profileFilter, results],
  );
  const filteredPareto = pareto.filter(
    (row) => (!modelFilter || row.model === modelFilter) && (!profileFilter || row.profile === profileFilter),
  );

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!results.length) return <EmptyState title="Результатов пока нет" text="Completed-запуски появятся здесь после импорта или выполнения benchmark-а." />;

  return (
    <div className="page-stack">
      <section className="toolbar panel">
        <select value={modelFilter} onChange={(event) => setModelFilter(event.target.value)}>
          <option value="">Модель: все</option>
          {models.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
        <select value={profileFilter} onChange={(event) => setProfileFilter(event.target.value)}>
          <option value="">Профиль: все</option>
          {profiles.map((profile) => (
            <option key={profile} value={profile}>
              {profile}
            </option>
          ))}
        </select>
      </section>

      <div className="metric-grid">
        <MetricCard title="Средний proxy-ASR" value={formatMetric(avg(filtered.map((row) => row.proxy_asr)))} hint="ниже лучше" icon={Gauge} />
        <MetricCard title="1−proxy-ASR" value={formatMetric(avg(filtered.map((row) => row.one_minus_asr)))} hint="устойчивость" tone="green" icon={ShieldCheck} />
        <MetricCard title="U_mean" value={formatMetric(avg(filtered.map((row) => row.u_mean)))} hint="полезность" tone="green" icon={TrendingUp} />
        <MetricCard title="p95 latency" value={formatLatencySeconds(avg(filtered.map((row) => row.p95_latency)))} hint="секунды" tone="orange" icon={Timer} />
      </div>

      <div className="analytics-grid">
        <ParetoChart data={filteredPareto} />
        <HeatmapChart data={heatmap} />
      </div>

      <section className="panel">
        <h3>Таблица результатов</h3>
        <DataTable
          data={filtered}
          columns={[
            { key: "run", title: "Run ID", render: (row) => <code>{row.run_id}</code> },
            { key: "title", title: "Название", render: (row) => row.title },
            { key: "model", title: "Модель", render: (row) => row.model },
            { key: "dataset", title: "Датасет", render: (row) => row.dataset },
            { key: "profile", title: "Профиль", render: (row) => `${row.defense_level} ${row.defense_profile}` },
            { key: "proxy", title: "proxy-ASR", render: (row) => formatMetric(row.proxy_asr) },
            { key: "robust", title: "1−proxy-ASR", render: (row) => formatMetric(row.one_minus_asr) },
            { key: "fpr", title: "FPR", render: (row) => formatMetric(row.fpr) },
            { key: "u", title: "U_mean", render: (row) => formatMetric(row.u_mean) },
            { key: "p95", title: "p95, с", render: (row) => formatLatencySeconds(row.p95_latency) },
            { key: "date", title: "Создан", render: (row) => formatDate(row.created_at) },
          ]}
        />
      </section>
    </div>
  );
}
