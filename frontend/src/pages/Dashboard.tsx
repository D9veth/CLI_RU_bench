import { useEffect, useMemo, useState } from "react";
import { Activity, CheckCircle2, Clock3, Database, FileArchive, Gauge, ShieldAlert } from "lucide-react";
import { apiGet } from "../api/client";
import type { DashboardResponse } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { StatusBadge } from "../components/StatusBadge";
import { BarChartCard } from "../components/charts/BarChartCard";
import { DonutChart } from "../components/charts/DonutChart";
import { HeatmapChart } from "../components/charts/HeatmapChart";
import { errorMessage, formatDate, formatInteger, formatLatencySeconds, formatMetric } from "./utils";

export function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<DashboardResponse>("/api/dashboard/")
      .then(setData)
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const heatmap = useMemo(() => {
    const heatmapItems = data?.heatmap_by_model_profile ?? [];
    const rows = [...new Set(heatmapItems.map((item) => item.model))];
    const columns = [...new Set(heatmapItems.map((item) => item.profile))];
    const values = rows.map((row) =>
      columns.map((column) => heatmapItems.find((item) => item.model === row && item.profile === column)?.proxy_asr ?? null),
    );
    return { rows, columns, values };
  }, [data]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data || data.total_runs === 0) {
    return <EmptyState title="Данных пока нет" text="Импортируйте CLI-артефакты или создайте новый запуск." />;
  }

  const datasetDonut = Object.entries(data.dataset_distribution ?? {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="page-stack">
      <div className="metric-grid">
        <MetricCard title="Всего запусков" value={formatInteger(data.total_runs)} hint="в базе backend" tone="blue" icon={Activity} />
        <MetricCard title="Завершённых запусков" value={formatInteger(data.completed_runs)} hint="готовы к анализу" tone="green" icon={CheckCircle2} />
        <MetricCard title="Средний proxy-ASR" value={formatMetric(data.avg_proxy_asr)} hint="ниже лучше" tone="violet" icon={Gauge} />
        <MetricCard title="Средний U_mean" value={formatMetric(data.avg_u_mean)} hint="выше лучше" tone="green" icon={Database} />
        <MetricCard title="Средний FPR" value={formatMetric(data.avg_fpr)} hint="ниже лучше" tone="orange" icon={ShieldAlert} />
        <MetricCard title="Средняя p95 задержка" value={formatLatencySeconds(data.avg_p95_latency)} hint="секунды" tone="blue" icon={Clock3} />
        <MetricCard
          title="Артефакты"
          value={formatInteger(data.project_artifacts_count)}
          hint={`отчёты: ${formatInteger(data.reports_count)}, таблицы: ${formatInteger(data.tables_count)}, графики: ${formatInteger(data.figures_count)}`}
          tone="violet"
          icon={FileArchive}
        />
      </div>

      <div className="dashboard-grid">
        <BarChartCard
          title="proxy-ASR по профилям защиты"
          data={(data.asr_by_profile ?? []).map((item) => ({ profile: `${item.defense_level} ${item.profile}`, proxy_asr: item.proxy_asr }))}
          xKey="profile"
          yKey="proxy_asr"
          yLabel="proxy-ASR"
        />
        <HeatmapChart data={heatmap} />
        <DonutChart title="Распределение датасетов" data={datasetDonut} />
      </div>

      <section className="panel">
        <div className="panel__header">
          <h3>Последние запуски</h3>
        </div>
        <DataTable
          data={data.latest_runs ?? []}
          columns={[
            { key: "run_id", title: "Run ID", render: (run) => <code>{run.run_id}</code> },
            { key: "title", title: "Название", render: (run) => run.title },
            { key: "model", title: "Модель", render: (run) => run.model_endpoint_name },
            { key: "status", title: "Статус", render: (run) => <StatusBadge status={run.status} /> },
            { key: "proxy_asr", title: "proxy-ASR", render: (run) => formatMetric(run.metrics?.proxy_asr) },
            { key: "created_at", title: "Создан", render: (run) => formatDate(run.created_at) },
          ]}
        />
      </section>
    </div>
  );
}
