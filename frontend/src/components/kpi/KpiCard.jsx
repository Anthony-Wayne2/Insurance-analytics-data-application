import { formatByType } from "../ui/format";

export default function KpiCard({
  label,
  value,
  format = "number",
  accent = false,
  loading = false,
  trend = null,
  hint = null,
}) {
  const display = loading ? "…" : formatByType(value, format);

  const baseCls =
    "rounded-xl border p-5 shadow-sm transition-colors min-h-[104px] flex flex-col justify-between";
  const variantCls = accent
    ? "bg-sky-50 dark:bg-sky-950/40 border-sky-200 dark:border-sky-900/60"
    : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800";

  return (
    <div className={`${baseCls} ${variantCls}`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </p>
        {trend && <TrendBadge {...trend} />}
      </div>

      <div>
        <p
          className={`text-2xl font-semibold tabular-nums ${
            accent
              ? "text-sky-700 dark:text-sky-300"
              : "text-slate-900 dark:text-slate-100"
          }`}
        >
          {display}
        </p>
        {hint && (
          <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
            {hint}
          </p>
        )}
      </div>
    </div>
  );
}

function TrendBadge({ value, direction = "up" }) {
  const isUp = direction === "up";
  const color = isUp
    ? "text-emerald-600 dark:text-emerald-400"
    : "text-rose-600 dark:text-rose-400";
  const arrow = isUp ? "▲" : "▼";
  return (
    <span className={`text-xs font-medium ${color}`}>
      {arrow} {Math.abs(value).toFixed(1)}%
    </span>
  );
}
