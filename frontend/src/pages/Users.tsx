import { FormEvent, useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import type { User, UserRole } from "../api/types";
import { DataTable } from "../components/DataTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { errorMessage } from "./utils";

export function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "viewer" as UserRole });

  async function load() {
    setUsers(await apiGet<User[]>("/api/auth/users/"));
  }

  useEffect(() => {
    load()
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await apiPost<User>("/api/auth/users/", form);
    setShowForm(false);
    setForm({ username: "", email: "", password: "", role: "viewer" });
    await load();
  }

  async function updateRole(user: User, role: UserRole) {
    await apiPatch<User>(`/api/auth/users/${user.id}/`, { role });
    await load();
  }

  async function deactivate(user: User) {
    await apiDelete(`/api/auth/users/${user.id}/`);
    await load();
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page-stack">
      <section className="toolbar panel">
        <button className="primary-button" onClick={() => setShowForm((value) => !value)}>
          <Plus size={18} />
          Создать пользователя
        </button>
      </section>
      {showForm ? (
        <section className="panel form-panel">
          <h3>Новый пользователь</h3>
          <form className="form-grid two-columns" onSubmit={(event) => void onSubmit(event)}>
            <label>
              username
              <input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} required />
            </label>
            <label>
              email
              <input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </label>
            <label>
              password
              <input value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} type="password" required />
            </label>
            <label>
              role
              <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}>
                <option value="viewer">viewer</option>
                <option value="researcher">researcher</option>
                <option value="admin">admin</option>
              </select>
            </label>
            <div className="form-actions wide">
              <button className="primary-button" type="submit">
                Создать
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <section className="panel">
        <DataTable
          data={users}
          columns={[
            { key: "username", title: "username", render: (user) => <strong>{user.username}</strong> },
            { key: "email", title: "email", render: (user) => user.email || "—" },
            {
              key: "role",
              title: "role",
              render: (user) => (
                <select value={user.role} onChange={(event) => void updateRole(user, event.target.value as UserRole)}>
                  <option value="viewer">viewer</option>
                  <option value="researcher">researcher</option>
                  <option value="admin">admin</option>
                </select>
              ),
            },
            { key: "active", title: "is_active", render: (user) => (user.is_active ? "Да" : "Нет") },
            { key: "staff", title: "is_staff", render: (user) => (user.is_staff ? "Да" : "Нет") },
            {
              key: "actions",
              title: "Действия",
              render: (user) => (
                <button className="icon-button small" title="Деактивировать" onClick={() => void deactivate(user)}>
                  <Trash2 size={16} />
                </button>
              ),
            },
          ]}
        />
      </section>
    </div>
  );
}
