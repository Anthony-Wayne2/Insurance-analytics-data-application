import { useEffect, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { api } from "../../api/client";
import Card from "../ui/Card";
import Spinner from "../ui/Spinner";
import ErrorBanner from "../ui/ErrorBanner";
import { formatNumber } from "../ui/format";
import { useChartTheme } from "../../hooks/useChartTheme";

export default function AgeBandsChart({ filters }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const t = useChartTheme();

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.ageBands(filters)
      .then((rows) => !cancelled && setData(rows))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [filters]);

  return (
    <Card title="Patients by Age Band" subtitle="Distinct patients with at least one claim in view">
      {loading && <Spinner />}
      {error && <ErrorBanner message={error} />}
      {!loading && !error && data.length === 0 && (
        <p className="text-sm text-slate-400 dark:text-slate-500 py-8 text-center">
          No patient activity in the current filters.
        </p>
      )}
      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={t.grid} vertical={false} />
            <XAxis
              dataKey="age_band"
              tick={{ fontSize: 12, fill: t.axisTextStrong }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: t.axisText }}
              tickFormatter={(v) => formatNumber(v)}
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
              formatter={(value) => [formatNumber(value), "Patients"]}
            />
            <Bar dataKey="patients" fill={t.amber} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
