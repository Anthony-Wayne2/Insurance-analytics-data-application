import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { api } from "../../api/client";
import Card from "../ui/Card";
import Spinner from "../ui/Spinner";
import ErrorBanner from "../ui/ErrorBanner";
import { formatCurrencyCompact, formatNumber } from "../ui/format";

export default function StateChart({ filters }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    api
      .state(filters)
      .then((rows) => {
        if (cancelled) return;
        // Show top 10 states by total claimed
        const top10 = [...rows]
          .sort((a, b) => (b.total_claimed || 0) - (a.total_claimed || 0))
          .slice(0, 10);
        setData(top10);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [filters]);

  return (
    <Card
      title="Claims by State"
      subtitle="Top 10 states by total claimed value"
    >
      {loading && <Spinner />}
      {error && <ErrorBanner message={error} />}
      {!loading && !error && data.length === 0 && (
        <p className="text-sm text-slate-400 py-8 text-center">
          No state data matches the current filters.
        </p>
      )}
      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={data}
            margin={{ top: 4, right: 8, left: 0, bottom: 48 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="state"
              tick={{ fontSize: 11, fill: "#334155" }}
              interval={0}
              angle={-45}
              textAnchor="end"
              height={70}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#64748b" }}
              tickFormatter={(v) => formatCurrencyCompact(v)}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: "1px solid #e2e8f0",
                fontSize: 12,
              }}
              formatter={(value, name, payload) => {
                if (name === "total_claimed") {
                  const n = payload?.payload?.claim_count;
                  return [
                    `${formatCurrencyCompact(value)}${n ? ` · ${formatNumber(n)} claims` : ""}`,
                    "Claimed",
                  ];
                }
                return [value, name];
              }}
            />
            <Bar
              dataKey="total_claimed"
              fill="#8b5cf6"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
