from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class BBoxIn(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


class SearchRequest(BaseModel):
    bbox: BBoxIn
    start_date: date
    end_date: date
    max_cloud_cover_pct: float = 40.0
    provider: str = "demo"


class SceneOut(BaseModel):
    scene_id: str
    provider: str
    platform: str
    acquisition_date: date
    cloud_cover_pct: float
    resolution_m: float
    is_demo: bool


class AnalyzeRequest(BaseModel):
    bbox: BBoxIn
    before_scene_id: str
    after_scene_id: str
    provider: str = "demo"
    resolution_px: int = Field(default=128, ge=32, le=512)


class IndexStats(BaseModel):
    mean: float
    min: float
    max: float
    std: float


class RegionOut(BaseModel):
    id: int
    change_type: str
    area_km2: float
    confidence: float
    before_value: float
    after_value: float
    severity: str
    bbox_px: tuple[int, int, int, int]


class VegetationSummary(BaseModel):
    before_pct: float
    after_pct: float
    change_pct: float
    before_stats: IndexStats
    after_stats: IndexStats


class WaterSummary(BaseModel):
    before_area_km2: float
    after_area_km2: float
    change_pct: float


class UrbanSummary(BaseModel):
    before_area_km2: float
    after_area_km2: float
    change_pct: float


class AnalyzeResponse(BaseModel):
    is_demo: bool
    method: str
    region_area_km2: float
    vegetation: VegetationSummary
    water: WaterSummary
    urban: UrbanSummary
    overall_severity: str
    total_changed_fraction: float
    regions: list[RegionOut]
    disclaimer: str
