import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { exportCsv, exportGeoJson, saveAnalysis, createProject } from "../lib/api";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadJson(obj: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
  downloadBlob(blob, filename);
}

export default function ExportAndSave() {
  const { analysis, bbox, authToken } = useAppStore();
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  if (!analysis || !bbox) return null;

  const handleCsv = async () => {
    const blob = await exportCsv(analysis);
    downloadBlob(blob, "earthvision-analysis.csv");
  };

  const handleGeoJson = async () => {
    const geojson = await exportGeoJson(analysis, bbox, 128);
    downloadJson(geojson, "earthvision-changes.geojson");
  };

  const handleSave = async () => {
    if (!authToken) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      const project = await createProject(
        `Region ${new Date().toISOString().slice(0, 16)}`,
        bbox,
        authToken
      );
      await saveAnalysis(project.id, "before", "after", "demo", analysis, authToken);
      setSaveMsg("Saved to your account.");
    } catch (e) {
      setSaveMsg(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 border-t border-slate-800 pt-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">Export</p>
      <div className="flex gap-2">
        <button onClick={handleCsv} className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded py-1.5">
          Download CSV
        </button>
        <button onClick={handleGeoJson} className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded py-1.5">
          Download GeoJSON
        </button>
      </div>
      {authToken ? (
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-slate-800 hover:bg-slate-700 disabled:text-slate-600 text-slate-200 text-xs rounded py-1.5"
        >
          {saving ? "Saving…" : "Save analysis to my account"}
        </button>
      ) : (
        <p className="text-slate-600 text-xs">Log in to save this analysis to your account.</p>
      )}
      {saveMsg && <p className="text-emerald-400 text-xs">{saveMsg}</p>}
    </div>
  );
}
