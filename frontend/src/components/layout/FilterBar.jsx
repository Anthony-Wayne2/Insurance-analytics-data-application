export default function FilterBar({ filters, setFilters }) {
  const update = (patch) => setFilters({ ...filters, ...patch });

  const reset = () =>
    setFilters({ startDate: null, endDate: null, state: null, status: null });

  const isDirty =
    filters.startDate || filters.endDate || filters.state || filters.status;

  const inputCls =
    "rounded-md border border-slate-300 dark:border-slate-700 " +
    "bg-white dark:bg-slate-900 " +
    "text-slate-800 dark:text-slate-100 " +
    "px-2 py-1 focus:outline-none focus:ring-2 focus:ring-sky-400";

  return (
    <div className="sticky top-0 z-10 bg-white/85 dark:bg-slate-900/85 backdrop-blur border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-6 py-3 flex flex-wrap items-center gap-4 text-sm">
        <label className="flex items-center gap-2">
          <span className="text-slate-600 dark:text-slate-300">From</span>
          <input
            type="date"
            className={inputCls}
            value={filters.startDate || ""}
            onChange={(e) => update({ startDate: e.target.value || null })}
          />
        </label>

        <label className="flex items-center gap-2">
          <span className="text-slate-600 dark:text-slate-300">To</span>
          <input
            type="date"
            className={inputCls}
            value={filters.endDate || ""}
            onChange={(e) => update({ endDate: e.target.value || null })}
          />
        </label>

        {isDirty && (
          <button
            onClick={reset}
            className="ml-auto rounded-md border border-slate-300 dark:border-slate-700 px-3 py-1 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            Reset filters
          </button>
        )}
      </div>
    </div>
  );
}