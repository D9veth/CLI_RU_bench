import {
  BarChart3,
  FolderArchive,
  Boxes,
  Database,
  Home,
  PlayCircle,
  Settings,
  Shield,
  Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { canManageUsers } from "../auth/roleGuards";

const items = [
  { to: "/dashboard", label: "Обзор", icon: Home },
  { to: "/runs", label: "Запуски", icon: PlayCircle },
  { to: "/results", label: "Результаты", icon: BarChart3 },
  { to: "/artifacts", label: "Артефакты", icon: FolderArchive },
  { to: "/datasets", label: "Датасеты", icon: Database },
  { to: "/configs", label: "Конфигурации", icon: Shield },
  { to: "/models", label: "Модели", icon: Boxes },
  { to: "/settings", label: "Настройки", icon: Settings },
];

export function Sidebar() {
  const { user } = useAuth();
  const visibleItems = canManageUsers(user)
    ? [...items.slice(0, 7), { to: "/users", label: "Пользователи", icon: Users }, items[7]]
    : items;

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand__mark">LB</div>
        <div>
          <strong>LLM Bench</strong>
          <span>Safety & Utility Evaluation</span>
        </div>
      </div>
      <nav className="sidebar__nav">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "active" : "")}>
              <Icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
