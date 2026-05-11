import { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import { apiGet } from "../api/client";
import type { DefenseProfile } from "../api/types";
import { DataTable } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { errorMessage, formatDate } from "./utils";

const levelNotes = [
  { level: "D0", title: "Базовый режим", text: "Запуск без дополнительных ограничений." },
  { level: "D1", title: "Системная политика", text: "Системные инструкции и безопасные отказы." },
  { level: "D2", title: "Промежуточная защита", text: "Баланс ограничений, wrapping и фильтров." },
  { level: "D3", title: "Строгий профиль", text: "Максимально строгие проверки и постфильтрация." },
];

export function Configurations() {
  const [profiles, setProfiles] = useState<DefenseProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<DefenseProfile[]>("/api/defense-profiles/")
      .then(setProfiles)
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page-stack">
      <div className="cards-grid four">
        {levelNotes.map((note) => (
          <section key={note.level} className="panel level-card">
            <span>{note.level}</span>
            <h3>{note.title}</h3>
            <p>{note.text}</p>
          </section>
        ))}
      </div>

      <section className="panel">
        <div className="panel__header">
          <h3>
            <Shield size={19} />
            Профили защиты
          </h3>
        </div>
        <DataTable
          data={profiles}
          columns={[
            { key: "level", title: "Уровень", render: (profile) => <span className="pill">{profile.level}</span> },
            { key: "name", title: "Название", render: (profile) => <strong>{profile.name}</strong> },
            { key: "yaml", title: "YAML", render: (profile) => <code>{profile.yaml_path || "—"}</code> },
            { key: "description", title: "Описание", render: (profile) => profile.description || "—" },
            { key: "params", title: "parameters_json", render: (profile) => <code>{JSON.stringify(profile.parameters_json)}</code> },
            { key: "updated", title: "Обновлён", render: (profile) => formatDate(profile.updated_at) },
          ]}
        />
      </section>
    </div>
  );
}
