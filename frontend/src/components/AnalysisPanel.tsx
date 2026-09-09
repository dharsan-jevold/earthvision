import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { runAnalysis, searchScenes } from "../lib/api";

export default function AnalysisPanel() {
  const { bbox, scenes, beforeSceneId, afterSceneId, status } = useAppStore();
  const setScenes = useAppStore((s) => s.setScenes);
  const setBeforeScene = useAppStore((s) => s.setBeforeScene);
  const setAfterScene = useAppStore((s) => s.setAfterScene);
  const setAnalysis = useAppStore((s) => s.setAnalysis);
  const setStatus = useAppStore((s) => s.setStatus);
  const setError = useAppStore((s) => s.setError);

  const [startDate, setStartDate] = useState("2026-01-01");
  const [endDate, setEndDate] = useState("2026-08-01");

  const handleSearch = async () => {
    if (!bbox) return;
    setStatus("searching");
    setError(null);
    try {
      const results = await searchScenes(bbox, startDate, endDate, "demo");
      setScenes(results);
      if (results.length >= 2) {
        setBeforeScene(results[0].scene_id);
        setAfterScene(results[results.length - 1].scene_id);
      }
      setStatus("idle");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    }
  };

  const handleAnalyze = async () => {
    if (!bbox || !beforeSceneId || !afterSceneId) return;
    setStatus("analyzing");
    setError(null);
    try {
      const result = await runAnalysis(bbox, beforeSceneId, afterSceneId, "demo", 128);
      setAnalysis(result);
      setStatus("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 text-sm">
      <div>
        <p className="text-cyan-400 font-semibold mb-2 uppercase tracking-wide text-xs">1. Region</p>
        {bbox ? (
          <p className="text-slate-300">
            Selected — {((bbox.max_lon - bbox.min_lon) * 111).toFixed(0)}km × {((bbox.max_lat - bbox.min_lat) * 111).toFixed(0)}km approx.
          </p>
        ) : (
          <p className="text-slate-500">Draw a region on the map to begin.</p>
        )}
      </div>

      <div>
        <p className="text-cyan-400 font-semibold mb-2 uppercase tracking-wide text-xs">2. Time period</p>
        <div className="flex gap-2 items-center">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 flex-1"
          />
          <span className="text-slate-500">→</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 flex-1"
          />
        </div>
        <button
          disabled={!bbox || status === "searching"}
          onClick={handleSearch}
          className="mt-2 w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded py-1.5 font-medium transition"
        >
          {status === "searching" ? "Searching…" : "Find available imagery"}
        </button>
      </div>

      {scenes.length > 0 && (
        <div>
          <p className="text-cyan-400 font-semibold mb-2 uppercase tracking-wide text-xs">
            3. Scenes ({scenes.length} found — <span className="text-amber-400">DEMO DATA</span>)
          </p>
          <div className="flex flex-col gap-1.5">
            <label className="text-slate-400 text-xs">Before</label>
            <select
              value={beforeSceneId ?? ""}
              onChange={(e) => setBeforeScene(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200"
            >
              {scenes.map((s) => (
                <option key={s.scene_id} value={s.scene_id}>
                  {s.acquisition_date} · cloud {s.cloud_cover_pct}%
                </option>
              ))}
            </select>
            <label className="text-slate-400 text-xs mt-1">After</label>
            <select
              value={afterSceneId ?? ""}
              onChange={(e) => setAfterScene(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200"
            >
              {scenes.map((s) => (
                <option key={s.scene_id} value={s.scene_id}>
                  {s.acquisition_date} · cloud {s.cloud_cover_pct}%
                </option>
              ))}
            </select>
          </div>
          <button
            disabled={!beforeSceneId || !afterSceneId || status === "analyzing"}
            onClick={handleAnalyze}
            className="mt-3 w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded py-1.5 font-medium transition"
          >
            {status === "analyzing" ? "Analyzing…" : "Run change detection"}
          </button>
        </div>
      )}

      {status === "error" && (
        <p className="text-red-400 text-xs bg-red-950/40 border border-red-900 rounded p-2">
          {useAppStore.getState().errorMessage}
        </p>
      )}
    </div>
  );
}
