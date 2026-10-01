import { useState } from "react";
import Header from "./components/layout/Header";
import FilterBar from "./components/layout/FilterBar";
import KpiRow from "./components/kpi/KpiRow";
import MonthlyClaimsChart from "./components/charts/MonthlyClaimsChart";
import StatusDonut from "./components/charts/StatusDonut";
import TopProvidersChart from "./components/charts/TopProvidersChart";
import StateChart from "./components/charts/StateChart";

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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MonthlyClaimsChart filters={filters} />
          <StatusDonut filters={filters} />
          <TopProvidersChart filters={filters} />
          <StateChart filters={filters} />
        </div>
      </main>
    </div>
  );
}
