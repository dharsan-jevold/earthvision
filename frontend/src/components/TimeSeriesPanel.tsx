import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { useAppStore } from "../store/useAppStore";
import { runTimeSeries } from "../lib/api";

const TREND_LABEL: Record<string, string> = {
  increasing: "▲ increasing",
  decreasing: "▼ decreasing",
  stable: "→ stable",
  insufficient_data: "insufficient data",
};

export default function TimeSeriesPanel() {
  const { bbox, scenes, timeSeries } = useAppStore();
  const setTimeSeries = useAppStore((s) => s.setTimeSeries);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    if (!bbox || scenes.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const sceneIds = scenes.map((s) => s.scene_id);
      const dates = scenes.map((s) => s.acquisition_date);
      const result = await runTimeSeries(bbox, sceneIds, dates, "demo", 64);
      setTimeSeries(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Time-series analysis failed");
    } finally {
      setLoading(false);
    }
  };

  if (!bbox || scenes.length < 2) {
    return (
      <div className="p-6 text-sm text-slate-600 text-center">
        Search for imagery first (needs at least 2 dates) to run time-series analysis.
      </div>
    );
  }

  const chartData = timeSeries?.dates.map((d, i) => ({
    date: d,
    vegetation: timeSeries.vegetation_pct_series[i],
    water: timeSeries.water_km2_series[i],
    urban: timeSeries.urban_km2_series[i],
  }));

  return (
    <div className="p-4 flex flex-col gap-4">
      <button
        onClick={handleRun}
        disabled={loading}
        className="bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 text-white rounded py-1.5 text-sm font-medium"
      >
        {loading ? "Analyzing across dates…" : `Run time-series across ${scenes.length} dates`}
      </button>
      {error && <p className="text-red-400 text-xs">{error}</p>}

      {timeSeries && (
        <>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {(["vegetation", "water", "urban"] as const).map((key) => (
              <div key={key} className="bg-slate-900 border border-slate-800 rounded p-2">
                <p className="text-slate-500 capitalize">{key}</p>
                <p className="text-slate-200 font-medium">{TREND_LABEL[timeSeries.trends[key].direction]}</p>
              </div>
            ))}
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 h-56">
            <p className="text-xs text-slate-500 mb-2">Vegetation coverage (%) over time</p>
            <ResponsiveContainer width="100%" height="85%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 12 }} />
                <Line type="monotone" dataKey="vegetation" stroke="#22d3ee" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 h-56">
            <p className="text-xs text-slate-500 mb-2">Water & urban area (km²) over time</p>
            <ResponsiveContainer width="100%" height="85%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="water" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="urban" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          {timeSeries.is_demo && <p className="text-amber-400 text-xs">⚠ Demo data — synthetic time series.</p>}
        </>
      )}
    </div>
  );
}
