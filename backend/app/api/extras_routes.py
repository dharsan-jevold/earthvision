from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.analysis.time_series import run_time_series
from app.reports.export import analysis_to_csv, analysis_to_geojson
from app.reports.report_generator import generate_report
from app.satellite.base import BoundingBox
from app.schemas.extras import (
    ExportCSVRequest,
    ExportGeoJSONRequest,
    LayersRequest,
    ReportRequest,
    TimeSeriesRequest,
)
from app.services.layers_service import get_layers

router = APIRouter()


@router.post("/analysis/layers")
def analysis_layers(req: LayersRequest):
    bbox = BoundingBox(**req.bbox.model_dump())
    try:
        return get_layers(bbox, req.before_scene_id, req.after_scene_id, req.provider, req.resolution_px)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analysis/time-series")
def analysis_time_series(req: TimeSeriesRequest):
    bbox = BoundingBox(**req.bbox.model_dump())
    try:
        return run_time_series(bbox, req.scene_ids, req.dates, req.provider, req.resolution_px)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/report/generate")
def report_generate(req: ReportRequest):
    return generate_report(req.analysis.model_dump(), req.region_name)


@router.post("/export/csv", response_class=PlainTextResponse)
def export_csv(req: ExportCSVRequest):
    csv_text = analysis_to_csv(req.analysis.model_dump())
    return PlainTextResponse(content=csv_text, media_type="text/csv")


@router.post("/export/geojson")
def export_geojson(req: ExportGeoJSONRequest):
    return analysis_to_geojson(req.analysis.model_dump(), req.bbox.model_dump(), req.resolution_px)
