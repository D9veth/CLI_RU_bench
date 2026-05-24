import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, Download, GitCompareArrows, Info, TableProperties } from "lucide-react";
import { apiGet, apiGetBlob, getCompareExportUrl, getCompareRuns } from "../api/client";
import type { CategoryBreakdown, CompareMetric, CompareOptionsResponse, CompareOptionRun, CompareResponse, DifferentCase } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { errorMessage, formatInteger, formatLatencySeconds, formatMetric } from "./utils";

const CARD_METRICS = ["proxy_asr", "one_minus_asr", "fpr", "u_mean", "p95_latency", "parse_error_rate"];
const GROUPED_CHART_METRICS = ["proxy_asr", "fpr", "u_mean", "p95_latency"];
const PROFILE_METRICS = ["proxy_asr", "fpr", "u_mean", "p95_latency", "parse_error_rate"];

const DISPLAY_LABELS: Record<string, string> = {
  proxy_asr: "proxy-ASR",
  one_minus_asr: "1−proxy-ASR",
  fpr: "FPR",
  u_mean: "U_mean",
  rummlu_accuracy: "ruMMLU",
  sberquad_f1: "SberQuAD F1",
  sberquad_em: "SberQuAD EM",
  p50_latency: "p50 latency",
  p95_latency: "p95 latency",
  parse_error_rate: "parse_error",
  total_cases: "total cases",
};

export function Compare() {
  const [options, setOptions] = useState<CompareOptionRun[]>([]);
  const [selectedA, setSelectedA] = useState("");
  const [selectedB, setSelectedB] = useState("");
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [compareError, setCompareError] = useState("");

  useEffect(() => {
    apiGet<CompareOptionsResponse>("/api/compare/options/")
      .then((data) => setOptions(data.runs))
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const selectedRunA = options.find((run) => String(run.id) === selectedA) ?? null;
  const selectedRunB = options.find((run) => String(run.id) === selectedB) ?? null;
  const sameRunSelected = Boolean(selectedA && selectedB && selectedA === selectedB);
  const canCompare = Boolean(selectedA && selectedB && !sameRunSelected && !comparing);
  const metricsByKey = useMemo(() => {
    const lookup = new Map<string, CompareMetric>();
    comparison?.metrics.forEach((metric) => lookup.set(metric.key, metric));
    return lookup;
  }, [comparison]);

  async function compare() {
    if (!selectedA || !selectedB) return;
    if (sameRunSelected) {
      setCompareError("Выберите два разных запуска.");
      return;
    }
    setComparing(true);
    setCompareError("");
    try {
      const data = await getCompareRuns(Number(selectedA), Number(selectedB));
      setComparison(data);
    } catch (err) {
      setComparison(null);
      setCompareError(errorMessage(err));
    } finally {
      setComparing(false);
    }
  }

  async function downloadCsv() {
    if (!selectedA || !selectedB || sameRunSelected) return;
    setDownloading(true);
    setCompareError("");
    try {
      const exportUrl = new URL(getCompareExportUrl(Number(selectedA), Number(selectedB)));
      const blob = await apiGetBlob(`${exportUrl.pathname}${exportUrl.search}`);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `compare_${selectedA}_${selectedB}.csv`;
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err) {
      setCompareError(errorMessage(err));
    } finally {
      setDownloading(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page-stack">
      <section className="info-note">
        <Info size={20} />
        <p>
          proxy-ASR — эвристическая метрика текущего evaluator-а. Она показывает долю атакующих кейсов без распознанного безопасного отказа или с найденным индикатором цели атаки. Не является строгим доказательством фактического вредоносного успеха атаки.
        </p>
      </section>

      {!options.length ? (
        <EmptyState title="Завершённые запуски не найдены" text="Сначала импортируйте артефакты или выполните benchmark." />
      ) : (
        <>
          <section className="panel compare-selection">
            <label>
              <span>Запуск A</span>
              <select value={selectedA} onChange={(event) => setSelectedA(event.target.value)}>
                <option value="">Выберите запуск A</option>
                {options.map((run) => (
                  <option key={run.id} value={run.id}>
                    {run.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Запуск B</span>
              <select value={selectedB} onChange={(event) => setSelectedB(event.target.value)}>
                <option value="">Выберите запуск B</option>
                {options.map((run) => (
                  <option key={run.id} value={run.id}>
                    {run.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="compare-selection__actions">
              <button className="primary-button" disabled={!canCompare} onClick={() => void compare()}>
                <GitCompareArrows size={18} />
                {comparing ? "Сравниваем..." : "Сравнить"}
              </button>
              <button className="secondary-button" disabled={!comparison || downloading} onClick={() => void downloadCsv()}>
                <Download size={18} />
                CSV
              </button>
            </div>
            <div className="compare-selection__meta">
              <span>Датасет: {selectedRunA?.dataset ?? selectedRunB?.dataset ?? "—"}</span>
              <span>Профиль: {selectedRunA?.profile ?? selectedRunB?.profile ?? "—"}</span>
            </div>
          </section>

          {sameRunSelected ? <div className="form-error">Выберите два разных запуска.</div> : null}
          {compareError ? <div className="form-error">{compareError}</div> : null}

          {!comparison ? (
            <EmptyState title="Выберите два завершённых запуска для сравнения." text="Сравнение считается на лету по двум run_id." />
          ) : (
            <>
              <ComparisonWarnings warnings={comparison.warnings} />
              <MetricCards metrics={CARD_METRICS.map((key) => metricsByKey.get(key)).filter((metric): metric is CompareMetric => Boolean(metric))} />
              <div className="analytics-grid">
                <GroupedMetricChart metrics={GROUPED_CHART_METRICS.map((key) => metricsByKey.get(key)).filter((metric): metric is CompareMetric => Boolean(metric))} />
                <ProfileChart metrics={PROFILE_METRICS.map((key) => metricsByKey.get(key)).filter((metric): metric is CompareMetric => Boolean(metric))} />
              </div>
              {comparison.category_breakdown.length ? <CategoryChart rows={comparison.category_breakdown} /> : null}
              <MetricsTable metrics={comparison.metrics} />
              <DifferentCasesTable rows={comparison.top_different_cases} />
              <section className="panel actions-bar">
                <Link className="secondary-button" to={`/runs/${comparison.run_a.id}`}>
                  Открыть запуск A
                </Link>
                <Link className="secondary-button" to={`/runs/${comparison.run_b.id}`}>
                  Открыть запуск B
                </Link>
                <button className="secondary-button" disabled={downloading} onClick={() => void downloadCsv()}>
                  <Download size={18} />
                  Скачать CSV
                </button>
                <Link className="secondary-button" to={`/runs/${comparison.run_a.id}`}>
                  Перейти к отчёту A
                </Link>
                <Link className="secondary-button" to={`/runs/${comparison.run_b.id}`}>
                  Перейти к отчёту B
                </Link>
              </section>
            </>
          )}
        </>
      )}
    </div>
  );
}

function ComparisonWarnings({ warnings }: { warnings: CompareResponse["warnings"] }) {
  if (!warnings.length) return null;
  return (
    <section className="warning-note">
      <AlertTriangle size={20} />
      <div>
        <strong>Запуски выполнены на разных датасетах или профилях защиты. Такое сравнение можно использовать для ориентира, но оно менее строгое.</strong>
        {warnings.map((warning) => (
          <p key={warning.code}>{warning.message}</p>
        ))}
      </div>
    </section>
  );
}

function MetricCards({ metrics }: { metrics: CompareMetric[] }) {
  return (
    <div className="compare-card-grid">
      {metrics.map((metric) => (
        <section className="compare-card" key={metric.key}>
          <div className="compare-card__header">
            <strong>
              {displayLabel(metric)} {directionArrow(metric.direction)}
            </strong>
            <WinnerBadge better={metric.better} />
          </div>
          <dl>
            <div>
              <dt>A</dt>
              <dd>{formatCompareValue(metric, metric.value_a)}</dd>
            </div>
            <div>
              <dt>B</dt>
              <dd>{formatCompareValue(metric, metric.value_b)}</dd>
            </div>
            <div>
              <dt>Δ</dt>
              <dd>{formatDelta(metric)}</dd>
            </div>
          </dl>
        </section>
      ))}
    </div>
  );
}

function GroupedMetricChart({ metrics }: { metrics: CompareMetric[] }) {
  const data = metrics.map((metric) => ({
    metric: displayLabel(metric),
    A: chartValue(metric, metric.value_a),
    B: chartValue(metric, metric.value_b),
  }));

  return (
    <section className="panel chart-panel">
      <h3>Основные метрики</h3>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 12, right: 12, bottom: 12, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="metric" tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => Number(value).toFixed(3)} />
          <Legend />
          <Bar dataKey="A" fill="#2563eb" radius={[6, 6, 0, 0]} />
          <Bar dataKey="B" fill="#f97316" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function ProfileChart({ metrics }: { metrics: CompareMetric[] }) {
  const maxLatency = Math.max(
    ...metrics.filter((metric) => metric.key.includes("latency")).flatMap((metric) => [metric.value_a ?? 0, metric.value_b ?? 0]),
    1,
  );
  const data = metrics.map((metric) => ({
    metric: displayLabel(metric),
    A: normalizedValue(metric, metric.value_a, maxLatency),
    B: normalizedValue(metric, metric.value_b, maxLatency),
  }));

  return (
    <section className="panel chart-panel">
      <h3>Профиль модели</h3>
      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="metric" />
          <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
          <Radar name="Запуск A" dataKey="A" stroke="#2563eb" fill="#2563eb" fillOpacity={0.25} />
          <Radar name="Запуск B" dataKey="B" stroke="#f97316" fill="#f97316" fillOpacity={0.18} />
          <Legend />
          <Tooltip formatter={(value) => Number(value).toFixed(3)} />
        </RadarChart>
      </ResponsiveContainer>
    </section>
  );
}

function CategoryChart({ rows }: { rows: CategoryBreakdown[] }) {
  const data = rows.map((row) => ({
    category: row.category,
    A: row.proxy_asr_a,
    B: row.proxy_asr_b,
  }));

  return (
    <section className="panel chart-panel">
      <h3>proxy-ASR по категориям</h3>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 12, right: 16, bottom: 36, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="category" tickLine={false} axisLine={false} angle={-10} textAnchor="end" height={70} />
          <YAxis domain={[0, 1]} tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => (value === null ? "—" : Number(value).toFixed(3))} />
          <Legend />
          <Bar dataKey="A" fill="#2563eb" radius={[6, 6, 0, 0]} />
          <Bar dataKey="B" fill="#f97316" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function MetricsTable({ metrics }: { metrics: CompareMetric[] }) {
  return (
    <section className="panel">
      <h3>
        <TableProperties size={19} />
        Таблица сравнения
      </h3>
      <DataTable
        data={metrics}
        columns={[
          { key: "metric", title: "Метрика", render: (metric) => `${displayLabel(metric)} ${directionArrow(metric.direction)}` },
          { key: "a", title: "Запуск A", render: (metric) => formatCompareValue(metric, metric.value_a) },
          { key: "b", title: "Запуск B", render: (metric) => formatCompareValue(metric, metric.value_b) },
          { key: "delta", title: "Δ A−B", render: (metric) => formatDelta(metric) },
          { key: "better", title: "Лучше", render: (metric) => <WinnerBadge better={metric.better} compact /> },
        ]}
      />
    </section>
  );
}

function DifferentCasesTable({ rows }: { rows: DifferentCase[] }) {
  return (
    <section className="panel">
      <h3>Кейсы с различающимся результатом</h3>
      {rows.length ? (
        <DataTable
          data={rows}
          columns={[
            { key: "case_id", title: "case_id", render: (row) => <code>{row.case_id}</code> },
            { key: "category", title: "Категория", render: (row) => row.category || "—" },
            { key: "result_a", title: "Результат A", render: (row) => row.result_a },
            { key: "result_b", title: "Результат B", render: (row) => row.result_b },
            { key: "difference", title: "Разница", render: (row) => row.difference ?? betterLabel(row.better) },
          ]}
        />
      ) : (
        <EmptyState title="Различия по отдельным кейсам недоступны для этих запусков." text="Для этого нужны cases.jsonl у обоих запусков и совпадающие case_id." />
      )}
    </section>
  );
}

function WinnerBadge({ better, compact = false }: { better: CompareMetric["better"]; compact?: boolean }) {
  return <span className={`winner-badge winner-${better ?? "none"}`}>{compact ? betterLabelCompact(better) : betterLabel(better)}</span>;
}

function displayLabel(metric: CompareMetric) {
  return DISPLAY_LABELS[metric.key] ?? metric.label;
}

function directionArrow(direction: CompareMetric["direction"]) {
  if (direction === "lower") return "↓";
  if (direction === "higher") return "↑";
  return "";
}

function betterLabel(better: CompareMetric["better"]) {
  if (better === "a") return "Лучше: A";
  if (better === "b") return "Лучше: B";
  if (better === "equal") return "Одинаково";
  return "—";
}

function betterLabelCompact(better: CompareMetric["better"]) {
  if (better === "a") return "A";
  if (better === "b") return "B";
  if (better === "equal") return "=";
  return "—";
}

function formatCompareValue(metric: CompareMetric, value: number | null) {
  if (metric.key === "total_cases") {
    return formatInteger(value);
  }
  if (metric.key.includes("latency")) {
    return formatLatencySeconds(value);
  }
  return formatMetric(value);
}

function formatDelta(metric: CompareMetric) {
  if (metric.delta === null) return "—";
  const sign = metric.delta > 0 ? "+" : "";
  if (metric.key === "total_cases") {
    return `${sign}${formatInteger(metric.delta)}`;
  }
  if (metric.key.includes("latency")) {
    return `${sign}${formatLatencySeconds(metric.delta)}`;
  }
  return `${sign}${metric.delta.toFixed(3)}`;
}

function chartValue(metric: CompareMetric, value: number | null) {
  if (value === null) return null;
  return metric.key.includes("latency") ? value / 1000 : value;
}

function normalizedValue(metric: CompareMetric, value: number | null, maxLatency: number) {
  if (value === null) return 0;
  if (metric.key.includes("latency")) {
    return clamp01(1 - value / maxLatency);
  }
  if (metric.direction === "lower") {
    return clamp01(1 - value);
  }
  if (metric.direction === "higher") {
    return clamp01(value);
  }
  return 0;
}

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value));
}
