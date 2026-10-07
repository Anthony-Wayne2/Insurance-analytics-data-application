import { useEffect, useState } from "react";
import { api } from "../../api/client";
import Card from "../ui/Card";
import Spinner from "../ui/Spinner";
import ErrorBanner from "../ui/ErrorBanner";
import { formatCurrencyCompact, formatNumber } from "../ui/format";

export default function TopPatientsTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.topPatients()
      .then((rows) => !cancelled && setData(rows))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, []);

  return (
    <Card
      title="Top 10 Patients by Claim Value"
      subtitle="Highest-cost patients (potential care-management cases)"
    >
      {loading && <Spinner />}
      {error && <ErrorBanner message={error} />}
      {!loading && !error && data.length === 0 && (
        <p className="text-sm text-slate-400 dark:text-slate-500 py-8 text-center">
          No patient data available.
        </p>
      )}
      {!loading && !error && data.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-left text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                <th className="py-2 pr-4">Patient</th>
                <th className="py-2 pr-4">State</th>
                <th className="py-2 pr-4 text-right">Age</th>
                <th className="py-2 pr-4 text-right">Claims</th>
                <th className="py-2 text-right">Total Claimed</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr
                  key={row.patient_id}
                  className="border-b border-slate-100 dark:border-slate-800 last:border-b-0 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <td className="py-2 pr-4 font-medium text-slate-800 dark:text-slate-100">
                    {row.patient_name}
                  </td>
                  <td className="py-2 pr-4 text-slate-600 dark:text-slate-400">
                    {row.state}
                  </td>
                  <td className="py-2 pr-4 text-right tabular-nums text-slate-700 dark:text-slate-300">
                    {row.age}
                  </td>
                  <td className="py-2 pr-4 text-right tabular-nums text-slate-700 dark:text-slate-300">
                    {formatNumber(row.claim_count)}
                  </td>
                  <td className="py-2 text-right tabular-nums font-semibold text-sky-700 dark:text-sky-300">
                    {formatCurrencyCompact(row.total_claimed)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}