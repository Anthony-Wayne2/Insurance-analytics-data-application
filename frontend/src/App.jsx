import { useState } from "react";
import Header from "./components/layout/Header";
import FilterBar from "./components/layout/FilterBar";
import KpiRow from "./components/kpi/KpiRow";

export default function App() {
  const [filters, setFilters] = useState({
    startDate: null,
    endDate: null,
    state: null,
    status: null,
  });

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <FilterBar filters={filters} setFilters={setFilters} />

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        <KpiRow filters={filters} />

        {/* Placeholder for the charts grid — added next */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-dashed border-slate-300 bg-white/60 p-10 text-center text-sm text-slate-400">
            MonthlyClaimsChart coming next
          </div>
          <div className="rounded-xl border border-dashed border-slate-300 bg-white/60 p-10 text-center text-sm text-slate-400">
            StatusDonut coming next
          </div>
        </div>
      </main>
    </div>
  );
}
