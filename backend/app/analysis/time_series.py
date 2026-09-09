"""
Phase 13 — time-series analysis across more than two dates.

Fetches a scene per requested date, computes NDVI/NDWI/NDBI summary stats
for each, and does simple trend detection (linear regression slope) so the
frontend can plot "vegetation health over time" and get a plain-language
trend statement.
"""
from __future__ import annotations

from datetime import date

import numpy as np

from app.geospatial import indices as idx
from app.satellite.base import BoundingBox
from app.satellite.registry import get_provider


def _linear_trend(values: list[float]) -> dict:
    """Fit y = a*x + b over equally-spaced x, return slope + direction label."""
    n = len(values)
    if n < 2:
        return {"slope": 0.0, "direction": "insufficient_data"}
    x = np.arange(n, dtype=np.float64)
    y = np.array(values, dtype=np.float64)
    slope, intercept = np.polyfit(x, y, 1)
    # Normalize slope relative to the value range so "direction" is meaningful
    # regardless of the index's scale.
    value_range = max(y.max() - y.min(), 1e-6)
    relative_slope = slope * n / value_range
    if relative_slope > 0.15:
        direction = "increasing"
    elif relative_slope < -0.15:
        direction = "decreasing"
    else:
        direction = "stable"
    return {"slope": float(slope), "direction": direction}


def run_time_series(
    bbox: BoundingBox,
    scene_ids: list[str],
    dates: list[date],
    provider_name: str,
    resolution_px: int = 96,
) -> dict:
    if len(scene_ids) != len(dates):
        raise ValueError("scene_ids and dates must be the same length")
    if len(scene_ids) < 2:
        raise ValueError("Time-series analysis requires at least 2 dates")

    provider = get_provider(provider_name)

    ndvi_means, ndwi_means, ndbi_means = [], [], []
    veg_pcts, water_km2s, urban_km2s = [], [], []

    for scene_id in scene_ids:
        raster = provider.fetch(scene_id, bbox, resolution_px)
        bands = raster.band_arrays
        ndvi = idx.ndvi(bands["nir"], bands["red"])
        ndwi = idx.ndwi(bands["green"], bands["nir"])
        ndbi = idx.ndbi(bands["swir1"], bands["nir"])

        ndvi_means.append(float(np.mean(ndvi)))
        ndwi_means.append(float(np.mean(ndwi)))
        ndbi_means.append(float(np.mean(ndbi)))

        veg_pcts.append(idx.coverage_fraction(ndvi, 0.3) * 100)
        px_area = bbox.area_km2() / (resolution_px * resolution_px)
        water_km2s.append(float(np.sum(ndwi > 0)) * px_area)
        urban_km2s.append(float(np.sum(ndbi > 0)) * px_area)

    return {
        "is_demo": provider.is_demo,
        "dates": [d.isoformat() for d in dates],
        "ndvi_mean_series": [round(v, 4) for v in ndvi_means],
        "ndwi_mean_series": [round(v, 4) for v in ndwi_means],
        "ndbi_mean_series": [round(v, 4) for v in ndbi_means],
        "vegetation_pct_series": [round(v, 2) for v in veg_pcts],
        "water_km2_series": [round(v, 4) for v in water_km2s],
        "urban_km2_series": [round(v, 4) for v in urban_km2s],
        "trends": {
            "vegetation": _linear_trend(veg_pcts),
            "water": _linear_trend(water_km2s),
            "urban": _linear_trend(urban_km2s),
        },
    }
