import { FormEvent, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { apiGet, apiPost } from "../api/client";
import type { ModelEndpoint } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { canEditDictionaries } from "../auth/roleGuards";
import { DataTable } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { errorMessage, formatDate } from "./utils";

export function Models() {
  const { user } = useAuth();
  const [models, setModels] = useState<ModelEndpoint[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    slug: "",
    provider: "openai_compatible",
    model_name: "",
    base_url: "",
    default_temperature: "0.2",
    default_max_tokens: "1024",
  });

  async function load() {
    setModels(await apiGet<ModelEndpoint[]>("/api/model-endpoints/"));
  }

  useEffect(() => {
    load()
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await apiPost<ModelEndpoint>("/api/model-endpoints/", {
      ...form,
      default_temperature: Number(form.default_temperature),
      default_max_tokens: Number(form.default_max_tokens),
    });
    setShowForm(false);
    await load();
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page-stack">
      <section className="toolbar panel">
        <input className="search-input" placeholder="Поиск по названию модели или endpoint" onChange={() => undefined} />
        {canEditDictionaries(user) ? (
          <button className="primary-button" onClick={() => setShowForm((value) => !value)}>
            <Plus size={18} />
            Добавить модель
          </button>
        ) : null}
      </section>
      {showForm ? (
        <section className="panel form-panel">
          <h3>Новый model endpoint</h3>
          <form className="form-grid two-columns" onSubmit={(event) => void onSubmit(event)}>
            {(["name", "slug", "model_name", "base_url", "default_temperature", "default_max_tokens"] as const).map((key) => (
              <label key={key}>
                {key}
                <input value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} required />
              </label>
            ))}
            <label>
              provider
              <select value={form.provider} onChange={(event) => setForm({ ...form, provider: event.target.value })}>
                <option value="lmstudio">lmstudio</option>
                <option value="ollama">ollama</option>
                <option value="openai_compatible">openai_compatible</option>
                <option value="other">other</option>
              </select>
            </label>
            <div className="form-actions wide">
              <button className="primary-button" type="submit">
                Сохранить
              </button>
            </div>
          </form>
        </section>
      ) : null}
      <section className="panel">
        <DataTable
          data={models}
          columns={[
            { key: "name", title: "Модель", render: (model) => <strong>{model.display_name ?? model.model_name ?? model.name}</strong> },
            { key: "endpoint", title: "Endpoint", render: (model) => model.name },
            { key: "provider", title: "Провайдер", render: (model) => <span className="pill">{model.provider}</span> },
            { key: "model", title: "model_name", render: (model) => model.model_name },
            { key: "base", title: "base_url", render: (model) => <code>{model.base_url}</code> },
            { key: "temp", title: "temperature", render: (model) => model.default_temperature },
            { key: "tokens", title: "max_tokens", render: (model) => model.default_max_tokens },
            { key: "status", title: "Проверка", render: (model) => model.last_check_status || "—" },
            { key: "active", title: "Статус", render: (model) => (model.is_active ? "Активна" : "Выключена") },
            { key: "updated", title: "Обновлена", render: (model) => formatDate(model.updated_at) },
          ]}
        />
      </section>
    </div>
  );
}
