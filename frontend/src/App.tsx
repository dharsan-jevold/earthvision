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
    <div className="h-screen w-screen flex flex-col bg-slate-950">
      <header className="h-14 flex items-center px-5 border-b border-slate-800 bg-slate-900/60">
        <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 mr-2.5" />
        <h1 className="text-slate-100 font-semibold tracking-tight">
          EarthVision AI <span className="text-slate-500 font-normal text-sm ml-1">Satellite Earth Intelligence</span>
        </h1>
        <AuthWidget />
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="w-80 border-r border-slate-800 overflow-y-auto shrink-0">
          <AnalysisPanel />
        </div>
        <div className="flex-1 relative">
          <MapSelector />
          <LayerControls />
        </div>
        <div className="w-96 border-l border-slate-800 flex flex-col shrink-0">
          <div className="flex border-b border-slate-800 shrink-0">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex-1 text-xs font-medium py-2.5 ${
                  tab === t.id ? "text-cyan-400 border-b-2 border-cyan-400" : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="flex-1 overflow-y-auto">
            {tab === "results" && <ResultsDashboard />}
            {tab === "timeseries" && <TimeSeriesPanel />}
            {tab === "report" && <ReportPanel />}
          </div>
        </div>
      </div>
    </div>
  );
}
