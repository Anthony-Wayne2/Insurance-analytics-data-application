import { useEffect, useState } from "react";
import { api } from "../../api/client";
import KpiCard from "./KpiCard";
import ErrorBanner from "../ui/ErrorBanner";
import { formatCurrency } from "../ui/format";

export default function KpiRow({ filters }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      api.kpiClaims(filters),
      api.kpiPayments(filters),
    ])
      .then(([claims, payments]) => {
        if (cancelled) return;
        setData({
          total_claims:       claims.total_claims,
          total_claimed:      claims.total_claimed,
          avg_claim_amount:   claims.avg_claim_amount,
          total_paid:         payments.total_paid,
          avg_payment_amount: payments.avg_payment_amount,
          payment_ratio:      payments.payment_ratio,
        });
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [filters]);

  if (error) {
    return (
      <ErrorBanner
        message={`Failed to load KPIs: ${error}`}
        onRetry={() => setLoading(true)}
      />
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <KpiCard
        label="Total Claims"
        value={data?.total_claims}
        format="number"
        loading={loading}
        hint={
          data?.avg_claim_amount
            ? `Avg claim: ${formatCurrency(data.avg_claim_amount)}`
            : undefined
        }
      />
      <KpiCard
        label="Total Claimed"
        value={data?.total_claimed}
        format="currency"
        loading={loading}
      />
      <KpiCard
        label="Total Paid"
        value={data?.total_paid}
        format="currency"
        loading={loading}
        hint={
          data?.avg_payment_amount
            ? `Avg payment: ${formatCurrency(data.avg_payment_amount)}`
            : undefined
        }
      />
      <KpiCard
        label="Payment Ratio"
        value={data?.payment_ratio}
        format="percent"
        accent
        loading={loading}
        hint="Paid ÷ Claimed"
      />
    </div>
  );
}
