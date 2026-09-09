"""
Baseline change-detection pipeline: index differencing + thresholding +
connected-component labeling to produce discrete change regions.

This is the scientifically-grounded baseline described in the spec (section
10). It is what actually runs today. A learned Siamese/U-Net model
(app/ml/change_model.py) is stubbed as a second, swappable stage — see that
file for exactly what's needed to make it real.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.geospatial import indices as idx
from app.geospatial.area import mask_area_km2
from app.satellite.base import BoundingBox

# Configurable severity thresholds (spec section 12) — NOT a universal
# scientific standard, just a documented project default.
SEVERITY_THRESHOLDS = {
    "LOW": (0.0, 0.10),
    "MODERATE": (0.10, 0.25),
    "HIGH": (0.25, 0.50),
    "CRITICAL": (0.50, 1.01),
}

CHANGE_MAGNITUDE_THRESHOLD = 0.15  # |delta index| above this counts as a "change" pixel


def severity_for(fraction_changed: float) -> str:
    for label, (lo, hi) in SEVERITY_THRESHOLDS.items():
        if lo <= fraction_changed < hi:
            return label
    return "CRITICAL"


@dataclass
class ChangeRegion:
    id: int
    change_type: str
    area_km2: float
    confidence: float
    before_value: float
    after_value: float
    centroid_px: tuple[int, int]
    bbox_px: tuple[int, int, int, int]  # row_min, col_min, row_max, col_max
    severity: str


def _label_connected_components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """Simple flood-fill connected component labeling (4-connectivity), no scipy dependency."""
    labels = np.zeros_like(mask, dtype=np.int32)
    current_label = 0
    h, w = mask.shape
    for i in range(h):
        for j in range(w):
            if mask[i, j] and labels[i, j] == 0:
                current_label += 1
                stack = [(i, j)]
                labels[i, j] = current_label
                while stack:
                    y, x = stack.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and labels[ny, nx] == 0:
                            labels[ny, nx] = current_label
                            stack.append((ny, nx))
    return labels, current_label


def classify_change(ndvi_delta: float, ndwi_delta: float, ndbi_delta: float) -> str:
    """Classify a region's dominant change type from its index deltas."""
    deltas = {
        "Vegetation loss": -ndvi_delta if ndvi_delta < -0.05 else -1,
        "Vegetation growth": ndvi_delta if ndvi_delta > 0.05 else -1,
        "Water decrease": -ndwi_delta if ndwi_delta < -0.05 else -1,
        "Water increase": ndwi_delta if ndwi_delta > 0.05 else -1,
        "Urban expansion": ndbi_delta if ndbi_delta > 0.05 else -1,
    }
    best = max(deltas, key=deltas.get)
    if deltas[best] <= 0:
        return "Other/unknown"
    return best


def detect_changes(
    before_bands: dict[str, np.ndarray],
    after_bands: dict[str, np.ndarray],
    bbox: BoundingBox,
    min_region_px: int = 15,
) -> dict:
    ndvi_before = idx.ndvi(before_bands["nir"], before_bands["red"])
    ndvi_after = idx.ndvi(after_bands["nir"], after_bands["red"])
    ndwi_before = idx.ndwi(before_bands["green"], before_bands["nir"])
    ndwi_after = idx.ndwi(after_bands["green"], after_bands["nir"])
    ndbi_before = idx.ndbi(before_bands["swir1"], before_bands["nir"])
    ndbi_after = idx.ndbi(after_bands["swir1"], after_bands["nir"])

    ndvi_delta = ndvi_after - ndvi_before
    ndwi_delta = ndwi_after - ndwi_before
    ndbi_delta = ndbi_after - ndbi_before

    combined_magnitude = np.maximum.reduce(
        [np.abs(ndvi_delta), np.abs(ndwi_delta), np.abs(ndbi_delta)]
    )
    change_mask = combined_magnitude > CHANGE_MAGNITUDE_THRESHOLD

    labels, n_regions = _label_connected_components(change_mask)

    regions: list[ChangeRegion] = []
    region_id = 0
    for label_val in range(1, n_regions + 1):
        region_mask = labels == label_val
        size = int(np.sum(region_mask))
        if size < min_region_px:
            continue
        region_id += 1
        ys, xs = np.where(region_mask)
        centroid = (int(np.mean(ys)), int(np.mean(xs)))
        bbox_px = (int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max()))

        rv_ndvi_delta = float(np.mean(ndvi_delta[region_mask]))
        rv_ndwi_delta = float(np.mean(ndwi_delta[region_mask]))
        rv_ndbi_delta = float(np.mean(ndbi_delta[region_mask]))
        change_type = classify_change(rv_ndvi_delta, rv_ndwi_delta, rv_ndbi_delta)

        area = mask_area_km2(region_mask, bbox)
        magnitude = float(np.mean(combined_magnitude[region_mask]))
        # Confidence = how far the mean magnitude sits above the detection
        # threshold, saturating at 0.98. This is an explainable heuristic,
        # not a calibrated probability — labeled as such in the API response.
        confidence = min(0.98, 0.5 + (magnitude - CHANGE_MAGNITUDE_THRESHOLD) * 2)

        if "Vegetation" in change_type:
            before_val, after_val = float(np.mean(ndvi_before[region_mask])), float(np.mean(ndvi_after[region_mask]))
        elif "Water" in change_type:
            before_val, after_val = float(np.mean(ndwi_before[region_mask])), float(np.mean(ndwi_after[region_mask]))
        elif "Urban" in change_type:
            before_val, after_val = float(np.mean(ndbi_before[region_mask])), float(np.mean(ndbi_after[region_mask]))
        else:
            before_val, after_val = 0.0, 0.0

        regions.append(
            ChangeRegion(
                id=region_id,
                change_type=change_type,
                area_km2=area,
                confidence=round(confidence, 3),
                before_value=round(before_val, 4),
                after_value=round(after_val, 4),
                centroid_px=centroid,
                bbox_px=bbox_px,
                severity=severity_for(min(1.0, magnitude)),
            )
        )

    total_changed_fraction = float(np.mean(change_mask))

    return {
        "ndvi_before": ndvi_before,
        "ndvi_after": ndvi_after,
        "ndwi_before": ndwi_before,
        "ndwi_after": ndwi_after,
        "ndbi_before": ndbi_before,
        "ndbi_after": ndbi_after,
        "change_mask": change_mask,
        "regions": regions,
        "overall_severity": severity_for(total_changed_fraction),
        "total_changed_fraction": round(total_changed_fraction, 4),
        "method": "spectral_index_differencing_baseline",
    }
