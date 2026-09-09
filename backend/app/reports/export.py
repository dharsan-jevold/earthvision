from __future__ import annotations

import csv
import io
import json


def analysis_to_csv(analysis: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["metric", "before", "after", "change_pct"])
    writer.writerow(["vegetation_pct", analysis["vegetation"]["before_pct"], analysis["vegetation"]["after_pct"], analysis["vegetation"]["change_pct"]])
    writer.writerow(["water_km2", analysis["water"]["before_area_km2"], analysis["water"]["after_area_km2"], analysis["water"]["change_pct"]])
    writer.writerow(["urban_km2", analysis["urban"]["before_area_km2"], analysis["urban"]["after_area_km2"], analysis["urban"]["change_pct"]])
    writer.writerow([])
    writer.writerow(["region_id", "change_type", "area_km2", "confidence", "severity", "before_value", "after_value"])
    for r in analysis["regions"]:
        writer.writerow([r["id"], r["change_type"], r["area_km2"], r["confidence"], r["severity"], r["before_value"], r["after_value"]])
    return buf.getvalue()


def analysis_to_geojson(analysis: dict, bbox: dict, resolution_px: int) -> dict:
    """
    Regions only have pixel-space bbox_px in the analysis result; convert to
    lon/lat using the same bbox+resolution the analysis was run with, and
    emit one Polygon Feature per detected change region.
    """
    min_lon, min_lat = bbox["min_lon"], bbox["min_lat"]
    max_lon, max_lat = bbox["max_lon"], bbox["max_lat"]
    lon_per_px = (max_lon - min_lon) / resolution_px
    lat_per_px = (max_lat - min_lat) / resolution_px

    def px_to_lonlat(row: int, col: int) -> list[float]:
        lon = min_lon + col * lon_per_px
        lat = max_lat - row * lat_per_px  # row 0 = north edge
        return [round(lon, 6), round(lat, 6)]

    features = []
    for r in analysis["regions"]:
        row_min, col_min, row_max, col_max = r["bbox_px"]
        ring = [
            px_to_lonlat(row_min, col_min),
            px_to_lonlat(row_min, col_max),
            px_to_lonlat(row_max, col_max),
            px_to_lonlat(row_max, col_min),
            px_to_lonlat(row_min, col_min),
        ]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "region_id": r["id"],
                    "change_type": r["change_type"],
                    "area_km2": r["area_km2"],
                    "confidence": r["confidence"],
                    "severity": r["severity"],
                    "before_value": r["before_value"],
                    "after_value": r["after_value"],
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )

    return {"type": "FeatureCollection", "features": features}
