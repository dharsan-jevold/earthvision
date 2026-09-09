from __future__ import annotations

from app.analysis.change_detection import detect_changes
from app.geospatial import indices as idx
from app.geospatial.area import mask_area_km2
from app.satellite.base import BoundingBox
from app.satellite.registry import get_provider

VEG_THRESHOLD = 0.3   # NDVI above this ~ vegetated pixel (standard rule-of-thumb, not universal)
WATER_THRESHOLD = 0.0  # NDWI above this ~ water pixel (McFeeters convention)
URBAN_THRESHOLD = 0.0  # NDBI above this ~ built-up pixel


def run_analysis(
    bbox: BoundingBox,
    before_scene_id: str,
    after_scene_id: str,
    provider_name: str,
    resolution_px: int,
) -> dict:
    provider = get_provider(provider_name)

    before_raster = provider.fetch(before_scene_id, bbox, resolution_px)
    after_raster = provider.fetch(after_scene_id, bbox, resolution_px)

    result = detect_changes(before_raster.band_arrays, after_raster.band_arrays, bbox)

    ndvi_before, ndvi_after = result["ndvi_before"], result["ndvi_after"]
    ndwi_before, ndwi_after = result["ndwi_before"], result["ndwi_after"]
    ndbi_before, ndbi_after = result["ndbi_before"], result["ndbi_after"]

    veg_before_pct = idx.coverage_fraction(ndvi_before, VEG_THRESHOLD) * 100
    veg_after_pct = idx.coverage_fraction(ndvi_after, VEG_THRESHOLD) * 100

    water_before_mask = ndwi_before > WATER_THRESHOLD
    water_after_mask = ndwi_after > WATER_THRESHOLD
    water_before_km2 = mask_area_km2(water_before_mask, bbox)
    water_after_km2 = mask_area_km2(water_after_mask, bbox)

    urban_before_mask = ndbi_before > URBAN_THRESHOLD
    urban_after_mask = ndbi_after > URBAN_THRESHOLD
    urban_before_km2 = mask_area_km2(urban_before_mask, bbox)
    urban_after_km2 = mask_area_km2(urban_after_mask, bbox)

    def pct_change(before: float, after: float) -> float:
        if before == 0:
            return 0.0
        return round(((after - before) / before) * 100, 2)

    return {
        "is_demo": provider.is_demo,
        "method": result["method"],
        "region_area_km2": bbox.area_km2(),
        "vegetation": {
            "before_pct": round(veg_before_pct, 2),
            "after_pct": round(veg_after_pct, 2),
            "change_pct": pct_change(veg_before_pct, veg_after_pct),
            "before_stats": idx.index_stats(ndvi_before),
            "after_stats": idx.index_stats(ndvi_after),
        },
        "water": {
            "before_area_km2": water_before_km2,
            "after_area_km2": water_after_km2,
            "change_pct": pct_change(water_before_km2, water_after_km2),
        },
        "urban": {
            "before_area_km2": urban_before_km2,
            "after_area_km2": urban_after_km2,
            "change_pct": pct_change(urban_before_km2, urban_after_km2),
        },
        "overall_severity": result["overall_severity"],
        "total_changed_fraction": result["total_changed_fraction"],
        "regions": [
            {
                "id": r.id,
                "change_type": r.change_type,
                "area_km2": r.area_km2,
                "confidence": r.confidence,
                "before_value": r.before_value,
                "after_value": r.after_value,
                "severity": r.severity,
                "bbox_px": r.bbox_px,
            }
            for r in result["regions"]
        ],
        "disclaimer": (
            "Demo dataset: bands are synthetically generated, not real satellite "
            "imagery. Change detection uses the spectral-index differencing "
            "baseline; the deep-learning model described in the project spec is "
            "not yet trained/wired in. Possible-cause explanations, when shown, "
            "are model inferences or hypotheses, not confirmed facts."
            if provider.is_demo
            else "Change detection uses the spectral-index differencing baseline."
        ),
    }
