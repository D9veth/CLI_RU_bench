import { Loader2 } from "lucide-react";

export function LoadingState({ label = "Загружаем данные" }: { label?: string }) {
  return (
    <div className="state state-loading">
      <Loader2 className="spin" size={22} />
      <span>{label}</span>
    </div>
  );
}
