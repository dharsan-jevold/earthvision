"""Pixel-grid-aware area math (still equirectangular-approximate, documented as such)."""
from __future__ import annotations

import numpy as np

from app.satellite.base import BoundingBox


def pixel_area_km2(bbox: BoundingBox, resolution_px: int) -> float:
    total_km2 = bbox.area_km2()
    n_pixels = resolution_px * resolution_px
    return total_km2 / n_pixels if n_pixels else 0.0


def mask_area_km2(mask: np.ndarray, bbox: BoundingBox) -> float:
    px_area = pixel_area_km2(bbox, mask.shape[0])
    return round(float(np.sum(mask)) * px_area, 4)
