import { AlertTriangle } from "lucide-react";

export function ErrorState({ title = "Не удалось загрузить данные", message }: { title?: string; message?: string }) {
  return (
    <div className="state state-error">
      <AlertTriangle size={22} />
      <div>
        <strong>{title}</strong>
        {message ? <p>{message}</p> : null}
      </div>
    </div>
  );
}
