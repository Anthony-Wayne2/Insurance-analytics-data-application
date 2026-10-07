import { useEffect, useState } from "react";
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend,
} from "recharts";
import { api } from "../../api/client";
import Card from "../ui/Card";
import Spinner from "../ui/Spinner";
import ErrorBanner from "../ui/ErrorBanner";
import { formatNumber, formatCurrencyCompact } from "../ui/format";
import { useChartTheme } from "../../hooks/useChartTheme";

export default function StatusDonut({ filters }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const t = useChartTheme();

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.status(filters)
      .then((rows) => !cancelled && setData(rows))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [filters]);

  const colorFor = (status) => {
    if (status === "Approved") return t.emerald;
    if (status === "Pending") return t.amber;
    if (status === "Rejected") return t.rose;
    return t.sky;
  };

  const total = data.reduce((s, r) => s + (r.n || 0), 0);

  return (
    <Card
      title="Claims by Status"
      subtitle={total ? `${formatNumber(total)} claims in view` : undefined}
    >
      {loading && <Spinner />}
      {error && <ErrorBanner message={error} />}
      {!loading && !error && data.length === 0 && (
        <p className="text-sm text-slate-400 dark:text-slate-500 py-8 text-center">
          No claims match the current filters.
        </p>
      )}
      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={data}
              dataKey="n"
              nameKey="status"
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
            >
              {data.map((entry) => (
                <Cell key={entry.status} fill={colorFor(entry.status)} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: t.tooltipBg,
                border: `1px solid ${t.tooltipBorder}`,
                color: t.tooltipText,
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: t.tooltipText }}
              formatter={(value, name, payload) => [
                `${formatNumber(value)} (${formatCurrencyCompact(payload?.payload?.value || 0)})`,
                name,
              ]}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              wrapperStyle={{ fontSize: 12, color: t.axisText }}
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
