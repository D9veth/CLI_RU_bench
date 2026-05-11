import clsx from "clsx";
import type { RunStatus } from "../api/types";

const labels: Record<RunStatus, string> = {
  pending: "Очередь",
  running: "В процессе",
  completed: "Завершён",
  failed: "Ошибка",
  cancelled: "Отменён",
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return <span className={clsx("status-badge", `status-${status}`)}>{labels[status] ?? status}</span>;
}
