from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.analysis import AnalyzeResponse, BBoxIn


class ProjectCreate(BaseModel):
    name: str
    bbox: BBoxIn


class ProjectOut(BaseModel):
    id: int
    name: str
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SaveAnalysisRequest(BaseModel):
    project_id: int
    before_scene_id: str
    after_scene_id: str
    provider: str
    result: AnalyzeResponse


class AnalysisRecordOut(BaseModel):
    id: int
    project_id: int
    before_scene_id: str
    after_scene_id: str
    provider: str
    overall_severity: str
    total_changed_fraction: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisRecordDetailOut(AnalysisRecordOut):
    result_json: AnalyzeResponse
