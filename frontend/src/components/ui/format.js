// ==================================================================
// Shared display formatters — used by every KPI card and table.
// ==================================================================

export function formatNumber(n, options = {}) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
    ...options,
  }).format(n);
}

export function formatCurrency(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatCurrencyCompact(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000)     return `$${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000)         return `$${(n / 1_000).toFixed(1)}K`;
  return formatCurrency(n);
}

export function formatPercent(n, digits = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${Number(n).toFixed(digits)}%`;
}

export function formatByType(value, type) {
  switch (type) {
    case "number":    return formatNumber(value);
    case "currency":  return formatCurrency(value);
    case "compact":   return formatCurrencyCompact(value);
    case "percent":   return formatPercent(value);
    default:          return String(value ?? "—");
  }
}
