import { useEffect, useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { api } from "../../api/client";
import Card from "../ui/Card";
import Spinner from "../ui/Spinner";
import ErrorBanner from "../ui/ErrorBanner";
import { formatCurrencyCompact, formatNumber } from "../ui/format";
import { useChartTheme } from "../../hooks/useChartTheme";

export default function MonthlyClaimsChart({ filters }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const t = useChartTheme();

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.monthlyClaims(filters)
      .then((rows) => !cancelled && setData(rows))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [filters]);

  return (
    <Card title="Monthly Claim Volume" subtitle="Claims submitted per calendar month">
      {loading && <Spinner />}
      {error && <ErrorBanner message={error} />}
      {!loading && !error && (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={t.grid} />
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: t.axisText }} tickLine={false} />
            <YAxis
              tick={{ fontSize: 12, fill: t.axisText }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => formatNumber(v)}
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
              formatter={(value, name) => {
                if (name === "claims") return [formatNumber(value), "Claims"];
                if (name === "claimed_value") return [formatCurrencyCompact(value), "Claimed"];
                return [value, name];
              }}
            />
            <Line
              type="monotone"
              dataKey="claims"
              stroke={t.sky}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
