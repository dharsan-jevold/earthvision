from datetime import date

import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.ml.unsupervised_change import mask_iou, ml_change_mask
from app.reports.export import analysis_to_csv, analysis_to_geojson
from app.reports.report_generator import generate_report

client = TestClient(app)

BBOX = {"min_lon": 80.2, "min_lat": 13.0, "max_lon": 80.3, "max_lat": 13.1}


def _demo_bands(size=32, offset=0.0):
    return {
        "red": np.full((size, size), 0.1, dtype=np.float32),
        "green": np.full((size, size), 0.1, dtype=np.float32),
        "blue": np.full((size, size), 0.05, dtype=np.float32),
        "nir": np.full((size, size), 0.4 + offset, dtype=np.float32),
        "swir1": np.full((size, size), 0.1, dtype=np.float32),
    }


def test_ml_change_mask_runs_and_returns_expected_shape():
    before = _demo_bands()
    after = _demo_bands()
    after["nir"][5:15, 5:15] = 0.05  # inject a change patch
    result = ml_change_mask(before, after)
    assert result["change_mask"].shape == (32, 32)
    assert result["method"] == "kmeans_spectral_difference_clustering"
    assert 0 <= result["change_cluster_index"] < result["n_clusters"]


def test_mask_iou_identical_masks_is_one():
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:5, 2:5] = True
    assert mask_iou(mask, mask) == 1.0


def test_mask_iou_disjoint_masks_is_zero():
    a = np.zeros((10, 10), dtype=bool)
    b = np.zeros((10, 10), dtype=bool)
    a[0:2, 0:2] = True
    b[8:10, 8:10] = True
    assert mask_iou(a, b) == 0.0


def test_layers_endpoint():
    scenes = client.post(
        "/api/satellite/search",
        json={"bbox": BBOX, "start_date": "2026-01-01", "end_date": "2026-06-01", "provider": "demo"},
    ).json()
    r = client.post(
        "/api/analysis/layers",
        json={
            "bbox": BBOX,
            "before_scene_id": scenes[0]["scene_id"],
            "after_scene_id": scenes[-1]["scene_id"],
            "provider": "demo",
            "resolution_px": 48,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert set(body["layers"].keys()) == {"ndvi", "ndwi", "ndbi", "change_baseline", "change_ml"}
    for png_data_url in body["layers"].values():
        assert png_data_url.startswith("data:image/png;base64,")
    assert len(body["bounds"]) == 4
    assert 0 <= body["comparison"]["agreement_iou"] <= 1


def test_time_series_endpoint():
    scenes = client.post(
        "/api/satellite/search",
        json={"bbox": BBOX, "start_date": "2026-01-01", "end_date": "2026-08-01", "provider": "demo"},
    ).json()
    scene_ids = [s["scene_id"] for s in scenes]
    dates = [s["acquisition_date"] for s in scenes]
    r = client.post(
        "/api/analysis/time-series",
        json={"bbox": BBOX, "scene_ids": scene_ids, "dates": dates, "provider": "demo", "resolution_px": 32},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["ndvi_mean_series"]) == len(scene_ids)
    assert set(body["trends"].keys()) == {"vegetation", "water", "urban"}
    for t in body["trends"].values():
        assert t["direction"] in {"increasing", "decreasing", "stable", "insufficient_data"}


def test_time_series_requires_at_least_two_dates():
    r = client.post(
        "/api/analysis/time-series",
        json={
            "bbox": BBOX,
            "scene_ids": ["DEMO_2026-01-01_0001"],
            "dates": ["2026-01-01"],
            "provider": "demo",
            "resolution_px": 32,
        },
    )
    assert r.status_code == 400


def _sample_analysis():
    scenes = client.post(
        "/api/satellite/search",
        json={"bbox": BBOX, "start_date": "2026-01-01", "end_date": "2026-06-01", "provider": "demo"},
    ).json()
    return client.post(
        "/api/analysis/run",
        json={
            "bbox": BBOX,
            "before_scene_id": scenes[0]["scene_id"],
            "after_scene_id": scenes[-1]["scene_id"],
            "provider": "demo",
            "resolution_px": 48,
        },
    ).json()


def test_report_generation_structure():
    analysis = _sample_analysis()
    report = generate_report(analysis, "Test Region")
    assert "executive_summary" in report
    assert isinstance(report["key_findings"], list)
    for exp in report["possible_explanations"]:
        assert "observed_change" in exp
        assert "model_inference" in exp
        assert "hypotheses" in exp
    assert report["generation_method"] == "rules_based_template_nlg"


def test_report_endpoint():
    analysis = _sample_analysis()
    r = client.post("/api/report/generate", json={"analysis": analysis, "region_name": "Test Region"})
    assert r.status_code == 200
    assert "executive_summary" in r.json()


def test_export_csv():
    analysis = _sample_analysis()
    csv_text = analysis_to_csv(analysis)
    assert "vegetation_pct" in csv_text
    assert "region_id" in csv_text


def test_export_csv_endpoint():
    analysis = _sample_analysis()
    r = client.post("/api/export/csv", json={"analysis": analysis})
    assert r.status_code == 200
    assert "vegetation_pct" in r.text


def test_export_geojson():
    analysis = _sample_analysis()
    geojson = analysis_to_geojson(analysis, BBOX, 48)
    assert geojson["type"] == "FeatureCollection"
    for feature in geojson["features"]:
        assert feature["geometry"]["type"] == "Polygon"
        assert "change_type" in feature["properties"]


def test_export_geojson_endpoint():
    analysis = _sample_analysis()
    r = client.post("/api/export/geojson", json={"analysis": analysis, "bbox": BBOX, "resolution_px": 48})
    assert r.status_code == 200
    assert r.json()["type"] == "FeatureCollection"
