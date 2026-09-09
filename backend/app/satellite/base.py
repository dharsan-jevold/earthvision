"""
Satellite provider abstraction.

Every provider (demo, Sentinel-2, Landsat, GEE, ...) implements this same
interface. The rest of the application (preprocessing, indices, change
detection) never talks to a provider directly by name — only through this
contract. This is what lets a real provider be swapped in later without
touching analysis code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional

import numpy as np


@dataclass
class BoundingBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def area_km2(self) -> float:
        # Rough equirectangular approximation — good enough for UI display,
        # NOT used for any scientific area calculation (those use the
        # actual pixel/CRS-aware math in geospatial/area.py).
        lat_mid = (self.min_lat + self.max_lat) / 2
        km_per_deg_lat = 111.32
        km_per_deg_lon = 111.32 * np.cos(np.radians(lat_mid))
        width_km = abs(self.max_lon - self.min_lon) * km_per_deg_lon
        height_km = abs(self.max_lat - self.min_lat) * km_per_deg_lat
        return round(width_km * height_km, 3)


@dataclass
class SceneMetadata:
    scene_id: str
    provider: str
    platform: str
    acquisition_date: date
    cloud_cover_pct: float
    resolution_m: float
    bbox: BoundingBox
    is_demo: bool
    bands: list[str]


@dataclass
class SceneRaster:
    """
    In-memory raster stack for a scene. band_arrays maps band name -> 2D
    numpy array, all co-registered (same shape/grid). Values are surface
    reflectance scaled to [0, 1] float32, matching Sentinel-2 L2A convention.
    """
    metadata: SceneMetadata
    band_arrays: dict[str, np.ndarray]
    transform: tuple  # (pixel_width_deg, pixel_height_deg, origin_lon, origin_lat)


class SatelliteProvider(ABC):
    name: str = "base"
    is_demo: bool = False

    @abstractmethod
    def search(
        self,
        bbox: BoundingBox,
        start_date: date,
        end_date: date,
        max_cloud_cover_pct: float = 40.0,
    ) -> list[SceneMetadata]:
        """Return available scenes matching the query, without downloading pixels."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, scene_id: str, bbox: BoundingBox, resolution_px: int = 256) -> SceneRaster:
        """Download/generate the actual band data for a scene, cropped to bbox."""
        raise NotImplementedError
