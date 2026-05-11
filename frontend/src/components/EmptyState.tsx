import { Inbox } from "lucide-react";

export function EmptyState({ title = "Нет данных", text }: { title?: string; text?: string }) {
  return (
    <div className="state state-empty">
      <Inbox size={24} />
      <strong>{title}</strong>
      {text ? <p>{text}</p> : null}
    </div>
  );
}
