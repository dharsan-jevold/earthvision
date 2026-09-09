"""
DemoProvider — synthetic satellite data so the whole app runs with zero
API credentials. Every scene/metadata object it returns is flagged
is_demo=True and the frontend must display a "DEMO DATA" badge whenever
this provider is used.

The synthetic bands are NOT random noise. They're generated from smooth
Perlin-like fields with realistic reflectance ranges per band, and a
"change" is injected as a spatial patch that shifts vegetation/water/
built-up signatures between two dates — deterministically, seeded from
the bbox + date, so re-running the same query gives the same result
(useful for demoing and for tests).
"""
from __future__ import annotations

import hashlib
from datetime import date

import numpy as np

from app.satellite.base import (
    BoundingBox,
    SatelliteProvider,
    SceneMetadata,
    SceneRaster,
)

BANDS = ["red", "green", "blue", "nir", "swir1"]


def _seed_from(*parts: str) -> int:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return int(h[:8], 16)


def _smooth_field(size: int, seed: int, octaves: int = 4) -> np.ndarray:
    """Cheap smooth noise field via upsampled low-res random grid + blur, no external deps."""
    rng = np.random.default_rng(seed)
    field = np.zeros((size, size), dtype=np.float32)
    amp = 1.0
    for o in range(octaves):
        res = max(2, 2 ** (o + 1))
        low = rng.random((res, res)).astype(np.float32)
        # nearest-neighbour-free bilinear upsample using numpy
        x = np.linspace(0, res - 1, size)
        y = np.linspace(0, res - 1, size)
        xi = np.clip(x.astype(int), 0, res - 1)
        yi = np.clip(y.astype(int), 0, res - 1)
        upsampled = low[np.ix_(yi, xi)]
        field += amp * upsampled
        amp *= 0.5
    field -= field.min()
    field /= (field.max() + 1e-8)
    return field


class DemoProvider(SatelliteProvider):
    name = "demo"
    is_demo = True

    def search(
        self,
        bbox: BoundingBox,
        start_date: date,
        end_date: date,
        max_cloud_cover_pct: float = 40.0,
    ) -> list[SceneMetadata]:
        scenes = []
        span_days = max(1, (end_date - start_date).days)
        n_scenes = min(6, max(2, span_days // 20))
        for i in range(n_scenes):
            offset = int(span_days * i / max(1, n_scenes - 1))
            acq = date.fromordinal(start_date.toordinal() + offset)
            seed = _seed_from(str(bbox), str(acq))
            cloud = float((seed % 4000) / 100.0)  # 0-40%
            if cloud > max_cloud_cover_pct:
                cloud = max_cloud_cover_pct * 0.5
            scenes.append(
                SceneMetadata(
                    scene_id=f"DEMO_{acq.isoformat()}_{seed % 10000:04d}",
                    provider=self.name,
                    platform="Demo-Synthetic (Sentinel-2-like)",
                    acquisition_date=acq,
                    cloud_cover_pct=round(cloud, 1),
                    resolution_m=10.0,
                    bbox=bbox,
                    is_demo=True,
                    bands=BANDS,
                )
            )
        return scenes

    def fetch(self, scene_id: str, bbox: BoundingBox, resolution_px: int = 256) -> SceneRaster:
        seed = _seed_from(scene_id, str(bbox))
        size = resolution_px

        veg_field = _smooth_field(size, seed + 1)
        water_field = _smooth_field(size, seed + 2)
        urban_field = _smooth_field(size, seed + 3)

        # Inject a deterministic "change patch" whose strength depends on the
        # acquisition date embedded in scene_id, so before/after fetches of
        # the same bbox but different dates diverge in a specific region —
        # this is what the change-detection pipeline is meant to find.
        date_part = scene_id.split("_")[1] if "_" in scene_id else "2024-01-01"
        date_seed = _seed_from(date_part)
        drift = ((date_seed % 1000) / 1000.0) - 0.5  # -0.5..0.5

        yy, xx = np.mgrid[0:size, 0:size]
        cy, cx = size * 0.35, size * 0.6
        patch = np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * (size * 0.12) ** 2)))
        veg_field = np.clip(veg_field - drift * patch, 0, 1)
        urban_field = np.clip(urban_field + drift * patch, 0, 1)

        # Reflectance synthesis per band (rough physical plausibility):
        red = np.clip(0.08 + 0.15 * urban_field + 0.05 * (1 - veg_field), 0, 1)
        nir = np.clip(0.10 + 0.55 * veg_field - 0.05 * urban_field, 0, 1)
        green = np.clip(0.07 + 0.10 * urban_field + 0.08 * veg_field, 0, 1)
        blue = np.clip(0.05 + 0.30 * water_field + 0.04 * urban_field, 0, 1)
        swir1 = np.clip(0.10 + 0.35 * urban_field - 0.20 * water_field, 0, 1)

        # Water suppresses NIR strongly (real spectral behaviour)
        nir = np.where(water_field > 0.75, nir * 0.15, nir)
        red = np.where(water_field > 0.75, red * 0.4, red)

        bands = {"red": red.astype(np.float32), "green": green.astype(np.float32),
                 "blue": blue.astype(np.float32), "nir": nir.astype(np.float32),
                 "swir1": swir1.astype(np.float32)}

        try:
            acq = date.fromisoformat(date_part)
        except ValueError:
            acq = date.today()

        meta = SceneMetadata(
            scene_id=scene_id,
            provider=self.name,
            platform="Demo-Synthetic (Sentinel-2-like)",
            acquisition_date=acq,
            cloud_cover_pct=0.0,
            resolution_m=10.0,
            bbox=bbox,
            is_demo=True,
            bands=BANDS,
        )
        transform = (
            (bbox.max_lon - bbox.min_lon) / size,
            (bbox.max_lat - bbox.min_lat) / size,
            bbox.min_lon,
            bbox.max_lat,
        )
        return SceneRaster(metadata=meta, band_arrays=bands, transform=transform)
