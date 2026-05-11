import { FormEvent, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { apiGet, apiPost } from "../api/client";
import type { Dataset } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { canEditDictionaries } from "../auth/roleGuards";
import { DataTable } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { errorMessage, formatDate, formatInteger } from "./utils";

export function Datasets() {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    slug: "",
    file_path: "",
    dataset_type: "unknown",
    total_cases: "0",
    attack_cases: "0",
    benign_cases: "0",
    utility_cases: "0",
  });

  async function load() {
    setDatasets(await apiGet<Dataset[]>("/api/datasets/"));
  }

  useEffect(() => {
    load()
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await apiPost<Dataset>("/api/datasets/", {
      ...form,
      total_cases: Number(form.total_cases),
      attack_cases: Number(form.attack_cases),
      benign_cases: Number(form.benign_cases),
      utility_cases: Number(form.utility_cases),
    });
    setShowForm(false);
    await load();
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page-stack">
      <section className="toolbar panel">
        <input className="search-input" placeholder="Поиск по датасетам..." onChange={() => undefined} />
        {canEditDictionaries(user) ? (
          <button className="primary-button" onClick={() => setShowForm((value) => !value)}>
            <Plus size={18} />
            Добавить датасет
          </button>
        ) : null}
      </section>

      {showForm ? (
        <section className="panel form-panel">
          <h3>Новый датасет</h3>
          <form className="form-grid two-columns" onSubmit={(event) => void onSubmit(event)}>
            {(["name", "slug", "file_path"] as const).map((key) => (
              <label key={key}>
                {key}
                <input value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} required />
              </label>
            ))}
            <label>
              Тип
              <select value={form.dataset_type} onChange={(event) => setForm({ ...form, dataset_type: event.target.value })}>
                <option value="full">full</option>
                <option value="pilot">pilot</option>
                <option value="sample">sample</option>
                <option value="generated">generated</option>
                <option value="unknown">unknown</option>
              </select>
            </label>
            {(["total_cases", "attack_cases", "benign_cases", "utility_cases"] as const).map((key) => (
              <label key={key}>
                {key}
                <input value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} type="number" min="0" />
              </label>
            ))}
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
          data={datasets}
          columns={[
            { key: "name", title: "Название", render: (dataset) => <strong>{dataset.name}</strong> },
            { key: "type", title: "Тип", render: (dataset) => <span className="pill">{dataset.dataset_type}</span> },
            { key: "total", title: "Всего кейсов", render: (dataset) => formatInteger(dataset.total_cases) },
            { key: "attack", title: "Атаки", render: (dataset) => formatInteger(dataset.attack_cases) },
            { key: "benign", title: "Benign", render: (dataset) => formatInteger(dataset.benign_cases) },
            { key: "utility", title: "Utility", render: (dataset) => formatInteger(dataset.utility_cases) },
            { key: "path", title: "Файл", render: (dataset) => <code>{dataset.file_path}</code> },
            { key: "active", title: "Статус", render: (dataset) => (dataset.is_active ? "Активен" : "Выключен") },
            { key: "updated", title: "Обновлён", render: (dataset) => formatDate(dataset.updated_at) },
          ]}
        />
      </section>
    </div>
  );
}
