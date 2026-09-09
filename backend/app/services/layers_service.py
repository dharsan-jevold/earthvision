from __future__ import annotations

import numpy as np

from app.analysis.change_detection import detect_changes
from app.geospatial import indices as idx
from app.geospatial.rendering import render_index_png, render_mask_png
from app.ml.unsupervised_change import mask_iou, ml_change_mask
from app.satellite.base import BoundingBox
from app.satellite.registry import get_provider


def get_layers(
    bbox: BoundingBox,
    before_scene_id: str,
    after_scene_id: str,
    provider_name: str,
    resolution_px: int,
) -> dict:
    provider = get_provider(provider_name)
    before = provider.fetch(before_scene_id, bbox, resolution_px)
    after = provider.fetch(after_scene_id, bbox, resolution_px)

    ndvi_after = idx.ndvi(after.band_arrays["nir"], after.band_arrays["red"])
    ndwi_after = idx.ndwi(after.band_arrays["green"], after.band_arrays["nir"])
    ndbi_after = idx.ndbi(after.band_arrays["swir1"], after.band_arrays["nir"])

    baseline = detect_changes(before.band_arrays, after.band_arrays, bbox)
    ml_result = ml_change_mask(before.band_arrays, after.band_arrays)

    iou = mask_iou(baseline["change_mask"], ml_result["change_mask"])

    # bounds for georeferencing on the frontend map (NW, NE, SE, SW corners,
    # matching MapLibre's addImage/addSource "coordinates" convention)
    bounds = [
        [bbox.min_lon, bbox.max_lat],  # top-left
        [bbox.max_lon, bbox.max_lat],  # top-right
        [bbox.max_lon, bbox.min_lat],  # bottom-right
        [bbox.min_lon, bbox.min_lat],  # bottom-left
    ]

    return {
        "bounds": bounds,
        "is_demo": provider.is_demo,
        "layers": {
            "ndvi": render_index_png(ndvi_after),
            "ndwi": render_index_png(ndwi_after),
            "ndbi": render_index_png(ndbi_after),
            "change_baseline": render_mask_png(baseline["change_mask"], color=(239, 68, 68)),
            "change_ml": render_mask_png(ml_result["change_mask"], color=(168, 85, 247)),
        },
        "comparison": {
            "baseline_method": baseline["method"],
            "ml_method": ml_result["method"],
            "baseline_changed_fraction": round(float(np.mean(baseline["change_mask"])), 4),
            "ml_changed_fraction": round(float(np.mean(ml_result["change_mask"])), 4),
            "agreement_iou": round(iou, 4),
        },
    }
