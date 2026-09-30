// ==================================================================
// API client — wraps every backend endpoint in a typed function.
// The base URL can be overridden with VITE_API_URL in .env.local.
// ==================================================================

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function buildQuery(params = {}) {
  const cleaned = Object.fromEntries(
    Object.entries(params).filter(
      ([, v]) => v !== null && v !== undefined && v !== ""
    )
  );
  const qs = new URLSearchParams(cleaned).toString();
  return qs ? `?${qs}` : "";
}

async function get(path, params) {
  const url = `${BASE_URL}${path}${buildQuery(params)}`;
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  // ---- KPIs ----
  kpiClaims:          (f) => get("/api/kpis/claims", f),
  kpiPayments:        (f) => get("/api/kpis/payments", f),
  kpiRates:           (f) => get("/api/kpis/rates", f),
  kpiPending:         ()  => get("/api/kpis/pending"),
  kpiPatients:        ()  => get("/api/kpis/patients"),
  kpiPaymentLag:      ()  => get("/api/kpis/payment-lag"),

  // ---- Charts ----
  monthlyClaims:      (f) => get("/api/charts/monthly-claims", f),
  momGrowth:          ()  => get("/api/charts/mom-growth"),
  status:             (f) => get("/api/charts/status", f),
  topProviders:       (f) => get("/api/charts/top-providers", f),
  specialty:          ()  => get("/api/charts/specialty"),
  providersPerState:  ()  => get("/api/charts/providers-per-state"),
  state:              (f) => get("/api/charts/state", f),
  topPayoutStates:    ()  => get("/api/charts/top-payout-states"),
  topPatients:        ()  => get("/api/charts/top-patients"),
  ageBands:           ()  => get("/api/charts/age-bands"),
  paymentLagHistogram:()  => get("/api/charts/payment-lag-histogram"),
  paidVsUnpaid:       ()  => get("/api/charts/paid-vs-unpaid"),

  // ---- Filters ----
  states:             ()  => get("/api/filters/states"),
  statuses:           ()  => get("/api/filters/statuses"),
  specialties:        ()  => get("/api/filters/specialties"),
};
