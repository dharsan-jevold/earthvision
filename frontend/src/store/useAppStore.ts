import { create } from "zustand";
import type {
  AnalyzeResponse,
  BBox,
  LayersResponse,
  ProjectOut,
  ReportResponse,
  Scene,
  TimeSeriesResponse,
} from "../lib/api";

interface AppState {
  bbox: BBox | null;
  scenes: Scene[];
  beforeSceneId: string | null;
  afterSceneId: string | null;
  analysis: AnalyzeResponse | null;
  status: "idle" | "searching" | "analyzing" | "done" | "error";
  errorMessage: string | null;

  // Phase 12 — GIS layers
  layers: LayersResponse | null;
  activeLayer: keyof LayersResponse["layers"] | null;

  // Phase 13 — time series
  timeSeries: TimeSeriesResponse | null;

  // Phase 14 — report
  report: ReportResponse | null;

  // Phase 17 — auth
  authToken: string | null;
  userEmail: string | null;
  projects: ProjectOut[];
  activeProjectId: number | null;

  setBBox: (b: BBox | null) => void;
  setScenes: (s: Scene[]) => void;
  setBeforeScene: (id: string | null) => void;
  setAfterScene: (id: string | null) => void;
  setAnalysis: (a: AnalyzeResponse | null) => void;
  setStatus: (s: AppState["status"]) => void;
  setError: (msg: string | null) => void;
  setLayers: (l: LayersResponse | null) => void;
  setActiveLayer: (k: keyof LayersResponse["layers"] | null) => void;
  setTimeSeries: (t: TimeSeriesResponse | null) => void;
  setReport: (r: ReportResponse | null) => void;
  setAuth: (token: string | null, email: string | null) => void;
  setProjects: (p: ProjectOut[]) => void;
  setActiveProject: (id: number | null) => void;
  reset: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  bbox: null,
  scenes: [],
  beforeSceneId: null,
  afterSceneId: null,
  analysis: null,
  status: "idle",
  errorMessage: null,
  layers: null,
  activeLayer: null,
  timeSeries: null,
  report: null,
  authToken: typeof window !== "undefined" ? window.localStorage.getItem("ev_token") : null,
  userEmail: typeof window !== "undefined" ? window.localStorage.getItem("ev_email") : null,
  projects: [],
  activeProjectId: null,

  setBBox: (b) =>
    set({ bbox: b, scenes: [], beforeSceneId: null, afterSceneId: null, analysis: null, layers: null, report: null }),
  setScenes: (s) => set({ scenes: s }),
  setBeforeScene: (id) => set({ beforeSceneId: id }),
  setAfterScene: (id) => set({ afterSceneId: id }),
  setAnalysis: (a) => set({ analysis: a }),
  setStatus: (s) => set({ status: s }),
  setError: (msg) => set({ errorMessage: msg, status: msg ? "error" : "idle" }),
  setLayers: (l) => set({ layers: l, activeLayer: null }),
  setActiveLayer: (k) => set({ activeLayer: k }),
  setTimeSeries: (t) => set({ timeSeries: t }),
  setReport: (r) => set({ report: r }),
  setAuth: (token, email) => {
    if (typeof window !== "undefined") {
      if (token) {
        window.localStorage.setItem("ev_token", token);
        if (email) window.localStorage.setItem("ev_email", email);
      } else {
        window.localStorage.removeItem("ev_token");
        window.localStorage.removeItem("ev_email");
      }
    }
    set({ authToken: token, userEmail: email });
  },
  setProjects: (p) => set({ projects: p }),
  setActiveProject: (id) => set({ activeProjectId: id }),
  reset: () =>
    set({
      bbox: null,
      scenes: [],
      beforeSceneId: null,
      afterSceneId: null,
      analysis: null,
      status: "idle",
      errorMessage: null,
      layers: null,
      activeLayer: null,
      timeSeries: null,
      report: null,
    }),
}));
