import { useState } from "react";
import Header from "./components/layout/Header";
import FilterBar from "./components/layout/FilterBar";
import KpiRow from "./components/kpi/KpiRow";
import MonthlyClaimsChart from "./components/charts/MonthlyClaimsChart";
import StatusDonut from "./components/charts/StatusDonut";
import TopProvidersChart from "./components/charts/TopProvidersChart";
import StateChart from "./components/charts/StateChart";
import SpecialtyChart from "./components/charts/SpecialtyChart";
import AgeBandsChart from "./components/charts/AgeBandsChart";
import TopPayoutStatesTable from "./components/tables/TopPayoutStatesTable";
import TopPatientsTable from "./components/tables/TopPatientsTable";

export default function App() {
  const [filters, setFilters] = useState({
    startDate: null,
    endDate: null,
    state: null,
    status: null,
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors">
      <Header />
      <FilterBar filters={filters} setFilters={setFilters} />

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        <KpiRow filters={filters} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MonthlyClaimsChart filters={filters} />
          <StatusDonut filters={filters} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TopProvidersChart filters={filters} />
          <StateChart filters={filters} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SpecialtyChart filters={filters} />
          <AgeBandsChart filters={filters} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TopPayoutStatesTable />
          <TopPatientsTable />
        </div>
      </main>
    </div>
  );
}
