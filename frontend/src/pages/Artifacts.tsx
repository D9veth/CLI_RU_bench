import { useEffect, useMemo, useState } from "react";
import { Download, Eye, FolderSync } from "lucide-react";
import { Link } from "react-router-dom";
import { apiGet, apiGetBlob, apiPost } from "../api/client";
import type { ProjectArtifact, ProjectArtifactPreview, ProjectArtifactType, ProjectArtifactsResponse } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { canEditDictionaries } from "../auth/roleGuards";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { errorMessage, formatBytes, formatDate, formatInteger, toQuery } from "./utils";

const artifactTypes: Array<{ value: ProjectArtifactType; label: string }> = [
  { value: "dataset", label: "Датасет" },
  { value: "config", label: "Конфиг" },
  { value: "run_artifact", label: "Артефакт запуска" },
  { value: "report", label: "Отчёт" },
  { value: "table", label: "Таблица" },
  { value: "figure", label: "График" },
  { value: "json", label: "JSON" },
  { value: "jsonl", label: "JSONL" },
  { value: "log", label: "Лог" },
  { value: "markdown", label: "Markdown" },
  { value: "document", label: "Документ" },
  { value: "script", label: "Скрипт" },
  { value: "other", label: "Другое" },
];

function typeLabel(value: string) {
  return artifactTypes.find((type) => type.value === value)?.label ?? value;
}

export function Artifacts() {
  const { user } = useAuth();
  const [artifacts, setArtifacts] = useState<ProjectArtifact[]>([]);
  const [count, setCount] = useState(0);
  const [filters, setFilters] = useState({ artifact_type: "", source_dir: "", search: "" });
  const [selected, setSelected] = useState<ProjectArtifact | null>(null);
  const [preview, setPreview] = useState<ProjectArtifactPreview | null>(null);
  const [previewImageUrl, setPreviewImageUrl] = useState("");
  const [ingestSummary, setIngestSummary] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState("");

  async function load(nextFilters = filters) {
    setError("");
    const query = toQuery({ ...nextFilters, limit: 200 });
    const response = await apiGet<ProjectArtifactsResponse>(`/api/project-artifacts/${query}`);
    setArtifacts(response.results);
    setCount(response.count);
  }

  useEffect(() => {
    load()
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => () => {
    if (previewImageUrl) {
      URL.revokeObjectURL(previewImageUrl);
    }
  }, [previewImageUrl]);

  const sourceDirs = useMemo(() => [...new Set(artifacts.map((artifact) => artifact.source_dir).filter(Boolean))], [artifacts]);

  async function updateFilter(key: keyof typeof filters, value: string) {
    const next = { ...filters, [key]: value };
    setFilters(next);
    try {
      await load(next);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function importArtifacts() {
    setImporting(true);
    setError("");
    try {
      const summary = await apiPost<Record<string, unknown>>("/api/project-artifacts/ingest/", {
        dry_run: false,
        artifact_type: filters.artifact_type || undefined,
      });
      setIngestSummary(summary);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setImporting(false);
    }
  }

  async function showPreview(artifact: ProjectArtifact) {
    setSelected(artifact);
    setPreview(null);
    setPreviewLoading(true);
    if (previewImageUrl) {
      URL.revokeObjectURL(previewImageUrl);
      setPreviewImageUrl("");
    }
    try {
      const data = await apiGet<ProjectArtifactPreview>(`/api/project-artifacts/${artifact.id}/preview/`);
      setPreview(data);
      if (data.type === "image") {
        const blob = await apiGetBlob(`/api/project-artifacts/${artifact.id}/raw/`);
        setPreviewImageUrl(URL.createObjectURL(blob));
      }
    } catch (err) {
      setPreview({ message: errorMessage(err) });
    } finally {
      setPreviewLoading(false);
    }
  }

  async function openRaw(artifact: ProjectArtifact) {
    const blob = await apiGetBlob(`/api/project-artifacts/${artifact.id}/raw/`);
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page-stack">
      <section className="toolbar panel">
        <input
          className="search-input"
          placeholder="Поиск по имени или пути..."
          value={filters.search}
          onChange={(event) => void updateFilter("search", event.target.value)}
        />
        <select value={filters.artifact_type} onChange={(event) => void updateFilter("artifact_type", event.target.value)}>
          <option value="">Тип: все</option>
          {artifactTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        <select value={filters.source_dir} onChange={(event) => void updateFilter("source_dir", event.target.value)}>
          <option value="">Источник: все</option>
          {sourceDirs.map((source) => (
            <option key={source} value={source}>
              {source}
            </option>
          ))}
        </select>
        {canEditDictionaries(user) ? (
          <button className="primary-button" disabled={importing} onClick={() => void importArtifacts()}>
            <FolderSync size={18} />
            {importing ? "Импортируем..." : "Импортировать артефакты"}
          </button>
        ) : null}
      </section>

      {ingestSummary ? (
        <section className="info-note">
          <p>
            Импорт завершён: found={String(ingestSummary.found ?? "—")}, imported={String(ingestSummary.imported ?? "—")},
            updated={String(ingestSummary.updated ?? "—")}, skipped={String(ingestSummary.skipped ?? "—")}.
          </p>
        </section>
      ) : null}

      <section className="panel">
        <div className="panel__header">
          <h3>Артефакты проекта</h3>
          <span>{formatInteger(count)} записей</span>
        </div>
        <DataTable
          data={artifacts}
          emptyText="Артефакты пока не импортированы."
          columns={[
            { key: "name", title: "Имя", render: (artifact) => artifact.name },
            { key: "type", title: "Тип", render: (artifact) => <span className="pill">{typeLabel(artifact.artifact_type)}</span> },
            { key: "source", title: "Источник", render: (artifact) => artifact.source_dir || "—" },
            { key: "extension", title: "Расширение", render: (artifact) => artifact.extension || "—" },
            { key: "size", title: "Размер", render: (artifact) => formatBytes(artifact.size_bytes) },
            { key: "lines", title: "Строк", render: (artifact) => formatInteger(artifact.line_count) },
            {
              key: "run",
              title: "Запуск",
              render: (artifact) =>
                artifact.related_run ? <Link to={`/runs/${artifact.related_run}`}>{artifact.related_run_id}</Link> : "—",
            },
            { key: "updated", title: "Обновлён", render: (artifact) => formatDate(artifact.updated_at) },
            {
              key: "actions",
              title: "Действия",
              render: (artifact) => (
                <div className="row-actions">
                  <button className="icon-button small" title="Предпросмотр" onClick={() => void showPreview(artifact)}>
                    <Eye size={17} />
                  </button>
                  <button className="icon-button small" title="Открыть файл" onClick={() => void openRaw(artifact)}>
                    <Download size={17} />
                  </button>
                </div>
              ),
            },
          ]}
        />
      </section>

      {selected ? (
        <section className="panel preview-panel">
          <div className="panel__header">
            <h3>Предпросмотр: {selected.name}</h3>
            <button className="secondary-button" onClick={() => void openRaw(selected)}>
              Открыть файл
            </button>
          </div>
          <p className="muted">{selected.file_path}</p>
          {previewLoading ? <LoadingState label="Загружаем предпросмотр" /> : renderPreview(preview, previewImageUrl)}
        </section>
      ) : artifacts.length ? null : (
        <EmptyState title="Нет выбранного артефакта" text="После импорта выберите файл для предпросмотра." />
      )}
    </div>
  );
}

function renderPreview(preview: ProjectArtifactPreview | null, imageUrl: string) {
  if (!preview) {
    return <EmptyState title="Предпросмотр недоступен" />;
  }
  if (preview.type === "image" && imageUrl) {
    return <img className="artifact-image" src={imageUrl} alt="Предпросмотр артефакта" />;
  }
  if (preview.rows?.length) {
    const columns = preview.columns?.length ? preview.columns : Object.keys(preview.rows[0]);
    return (
      <DataTable<Record<string, unknown>>
        data={preview.rows}
        columns={columns.map((column) => ({
          key: column,
          title: column,
          render: (row) => String(row[column] ?? "—"),
        }))}
      />
    );
  }
  if (preview.text) {
    return <pre className="markdown-block">{preview.text}</pre>;
  }
  return <EmptyState title="Предпросмотр недоступен" text={preview.message ?? "Для этого типа файла доступно только открытие raw-файла."} />;
}
