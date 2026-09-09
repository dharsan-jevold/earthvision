const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

export interface BBox {
  min_lon: number;
  min_lat: number;
  max_lon: number;
  max_lat: number;
}

export interface Scene {
  scene_id: string;
  provider: string;
  platform: string;
  acquisition_date: string;
  cloud_cover_pct: number;
  resolution_m: number;
  is_demo: boolean;
}

export interface IndexStats {
  mean: number;
  min: number;
  max: number;
  std: number;
}

export interface ChangeRegion {
  id: number;
  change_type: string;
  area_km2: number;
  confidence: number;
  before_value: number;
  after_value: number;
  severity: string;
  bbox_px: [number, number, number, number];
}

export interface AnalyzeResponse {
  is_demo: boolean;
  method: string;
  region_area_km2: number;
  vegetation: {
    before_pct: number;
    after_pct: number;
    change_pct: number;
    before_stats: IndexStats;
    after_stats: IndexStats;
  };
  water: { before_area_km2: number; after_area_km2: number; change_pct: number };
  urban: { before_area_km2: number; after_area_km2: number; change_pct: number };
  overall_severity: string;
  total_changed_fraction: number;
  regions: ChangeRegion[];
  disclaimer: string;
}

async function post<T>(path: string, body: unknown, token?: string): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json();
}

async function get<T>(path: string, token?: string): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json();
}

export function searchScenes(
  bbox: BBox,
  startDate: string,
  endDate: string,
  provider = "demo"
): Promise<Scene[]> {
  return post<Scene[]>("/satellite/search", {
    bbox,
    start_date: startDate,
    end_date: endDate,
    provider,
  });
}

export function runAnalysis(
  bbox: BBox,
  beforeSceneId: string,
  afterSceneId: string,
  provider = "demo",
  resolutionPx = 128
): Promise<AnalyzeResponse> {
  return post<AnalyzeResponse>("/analysis/run", {
    bbox,
    before_scene_id: beforeSceneId,
    after_scene_id: afterSceneId,
    provider,
    resolution_px: resolutionPx,
  });
}

// --- Phase 12: GIS layers ---
export interface LayersResponse {
  bounds: [number, number][];
  is_demo: boolean;
  layers: Record<"ndvi" | "ndwi" | "ndbi" | "change_baseline" | "change_ml", string>;
  comparison: {
    baseline_method: string;
    ml_method: string;
    baseline_changed_fraction: number;
    ml_changed_fraction: number;
    agreement_iou: number;
  };
}

export function getLayers(
  bbox: BBox,
  beforeSceneId: string,
  afterSceneId: string,
  provider = "demo",
  resolutionPx = 96
): Promise<LayersResponse> {
  return post<LayersResponse>("/analysis/layers", {
    bbox,
    before_scene_id: beforeSceneId,
    after_scene_id: afterSceneId,
    provider,
    resolution_px: resolutionPx,
  });
}

// --- Phase 13: time series ---
export interface TimeSeriesResponse {
  is_demo: boolean;
  dates: string[];
  ndvi_mean_series: number[];
  ndwi_mean_series: number[];
  ndbi_mean_series: number[];
  vegetation_pct_series: number[];
  water_km2_series: number[];
  urban_km2_series: number[];
  trends: Record<"vegetation" | "water" | "urban", { slope: number; direction: string }>;
}

export function runTimeSeries(
  bbox: BBox,
  sceneIds: string[],
  dates: string[],
  provider = "demo",
  resolutionPx = 64
): Promise<TimeSeriesResponse> {
  return post<TimeSeriesResponse>("/analysis/time-series", {
    bbox,
    scene_ids: sceneIds,
    dates,
    provider,
    resolution_px: resolutionPx,
  });
}

// --- Phase 14: report ---
export interface ReportResponse {
  region_name: string;
  executive_summary: string;
  key_findings: string[];
  significant_areas: { region_id: number; observation: string }[];
  possible_explanations: {
    region_id: number;
    observed_change: string;
    model_inference: string;
    hypotheses: string[];
    caveat: string;
  }[];
  recommendations: string[];
  generation_method: string;
  disclaimer: string;
}

export function generateReport(analysis: AnalyzeResponse, regionName: string): Promise<ReportResponse> {
  return post<ReportResponse>("/report/generate", { analysis, region_name: regionName });
}

// --- Phase 25: export ---
export async function exportCsv(analysis: AnalyzeResponse): Promise<Blob> {
  const res = await fetch(`${API_BASE}/export/csv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis }),
  });
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  return res.blob();
}

export function exportGeoJson(analysis: AnalyzeResponse, bbox: BBox, resolutionPx: number) {
  return post("/export/geojson", { analysis, bbox, resolution_px: resolutionPx });
}

// --- Phase 17: auth + projects ---
export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export function register(email: string, password: string): Promise<{ id: number; email: string }> {
  return post("/auth/register", { email, password });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return post("/auth/login", { email, password });
}

export interface ProjectOut {
  id: number;
  name: string;
  min_lon: number;
  min_lat: number;
  max_lon: number;
  max_lat: number;
  created_at: string;
}

export function createProject(name: string, bbox: BBox, token: string): Promise<ProjectOut> {
  return post("/projects", { name, bbox }, token);
}

export function listProjects(token: string): Promise<ProjectOut[]> {
  return get("/projects", token);
}

export interface AnalysisRecordOut {
  id: number;
  project_id: number;
  before_scene_id: string;
  after_scene_id: string;
  provider: string;
  overall_severity: string;
  total_changed_fraction: number;
  created_at: string;
}

export function saveAnalysis(
  projectId: number,
  beforeSceneId: string,
  afterSceneId: string,
  provider: string,
  result: AnalyzeResponse,
  token: string
): Promise<AnalysisRecordOut> {
  return post(
    "/projects/analyses",
    { project_id: projectId, before_scene_id: beforeSceneId, after_scene_id: afterSceneId, provider, result },
    token
  );
}

export function listAnalyses(projectId: number, token: string): Promise<AnalysisRecordOut[]> {
  return get(`/projects/${projectId}/analyses`, token);
}

export function getAnalysis(analysisId: number, token: string): Promise<AnalysisRecordOut & { result_json: AnalyzeResponse }> {
  return get(`/projects/analyses/${analysisId}`, token);
}
