import { useState } from "react";
import MapSelector from "./components/MapSelector";
import AnalysisPanel from "./components/AnalysisPanel";
import ResultsDashboard from "./components/ResultsDashboard";
import LayerControls from "./components/LayerControls";
import TimeSeriesPanel from "./components/TimeSeriesPanel";
import ReportPanel from "./components/ReportPanel";
import AuthWidget from "./components/AuthWidget";

type Tab = "results" | "timeseries" | "report";

const TABS: { id: Tab; label: string }[] = [
  { id: "results", label: "Results" },
  { id: "timeseries", label: "Time-series" },
  { id: "report", label: "Report" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("results");

  return (
    <div className="min-h-screen xl:h-screen w-full flex flex-col bg-[#080d14] text-slate-100">
      <header className="min-h-16 shrink-0 flex items-center justify-between gap-4 px-4 sm:px-6 border-b border-slate-800/90 bg-slate-950/95">
        <div className="flex min-w-0 items-center gap-3">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-cyan-400/20 bg-cyan-400/10 text-cyan-300" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth="1.7">
              <circle cx="12" cy="12" r="8.5" /><path d="M4 12h16M12 3.5c2.1 2.3 3.1 5.1 3.1 8.5S14.1 18.2 12 20.5C9.9 18.2 8.9 15.4 8.9 12S9.9 5.8 12 3.5Z" />
            </svg>
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-sm sm:text-base font-semibold tracking-tight text-slate-100">EarthVision AI</h1>
            <p className="hidden sm:block text-[11px] tracking-wide text-slate-500">SATELLITE EARTH INTELLIGENCE</p>
          </div>
          <span className="hidden md:inline-flex items-center gap-1.5 rounded-full border border-amber-500/20 bg-amber-500/5 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> Demo mode
          </span>
        </div>
        <AuthWidget />
      </header>
      <main className="flex flex-1 min-h-0 flex-col xl:flex-row xl:overflow-hidden">
        <aside className="w-full shrink-0 border-b border-slate-800 xl:w-[300px] xl:border-b-0 xl:border-r xl:overflow-y-auto">
          <AnalysisPanel />
        </aside>
        <section aria-label="Interactive map" className="relative h-[54vh] min-h-[360px] shrink-0 xl:h-auto xl:min-h-0 xl:min-w-0 xl:flex-1">
          <MapSelector />
          <LayerControls />
        </section>
        <aside aria-label="Analysis results" className="flex w-full min-h-[360px] flex-col border-t border-slate-800 xl:min-h-0 xl:w-[380px] xl:shrink-0 xl:border-l xl:border-t-0">
          <nav aria-label="Result views" className="flex shrink-0 border-b border-slate-800 bg-slate-950/40 px-2">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                aria-current={tab === t.id ? "page" : undefined}
                className={`relative flex-1 px-2 py-3 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-cyan-400 ${
                  tab === t.id ? "text-cyan-300 after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:rounded-full after:bg-cyan-400" : "text-slate-500 hover:text-slate-200"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div className="flex-1 overflow-y-auto">
            {tab === "results" && <ResultsDashboard />}
            {tab === "timeseries" && <TimeSeriesPanel />}
            {tab === "report" && <ReportPanel />}
          </div>
        </aside>
      </main>
    </div>
  );
}
