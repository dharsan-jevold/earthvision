from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.satellite.base import BoundingBox
from app.satellite.registry import get_provider
from app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    SceneOut,
    SearchRequest,
)
from app.services.analysis_service import run_analysis

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/satellite/search", response_model=list[SceneOut])
def search_scenes(req: SearchRequest):
    try:
        provider = get_provider(req.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    bbox = BoundingBox(**req.bbox.model_dump())
    scenes = provider.search(bbox, req.start_date, req.end_date, req.max_cloud_cover_pct)
    return [
        SceneOut(
            scene_id=s.scene_id,
            provider=s.provider,
            platform=s.platform,
            acquisition_date=s.acquisition_date,
            cloud_cover_pct=s.cloud_cover_pct,
            resolution_m=s.resolution_m,
            is_demo=s.is_demo,
        )
        for s in scenes
    ]


@router.post("/analysis/run", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    bbox = BoundingBox(**req.bbox.model_dump())
    if bbox.area_km2() <= 0:
        raise HTTPException(status_code=400, detail="Invalid bounding box.")
    try:
        result = run_analysis(
            bbox=bbox,
            before_scene_id=req.before_scene_id,
            after_scene_id=req.after_scene_id,
            provider_name=req.provider,
            resolution_px=req.resolution_px,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
