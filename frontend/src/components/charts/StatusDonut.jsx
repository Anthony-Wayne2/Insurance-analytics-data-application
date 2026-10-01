import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";
import { api } from "../../api/client";
import Card from "../ui/Card";
import Spinner from "../ui/Spinner";
import ErrorBanner from "../ui/ErrorBanner";
import { formatNumber, formatCurrencyCompact } from "../ui/format";

const COLORS = {
  Approved: "#10b981", // emerald
  Pending:  "#f59e0b", // amber
  Rejected: "#ef4444", // red
};
const FALLBACK = ["#0ea5e9", "#8b5cf6", "#f97316", "#14b8a6"];

export default function StatusDonut({ filters }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    api
      .status(filters)
      .then((rows) => !cancelled && setData(rows))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [filters]);

  const total = data.reduce((sum, r) => sum + (r.n || 0), 0);

  return (
    <Card
      title="Claims by Status"
      subtitle={total ? `${formatNumber(total)} claims in view` : undefined}
    >
      {loading && <Spinner />}
      {error && <ErrorBanner message={error} />}
      {!loading && !error && data.length === 0 && (
        <p className="text-sm text-slate-400 py-8 text-center">
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
              {data.map((entry, idx) => (
                <Cell
                  key={entry.status}
                  fill={COLORS[entry.status] || FALLBACK[idx % FALLBACK.length]}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: "1px solid #e2e8f0",
                fontSize: 12,
              }}
              formatter={(value, name, payload) => [
                `${formatNumber(value)} (${formatCurrencyCompact(
                  payload?.payload?.value || 0
                )})`,
                name,
              ]}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              wrapperStyle={{ fontSize: 12 }}
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
