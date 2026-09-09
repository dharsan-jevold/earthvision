import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { getLayers, type LayersResponse } from "../lib/api";

const LAYER_LABELS: Record<keyof LayersResponse["layers"], string> = {
  ndvi: "NDVI (vegetation)",
  ndwi: "NDWI (water)",
  ndbi: "NDBI (built-up)",
  change_baseline: "Change — baseline",
  change_ml: "Change — ML (K-means)",
};

export default function LayerControls() {
  const { bbox, beforeSceneId, afterSceneId, layers, activeLayer } = useAppStore();
  const setLayers = useAppStore((s) => s.setLayers);
  const setActiveLayer = useAppStore((s) => s.setActiveLayer);
  const [loading, setLoading] = useState(false);

  const canLoad = bbox && beforeSceneId && afterSceneId;

  const handleLoad = async () => {
    if (!bbox || !beforeSceneId || !afterSceneId) return;
    setLoading(true);
    try {
      const result = await getLayers(bbox, beforeSceneId, afterSceneId, "demo", 96);
      setLayers(result);
      setActiveLayer("ndvi");
    } catch {
      // silently ignore — this is a supplementary visualization, the main analysis flow still works
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute bottom-3 left-3 bg-slate-900/95 backdrop-blur border border-slate-700 rounded-lg p-3 text-xs text-slate-200 shadow-lg w-56">
      <p className="font-medium text-cyan-400 mb-2 uppercase tracking-wide">GIS layers</p>
      {!layers ? (
        <button
          disabled={!canLoad || loading}
          onClick={handleLoad}
          className="w-full bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-600 rounded py-1.5"
        >
          {loading ? "Loading…" : "Load map overlays"}
        </button>
      ) : (
        <div className="flex flex-col gap-1">
          <button
            onClick={() => setActiveLayer(null)}
            className={`text-left px-2 py-1 rounded ${activeLayer === null ? "bg-cyan-600 text-white" : "hover:bg-slate-800 text-slate-400"}`}
          >
            None
          </button>
          {(Object.keys(LAYER_LABELS) as (keyof LayersResponse["layers"])[]).map((key) => (
            <button
              key={key}
              onClick={() => setActiveLayer(key)}
              className={`text-left px-2 py-1 rounded ${activeLayer === key ? "bg-cyan-600 text-white" : "hover:bg-slate-800 text-slate-400"}`}
            >
              {LAYER_LABELS[key]}
            </button>
          ))}
          <p className="text-slate-500 mt-1 pt-1 border-t border-slate-800">
            Baseline vs. ML agreement (IoU): {(layers.comparison.agreement_iou * 100).toFixed(0)}%
          </p>
        </div>
      )}
    </div>
  );
}
