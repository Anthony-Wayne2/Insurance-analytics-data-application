import { formatByType } from "../ui/format";

export default function KpiCard({
  label,
  value,
  format = "number",
  accent = false,
  loading = false,
  trend = null,   // { value: 12.4, direction: "up" | "down" }
  hint = null,
}) {
  const display = loading ? "…" : formatByType(value, format);

  const baseCls =
    "rounded-xl border p-5 shadow-sm transition-colors min-h-[104px] flex flex-col justify-between";
  const variantCls = accent
    ? "bg-sky-50 border-sky-200"
    : "bg-white border-slate-200";

  return (
    <div className={`${baseCls} ${variantCls}`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {label}
        </p>
        {trend && <TrendBadge {...trend} />}
      </div>

      <div>
        <p
          className={`text-2xl font-semibold tabular-nums ${
            accent ? "text-sky-700" : "text-slate-900"
          }`}
        >
          {display}
        </p>
        {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
      </div>
    </div>
  );
}

function TrendBadge({ value, direction = "up" }) {
  const isUp = direction === "up";
  const color = isUp ? "text-emerald-600" : "text-rose-600";
  const arrow = isUp ? "▲" : "▼";
  return (
    <span className={`text-xs font-medium ${color}`}>
      {arrow} {Math.abs(value).toFixed(1)}%
    </span>
  );
}
