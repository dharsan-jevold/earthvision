from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "running"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_search_scenes():
    payload = {
        "bbox": {"min_lon": 80.2, "min_lat": 13.0, "max_lon": 80.3, "max_lat": 13.1},
        "start_date": "2026-01-01",
        "end_date": "2026-06-01",
        "provider": "demo",
    }
    r = client.post("/api/satellite/search", json=payload)
    assert r.status_code == 200
    scenes = r.json()
    assert len(scenes) >= 2
    assert all(s["is_demo"] for s in scenes)


def test_search_invalid_provider():
    payload = {
        "bbox": {"min_lon": 80.2, "min_lat": 13.0, "max_lon": 80.3, "max_lat": 13.1},
        "start_date": "2026-01-01",
        "end_date": "2026-06-01",
        "provider": "nonexistent",
    }
    r = client.post("/api/satellite/search", json=payload)
    assert r.status_code == 400


def test_full_analysis_flow():
    bbox = {"min_lon": 80.2, "min_lat": 13.0, "max_lon": 80.3, "max_lat": 13.1}
    search_payload = {
        "bbox": bbox,
        "start_date": "2026-01-01",
        "end_date": "2026-06-01",
        "provider": "demo",
    }
    scenes = client.post("/api/satellite/search", json=search_payload).json()

    analyze_payload = {
        "bbox": bbox,
        "before_scene_id": scenes[0]["scene_id"],
        "after_scene_id": scenes[-1]["scene_id"],
        "provider": "demo",
        "resolution_px": 64,
    }
    r = client.post("/api/analysis/run", json=analyze_payload)
    assert r.status_code == 200
    body = r.json()
    assert body["is_demo"] is True
    assert "vegetation" in body and "water" in body and "urban" in body
    assert body["overall_severity"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert isinstance(body["regions"], list)


def test_analysis_invalid_bbox():
    payload = {
        "bbox": {"min_lon": 80.2, "min_lat": 13.0, "max_lon": 80.2, "max_lat": 13.0},
        "before_scene_id": "DEMO_x",
        "after_scene_id": "DEMO_y",
        "provider": "demo",
    }
    r = client.post("/api/analysis/run", json=payload)
    assert r.status_code == 400
