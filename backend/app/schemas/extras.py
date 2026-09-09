from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.schemas.analysis import AnalyzeResponse, BBoxIn


class LayersRequest(BaseModel):
    bbox: BBoxIn
    before_scene_id: str
    after_scene_id: str
    provider: str = "demo"
    resolution_px: int = 96


class TimeSeriesRequest(BaseModel):
    bbox: BBoxIn
    scene_ids: list[str]
    dates: list[date]
    provider: str = "demo"
    resolution_px: int = 64


class ReportRequest(BaseModel):
    analysis: AnalyzeResponse
    region_name: str = "the selected region"


class ExportGeoJSONRequest(BaseModel):
    analysis: AnalyzeResponse
    bbox: BBoxIn
    resolution_px: int = 128


class ExportCSVRequest(BaseModel):
    analysis: AnalyzeResponse
