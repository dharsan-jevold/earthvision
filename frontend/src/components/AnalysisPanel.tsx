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
  const datesValid = startDate <= endDate;

  const handleSearch = async () => {
    if (!bbox || !datesValid) return;
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
    if (!bbox || !beforeSceneId || !afterSceneId || beforeSceneId === afterSceneId) return;
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

  const fieldClass = "mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-2.5 text-xs text-slate-200 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/15";
  const stepClass = "grid h-5 w-5 shrink-0 place-items-center rounded-full bg-cyan-400/15 text-[10px] font-bold text-cyan-300";

  return (
    <div className="flex flex-col gap-4 p-4 text-sm sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-300">Analysis setup</p>
          <h2 className="mt-1 text-base font-semibold text-slate-100">New comparison</h2>
        </div>
        <span className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-[10px] text-slate-400">STEP 1 / 3</span>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/55 p-3.5" aria-labelledby="region-title">
        <div className="mb-2 flex items-center gap-2">
          <span className={`${stepClass} ${bbox ? "bg-emerald-400/15 text-emerald-300" : ""}`}>{bbox ? "✓" : "1"}</span>
          <h3 id="region-title" className="text-xs font-semibold text-slate-200">Area of interest</h3>
        </div>
        {bbox ? (
          <div className="rounded-lg bg-slate-950/70 px-3 py-2.5">
            <p className="text-xs font-medium text-slate-200">Selection ready</p>
            <p className="mt-1 font-mono text-[10px] leading-relaxed text-slate-500">{bbox.min_lat.toFixed(3)}, {bbox.min_lon.toFixed(3)}<br />{bbox.max_lat.toFixed(3)}, {bbox.max_lon.toFixed(3)}</p>
            <p className="mt-2 text-[10px] text-cyan-300">Use Shift + drag on the map to redraw.</p>
          </div>
        ) : (
          <p className="rounded-lg border border-dashed border-slate-700 px-3 py-3 text-xs leading-relaxed text-slate-500">Hold Shift and drag on the map to select a region.</p>
        )}
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/55 p-3.5" aria-labelledby="dates-title">
        <div className="mb-3 flex items-center gap-2"><span className={stepClass}>2</span><h3 id="dates-title" className="text-xs font-semibold text-slate-200">Observation window</h3></div>
        <div className="grid grid-cols-2 gap-2">
          <label className="text-[10px] text-slate-500">From<input aria-label="Start date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className={fieldClass} /></label>
          <label className="text-[10px] text-slate-500">To<input aria-label="End date" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className={fieldClass} /></label>
        </div>
        {!datesValid && <p role="alert" className="mt-2 text-[11px] text-rose-300">End date must be on or after the start date.</p>}
        <button disabled={!bbox || !datesValid || status === "searching"} onClick={handleSearch} className="mt-3 flex w-full items-center justify-center rounded-lg bg-cyan-400 px-3 py-2.5 text-xs font-semibold text-slate-950 shadow-lg shadow-cyan-950/20 transition hover:bg-cyan-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500 disabled:shadow-none">
          {status === "searching" ? "Searching scenes…" : "Find available imagery"}
        </button>
      </section>

      {scenes.length > 0 && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/55 p-3.5" aria-labelledby="scenes-title">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2"><span className={stepClass}>3</span><h3 id="scenes-title" className="text-xs font-semibold text-slate-200">Compare scenes</h3></div>
            <span className="rounded-full bg-amber-400/10 px-2 py-1 text-[9px] font-semibold uppercase tracking-wider text-amber-300">{scenes.length} demo scenes</span>
          </div>
          <div className="flex flex-col gap-2.5">
            <label className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Earlier observation
              <select aria-label="Earlier observation" value={beforeSceneId ?? ""} onChange={(e) => setBeforeScene(e.target.value)} className={fieldClass}>
                {scenes.map((s) => <option key={s.scene_id} value={s.scene_id}>{s.acquisition_date} · cloud {s.cloud_cover_pct}%</option>)}
              </select>
            </label>
            <label className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Later observation
              <select aria-label="Later observation" value={afterSceneId ?? ""} onChange={(e) => setAfterScene(e.target.value)} className={fieldClass}>
                {scenes.map((s) => <option key={s.scene_id} value={s.scene_id}>{s.acquisition_date} · cloud {s.cloud_cover_pct}%</option>)}
              </select>
            </label>
          </div>
          {beforeSceneId === afterSceneId && <p role="alert" className="mt-2 text-[11px] text-rose-300">Choose two different observation dates.</p>}
          <button disabled={!beforeSceneId || !afterSceneId || beforeSceneId === afterSceneId || status === "analyzing"} onClick={handleAnalyze} className="mt-4 flex w-full items-center justify-center rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-3 py-2.5 text-xs font-semibold text-emerald-200 transition hover:bg-emerald-400/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 disabled:cursor-not-allowed disabled:border-slate-700 disabled:bg-slate-800 disabled:text-slate-500">
            {status === "analyzing" ? "Analyzing observations…" : "Run change detection"}
          </button>
        </section>
      )}

      {status === "error" && <p role="alert" className="rounded-lg border border-rose-900/70 bg-rose-950/40 p-3 text-xs leading-relaxed text-rose-300">{useAppStore.getState().errorMessage}</p>}
    </div>
  );
}
