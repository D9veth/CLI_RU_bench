import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PlayCircle, Save } from "lucide-react";
import { apiGet, apiPost } from "../api/client";
import type { BenchmarkRun, Dataset, DefenseProfile, ModelEndpoint } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { errorMessage, safeJsonParse } from "./utils";

export function NewRun() {
  const navigate = useNavigate();
  const [models, setModels] = useState<ModelEndpoint[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [profiles, setProfiles] = useState<DefenseProfile[]>([]);
  const [createdRun, setCreatedRun] = useState<BenchmarkRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "",
    model_endpoint: "",
    dataset: "",
    defense_profile: "",
    temperature: "0.2",
    max_tokens: "128",
    extra_params: "{\n  \"repeats\": 1\n}",
  });

  useEffect(() => {
    Promise.all([
      apiGet<ModelEndpoint[]>("/api/model-endpoints/").then(setModels),
      apiGet<Dataset[]>("/api/datasets/").then(setDatasets),
      apiGet<DefenseProfile[]>("/api/defense-profiles/").then(setProfiles),
    ])
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  function update(key: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const payload = {
        title: form.title,
        model_endpoint: Number(form.model_endpoint),
        dataset: Number(form.dataset),
        defense_profile: Number(form.defense_profile),
        temperature: form.temperature ? Number(form.temperature) : null,
        max_tokens: form.max_tokens ? Number(form.max_tokens) : null,
        extra_params: safeJsonParse(form.extra_params),
      };
      const run = await apiPost<BenchmarkRun>("/api/runs/", payload);
      setCreatedRun(run);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function startRun() {
    if (!createdRun) return;
    const run = await apiPost<BenchmarkRun>(`/api/runs/${createdRun.id}/start/`);
    navigate(`/runs/${run.id}`);
  }

  if (loading) return <LoadingState />;
  if (error && !createdRun) return <ErrorState message={error} />;
  if (!models.length || !datasets.length || !profiles.length) {
    return (
      <EmptyState
        title="Недостаточно данных для запуска"
        text="Добавьте хотя бы одну модель, датасет и профиль защиты или выполните seed_demo_data."
      />
    );
  }

  return (
    <div className="page-stack">
      <section className="panel form-panel">
        <h3>Параметры запуска</h3>
        <form className="form-grid two-columns" onSubmit={onSubmit}>
          <label className="wide">
            Название
            <input value={form.title} onChange={(event) => update("title", event.target.value)} required placeholder="Smoke run D1" />
          </label>
          <label>
            Модель
            <select value={form.model_endpoint} onChange={(event) => update("model_endpoint", event.target.value)} required>
              <option value="">Выберите модель</option>
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.display_name ?? `${model.name} · ${model.model_name}`}
                </option>
              ))}
            </select>
          </label>
          <label>
            Датасет
            <select value={form.dataset} onChange={(event) => update("dataset", event.target.value)} required>
              <option value="">Выберите датасет</option>
              {datasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Профиль защиты
            <select value={form.defense_profile} onChange={(event) => update("defense_profile", event.target.value)} required>
              <option value="">Выберите профиль</option>
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.level} · {profile.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Temperature
            <input value={form.temperature} onChange={(event) => update("temperature", event.target.value)} type="number" step="0.01" min="0" />
          </label>
          <label>
            Max tokens
            <input value={form.max_tokens} onChange={(event) => update("max_tokens", event.target.value)} type="number" min="1" />
          </label>
          <label className="wide">
            Extra params JSON
            <textarea value={form.extra_params} onChange={(event) => update("extra_params", event.target.value)} rows={8} />
          </label>
          {error ? <div className="form-error wide">{error}</div> : null}
          <div className="form-actions wide">
            <button className="primary-button" type="submit">
              <Save size={18} />
              Создать запуск
            </button>
          </div>
        </form>
      </section>

      {createdRun ? (
        <section className="panel success-panel">
          <h3>Запуск создан</h3>
          <p>
            <code>{createdRun.run_id}</code> создан в статусе <strong>{createdRun.status}</strong>.
          </p>
          <div className="row-actions">
            <button className="primary-button" onClick={() => void startRun()}>
              <PlayCircle size={18} />
              Запустить
            </button>
            <button className="secondary-button" onClick={() => navigate(`/runs/${createdRun.id}`)}>
              Открыть карточку
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
