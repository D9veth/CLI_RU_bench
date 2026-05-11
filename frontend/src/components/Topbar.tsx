import { LogOut, Settings } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const titles: Record<string, { title: string; subtitle: string }> = {
  "/dashboard": { title: "Обзор", subtitle: "Краткая сводка по запускам, моделям и результатам оценки." },
  "/runs": { title: "Запуски", subtitle: "Просмотр benchmark-запусков, статусов и ключевых метрик." },
  "/runs/new": { title: "Новый запуск", subtitle: "Создание pending-запуска на основе модели, датасета и профиля защиты." },
  "/results": { title: "Результаты", subtitle: "Аналитика завершённых запусков и сравнение метрик." },
  "/artifacts": { title: "Артефакты", subtitle: "Файлы датасетов, конфигов, запусков, отчётов, таблиц и графиков." },
  "/datasets": { title: "Датасеты", subtitle: "Управление датасетами для оценки безопасности и полезности." },
  "/configs": { title: "Конфигурации", subtitle: "Профили защиты и параметры запусков." },
  "/models": { title: "Модели", subtitle: "Доступные model endpoints и их параметры." },
  "/users": { title: "Пользователи", subtitle: "Управление аккаунтами и ролями." },
  "/settings": { title: "Настройки", subtitle: "Параметры подключения frontend и текущая сессия." },
};

export function Topbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const page = titles[location.pathname] ?? (location.pathname.startsWith("/runs/") ? titles["/runs"] : titles["/dashboard"]);

  return (
    <header className="topbar">
      <div>
        <h1>{page.title}</h1>
        <p>{page.subtitle}</p>
      </div>
      <div className="topbar__actions">
        <button className="icon-button" title="Настройки" onClick={() => navigate("/settings")}>
          <Settings size={20} />
        </button>
        <div className="user-chip">
          <div className="avatar">{user?.username.slice(0, 2).toUpperCase()}</div>
          <div>
            <strong>{user?.username}</strong>
            <span>{user?.role}</span>
          </div>
        </div>
        <button
          className="icon-button"
          title="Выйти"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
}
