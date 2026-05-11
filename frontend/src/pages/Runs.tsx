import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PauseCircle, PlayCircle, Plus, RefreshCw } from "lucide-react";
import { apiGet, apiPost } from "../api/client";
import type { BenchmarkRun, Dataset, DefenseProfile, ModelEndpoint, RunStatus } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { canCreateRun, canStartRun } from "../auth/roleGuards";
import { DataTable } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import { errorMessage, formatDate, formatLatencySeconds, formatMetric, toQuery } from "./utils";

interface Filters {
  status: string;
  model_endpoint: string;
  dataset: string;
  defense_profile: string;
}

export function Runs() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [runs, setRuns] = useState<BenchmarkRun[]>([]);
  const [models, setModels] = useState<ModelEndpoint[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [profiles, setProfiles] = useState<DefenseProfile[]>([]);
  const [filters, setFilters] = useState<Filters>({ status: "", model_endpoint: "", dataset: "", defense_profile: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadRuns(nextFilters = filters) {
    setError("");
    const query = toQuery(nextFilters);
    const data = await apiGet<BenchmarkRun[]>(`/api/runs/${query}`);
    setRuns(data);
  }

  useEffect(() => {
    Promise.all([
      loadRuns(),
      apiGet<ModelEndpoint[]>("/api/model-endpoints/").then(setModels),
      apiGet<Dataset[]>("/api/datasets/").then(setDatasets),
      apiGet<DefenseProfile[]>("/api/defense-profiles/").then(setProfiles),
    ])
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function updateFilter(key: keyof Filters, value: string) {
    const next = { ...filters, [key]: value };
    setFilters(next);
    try {
      await loadRuns(next);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function startRun(run: BenchmarkRun) {
    await apiPost<BenchmarkRun>(`/api/runs/${run.id}/start/`);
    await loadRuns();
  }

  async function cancelRun(run: BenchmarkRun) {
    await apiPost<BenchmarkRun>(`/api/runs/${run.id}/cancel/`);
    await loadRuns();
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page-stack">
      <section className="toolbar panel">
        <input className="search-input" placeholder="Поиск по названию запуска..." onChange={() => undefined} />
        <select value={filters.model_endpoint} onChange={(event) => void updateFilter("model_endpoint", event.target.value)}>
          <option value="">Модель: все</option>
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.display_name ?? model.model_name ?? model.name}
            </option>
          ))}
        </select>
        <select value={filters.defense_profile} onChange={(event) => void updateFilter("defense_profile", event.target.value)}>
          <option value="">Профиль: все</option>
          {profiles.map((profile) => (
            <option key={profile.id} value={profile.id}>
              {profile.level} {profile.name}
            </option>
          ))}
        </select>
        <select value={filters.dataset} onChange={(event) => void updateFilter("dataset", event.target.value)}>
          <option value="">Датасет: все</option>
          {datasets.map((dataset) => (
            <option key={dataset.id} value={dataset.id}>
              {dataset.name}
            </option>
          ))}
        </select>
        <select value={filters.status} onChange={(event) => void updateFilter("status", event.target.value as RunStatus)}>
          <option value="">Статус: все</option>
          <option value="pending">Очередь</option>
          <option value="running">В процессе</option>
          <option value="completed">Завершён</option>
          <option value="failed">Ошибка</option>
          <option value="cancelled">Отменён</option>
        </select>
        <button className="secondary-button" onClick={() => void loadRuns()}>
          <RefreshCw size={17} />
          Обновить
        </button>
        {canCreateRun(user) ? (
          <button className="primary-button" onClick={() => navigate("/runs/new")}>
            <Plus size={18} />
            Новый запуск
          </button>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel__header">
          <h3>Список запусков</h3>
          <span>{runs.length} записей</span>
        </div>
        <DataTable
          data={runs}
          columns={[
            { key: "run_id", title: "Run ID", render: (run) => <Link to={`/runs/${run.id}`}>{run.run_id}</Link> },
            { key: "title", title: "Название", render: (run) => run.title },
            { key: "model", title: "Модель", render: (run) => run.model_endpoint_name },
            { key: "dataset", title: "Датасет", render: (run) => run.dataset_name },
            { key: "profile", title: "Профиль", render: (run) => run.defense_profile_name },
            { key: "status", title: "Статус", render: (run) => <StatusBadge status={run.status} /> },
            { key: "proxy", title: "proxy-ASR", render: (run) => formatMetric(run.metrics?.proxy_asr) },
            { key: "fpr", title: "FPR", render: (run) => formatMetric(run.metrics?.fpr) },
            { key: "u", title: "U_mean", render: (run) => formatMetric(run.metrics?.u_mean) },
            { key: "p95", title: "p95, с", render: (run) => formatLatencySeconds(run.metrics?.p95_latency) },
            { key: "date", title: "Создан", render: (run) => formatDate(run.created_at) },
            {
              key: "actions",
              title: "Действия",
              render: (run) => (
                <div className="row-actions">
                  {canStartRun(user) && run.can_start ? (
                    <button className="icon-button small" title="Запустить" onClick={() => void startRun(run)}>
                      <PlayCircle size={17} />
                    </button>
                  ) : null}
                  {canStartRun(user) && run.can_cancel ? (
                    <button className="icon-button small" title="Отменить" onClick={() => void cancelRun(run)}>
                      <PauseCircle size={17} />
                    </button>
                  ) : null}
                </div>
              ),
            },
          ]}
        />
      </section>
    </div>
  );
}
