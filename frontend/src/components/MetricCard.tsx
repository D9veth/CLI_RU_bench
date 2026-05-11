import clsx from "clsx";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  hint?: string;
  trend?: string;
  tone?: "blue" | "green" | "red" | "violet" | "orange";
  icon?: LucideIcon;
}

export function MetricCard({ title, value, hint, trend, tone = "blue", icon: Icon }: MetricCardProps) {
  return (
    <section className={clsx("metric-card", `tone-${tone}`)}>
      <div className="metric-card__header">
        <span>{title}</span>
        {Icon ? (
          <span className="metric-card__icon">
            <Icon size={20} />
          </span>
        ) : null}
      </div>
      <div className="metric-card__value">{value}</div>
      {trend || hint ? (
        <div className="metric-card__hint">
          {trend ? <strong>{trend}</strong> : null}
          {hint ? <span>{hint}</span> : null}
        </div>
      ) : null}
    </section>
  );
}
