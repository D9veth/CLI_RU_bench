import { Server, UserCircle } from "lucide-react";
import { getApiBaseUrl } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";

export function Settings() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingState />;
  if (!user) return <EmptyState title="Сессия недоступна" text="Войдите заново, чтобы увидеть настройки текущего пользователя." />;

  return (
    <div className="page-stack">
      <section className="panel settings-grid">
        <div className="settings-card">
          <Server size={24} />
          <h3>API backend</h3>
          <code>{getApiBaseUrl()}</code>
          <p>Задаётся через `VITE_API_BASE_URL`.</p>
        </div>
        <div className="settings-card">
          <UserCircle size={24} />
          <h3>Текущий пользователь</h3>
          <p>
            {user.username} · {user.role}
          </p>
          <p>{user.email || "email не указан"}</p>
        </div>
      </section>
    </div>
  );
}
