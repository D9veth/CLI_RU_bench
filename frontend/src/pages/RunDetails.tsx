import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { FileText, PauseCircle, PlayCircle, Terminal } from "lucide-react";
import { apiGet, apiGetBlob, apiPost, ApiError } from "../api/client";
import type { BenchmarkRun, ProjectArtifact, ProjectArtifactsResponse, RunArtifact, RunMetrics } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { canStartRun } from "../auth/roleGuards";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { StatusBadge } from "../components/StatusBadge";
import { errorMessage, formatBytes, formatDate, formatLatencySeconds, formatMetric } from "./utils";

interface ReportResponse {
  report: string;
}

interface CasesResponse {
  cases: Array<Record<string, unknown>>;
}

interface LogsResponse {
  stdout: string;
  stderr: string;
}

interface DLPFindingsResponse {
  findings: Array<Record<string, unknown>>;
}

interface PolicyDecisionsResponse {
  decisions: Array<Record<string, unknown>>;
}

async function nullableGet<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function RunDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const [run, setRun] = useState<BenchmarkRun | null>(null);
  const [metrics, setMetrics] = useState<RunMetrics | null>(null);
  const [artifacts, setArtifacts] = useState<RunArtifact[]>([]);
  const [projectArtifacts, setProjectArtifacts] = useState<ProjectArtifact[]>([]);
  const [report, setReport] = useState("");
  const [cases, setCases] = useState<Array<Record<string, unknown>>>([]);
  const [logs, setLogs] = useState<LogsResponse>({ stdout: "", stderr: "" });
  const [dlpFindings, setDlpFindings] = useState<Array<Record<string, unknown>>>([]);
  const [policyDecisions, setPolicyDecisions] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    if (!id) return;
    const [runData, metricsData, artifactsData, projectArtifactsData, reportData, casesData, logsData, dlpData, policyData] = await Promise.all([
      apiGet<BenchmarkRun>(`/api/runs/${id}/`),
      nullableGet<RunMetrics>(`/api/runs/${id}/metrics/`),
      apiGet<RunArtifact[]>(`/api/runs/${id}/artifacts/`),
      apiGet<ProjectArtifactsResponse>(`/api/project-artifacts/?related_run=${id}&limit=100`),
      nullableGet<ReportResponse>(`/api/runs/${id}/report/`),
      nullableGet<CasesResponse>(`/api/runs/${id}/cases/?limit=100`),
      nullableGet<LogsResponse>(`/api/runs/${id}/logs/`),
      nullableGet<DLPFindingsResponse>(`/api/runs/${id}/dlp-findings/?limit=100`),
      nullableGet<PolicyDecisionsResponse>(`/api/runs/${id}/policy-decisions/?limit=100`),
    ]);
    setRun(runData);
    setMetrics(metricsData ?? runData.metrics ?? null);
    setArtifacts(artifactsData);
    setProjectArtifacts(projectArtifactsData.results);
    setReport(reportData?.report ?? "");
    setCases(casesData?.cases ?? []);
    setLogs(logsData ?? { stdout: "", stderr: "" });
    setDlpFindings(dlpData?.findings ?? []);
    setPolicyDecisions(policyData?.decisions ?? []);
  }

  useEffect(() => {
    load()
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function startRun() {
    if (!run) return;
    await apiPost<BenchmarkRun>(`/api/runs/${run.id}/start/`);
    await load();
  }

  async function cancelRun() {
    if (!run) return;
    await apiPost<BenchmarkRun>(`/api/runs/${run.id}/cancel/`);
    await load();
  }

  async function openProjectArtifact(artifact: ProjectArtifact) {
    const blob = await apiGetBlob(`/api/project-artifacts/${artifact.id}/raw/`);
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!run) return <ErrorState title="Запуск не найден" />;

  return (
    <div className="page-stack">
      <section className="panel run-hero">
        <div>
          <div className="eyebrow">Run ID</div>
          <h2>{run.run_id}</h2>
          <p>{run.title}</p>
        </div>
        <div className="run-hero__actions">
          <StatusBadge status={run.status} />
          {canStartRun(user) && run.can_start ? (
            <button className="primary-button" onClick={() => void startRun()}>
              <PlayCircle size={18} />
              Запустить
            </button>
          ) : null}
          {canStartRun(user) && run.can_cancel ? (
            <button className="secondary-button" onClick={() => void cancelRun()}>
              <PauseCircle size={18} />
              Отменить
            </button>
          ) : null}
        </div>
      </section>

      {metrics ? (
        <div className="metric-grid">
          <MetricCard title="proxy-ASR" value={formatMetric(metrics.proxy_asr)} hint="эвристическая метрика evaluator-а" tone="violet" />
          <MetricCard title="1−proxy-ASR" value={formatMetric(metrics.one_minus_asr)} hint="устойчивость" tone="green" />
          <MetricCard title="FPR" value={formatMetric(metrics.fpr)} hint="ложные срабатывания" tone="orange" />
          <MetricCard title="U_mean" value={formatMetric(metrics.u_mean)} hint="полезность" tone="blue" />
          <MetricCard title="p95 latency" value={formatLatencySeconds(metrics.p95_latency)} hint="секунды" tone="blue" />
          <MetricCard title="Кейсы" value={metrics.total_cases} hint={`ok: ${metrics.ok_cases}, errors: ${metrics.error_cases}`} />
        </div>
      ) : (
        <EmptyState title="Метрики недоступны" text="summary.json или RunMetrics пока не найдены для этого запуска." />
      )}

      <section className="panel details-grid">
        <div>
          <h3>Информация о запуске</h3>
          <dl className="definition-list">
            <dt>Модель</dt>
            <dd>{run.model_endpoint_name}</dd>
            <dt>Датасет</dt>
            <dd>{run.dataset_name}</dd>
            <dt>Профиль защиты</dt>
            <dd>{run.defense_profile_name}</dd>
            <dt>Создан</dt>
            <dd>{formatDate(run.created_at)}</dd>
            <dt>Начат</dt>
            <dd>{formatDate(run.started_at)}</dd>
            <dt>Завершён</dt>
            <dd>{formatDate(run.finished_at)}</dd>
            <dt>Output dir</dt>
            <dd>{run.output_dir || "—"}</dd>
          </dl>
        </div>
        <pre className="json-block">{JSON.stringify(run.config_snapshot_json, null, 2)}</pre>
      </section>

      <section className="panel">
        <div className="panel__header">
          <h3>
            <FileText size={19} />
            Отчёт
          </h3>
        </div>
        <pre className="markdown-block">{report || "Отчёт недоступен"}</pre>
      </section>

      <section className="panel">
        <h3>Артефакты</h3>
        <DataTable
          data={artifacts}
          columns={[
            { key: "type", title: "Тип", render: (artifact) => artifact.artifact_type },
            { key: "path", title: "Файл", render: (artifact) => <code>{artifact.file_path}</code> },
            { key: "size", title: "Размер", render: (artifact) => `${artifact.size_bytes} байт` },
            { key: "created", title: "Создан", render: (artifact) => formatDate(artifact.created_at) },
          ]}
        />
      </section>

      <section className="panel">
        <h3>Связанные артефакты проекта</h3>
        <DataTable
          data={projectArtifacts}
          emptyText="Связанные ProjectArtifact пока не найдены."
          columns={[
            { key: "name", title: "Имя", render: (artifact) => artifact.name },
            { key: "type", title: "Тип", render: (artifact) => artifact.artifact_type },
            { key: "path", title: "Файл", render: (artifact) => <code>{artifact.file_path}</code> },
            { key: "size", title: "Размер", render: (artifact) => formatBytes(artifact.size_bytes) },
            { key: "lines", title: "Строк", render: (artifact) => artifact.line_count ?? "—" },
            {
              key: "actions",
              title: "Действия",
              render: (artifact) => (
                <button className="secondary-button" onClick={() => void openProjectArtifact(artifact)}>
                  Открыть файл
                </button>
              ),
            },
          ]}
        />
      </section>

      <section className="panel">
        <h3>Кейсы</h3>
        {cases.length ? (
          <DataTable
            data={cases.slice(0, 100)}
            columns={[
              { key: "id", title: "case_id", render: (row) => String(row.case_id ?? row.id ?? "—") },
              { key: "type", title: "type", render: (row) => String(row.case_type ?? row.type ?? "—") },
              { key: "status", title: "status", render: (row) => String(row.status ?? "—") },
              { key: "success", title: "success_attack", render: (row) => String(row.success_attack ?? row.success ?? "—") },
            ]}
          />
        ) : (
          <EmptyState title="Кейсы недоступны" text="cases.jsonl не найден или пока пуст." />
        )}
      </section>

      <section className="panel">
        <h3>DLP findings</h3>
        {dlpFindings.length ? (
          <DataTable
            data={dlpFindings}
            columns={[
              { key: "case_id", title: "case_id", render: (row) => String(row.case_id ?? "—") },
              { key: "type", title: "Тип", render: (row) => String(row.type ?? "—") },
              { key: "severity", title: "Severity", render: (row) => String(row.severity ?? "—") },
              { key: "rule", title: "Rule", render: (row) => String(row.rule_id ?? "—") },
              { key: "evidence", title: "Evidence", render: (row) => String(row.evidence_redacted ?? "—") },
            ]}
          />
        ) : (
          <EmptyState title="DLP findings недоступны" text="Для этого нужны новые runs с включённым DLP." />
        )}
      </section>

      <section className="panel">
        <h3>Policy decisions</h3>
        {policyDecisions.length ? (
          <DataTable
            data={policyDecisions}
            columns={[
              { key: "case_id", title: "case_id", render: (row) => String(row.case_id ?? "—") },
              { key: "rule", title: "Rule", render: (row) => String(row.matched_rule_id ?? row.rule_id ?? "—") },
              { key: "action", title: "Action", render: (row) => String(row.action ?? "—") },
              { key: "severity", title: "Severity", render: (row) => String(row.severity ?? "—") },
              { key: "evidence", title: "Evidence", render: (row) => String(row.evidence_redacted ?? "—") },
            ]}
          />
        ) : (
          <EmptyState title="Policy decisions недоступны" text="Для этого нужны новые runs с включённым policy-as-code." />
        )}
      </section>

      <section className="panel">
        <div className="panel__header">
          <h3>
            <Terminal size={19} />
            Логи
          </h3>
        </div>
        {logs.stdout || logs.stderr ? (
          <div className="logs-grid">
            <pre>{logs.stdout || "stdout.log недоступен"}</pre>
            <pre>{logs.stderr || "stderr.log недоступен"}</pre>
          </div>
        ) : (
          <EmptyState title="Логи недоступны" text="stdout.log и stderr.log пока не найдены." />
        )}
      </section>
    </div>
  );
}
