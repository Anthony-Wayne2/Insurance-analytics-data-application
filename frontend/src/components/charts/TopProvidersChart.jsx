import { useEffect, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { api } from "../../api/client";
import Card from "../ui/Card";
import Spinner from "../ui/Spinner";
import ErrorBanner from "../ui/ErrorBanner";
import { formatCurrencyCompact } from "../ui/format";
import { useChartTheme } from "../../hooks/useChartTheme";

export default function TopProvidersChart({ filters }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const t = useChartTheme();

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.topProviders(filters)
      .then((rows) => !cancelled && setData(rows))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [filters]);

  return (
    <Card title="Top 10 Providers by Claim Value" subtitle="Highest-value providers in view">
      {loading && <Spinner />}
      {error && <ErrorBanner message={error} />}
      {!loading && !error && data.length === 0 && (
        <p className="text-sm text-slate-400 dark:text-slate-500 py-8 text-center">
          No providers match the current filters.
        </p>
      )}
      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={t.grid} horizontal={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: t.axisText }}
              tickFormatter={(v) => formatCurrencyCompact(v)}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="provider_name"
              width={160}
              tick={{ fontSize: 11, fill: t.axisTextStrong }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: t.tooltipBg,
                border: `1px solid ${t.tooltipBorder}`,
                color: t.tooltipText,
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: t.tooltipText }}
              formatter={(value, name) =>
                name === "total_claimed"
                  ? [formatCurrencyCompact(value), "Claimed"]
                  : [value, name]
              }
              labelFormatter={(label, payload) => {
                const row = payload?.[0]?.payload;
                return row ? `${label} · ${row.specialty}` : label;
              }}
            />
            <Bar dataKey="total_claimed" fill={t.sky} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
