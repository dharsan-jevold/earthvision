import os

# Use an isolated on-disk test DB so this doesn't collide with dev data.
os.environ["DATABASE_URL"] = "sqlite:///./test_earthvision.db"

import pytest
from fastapi.testclient import TestClient

from app.database.session import Base, engine
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _register_and_login(email="test@example.com", password="supersecret1"):
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_register_and_login():
    token = _register_and_login()
    assert token
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "test@example.com"


def test_duplicate_registration_rejected():
    _register_and_login()
    r = client.post("/api/auth/register", json={"email": "test@example.com", "password": "supersecret1"})
    assert r.status_code == 400


def test_login_wrong_password_rejected():
    _register_and_login()
    r = client.post("/api/auth/login", json={"email": "test@example.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_unauthenticated_request_rejected():
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_create_and_list_projects():
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Chennai Coastal Region",
        "bbox": {"min_lon": 80.2, "min_lat": 13.0, "max_lon": 80.3, "max_lat": 13.1},
    }
    r = client.post("/api/projects", json=payload, headers=headers)
    assert r.status_code == 201
    project_id = r.json()["id"]

    r = client.get("/api/projects", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == project_id


def test_save_and_retrieve_analysis():
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    bbox = {"min_lon": 80.2, "min_lat": 13.0, "max_lon": 80.3, "max_lat": 13.1}

    project = client.post(
        "/api/projects", json={"name": "Test region", "bbox": bbox}, headers=headers
    ).json()

    scenes = client.post(
        "/api/satellite/search",
        json={"bbox": bbox, "start_date": "2026-01-01", "end_date": "2026-06-01", "provider": "demo"},
    ).json()
    analysis = client.post(
        "/api/analysis/run",
        json={
            "bbox": bbox,
            "before_scene_id": scenes[0]["scene_id"],
            "after_scene_id": scenes[-1]["scene_id"],
            "provider": "demo",
            "resolution_px": 48,
        },
    ).json()

    save_payload = {
        "project_id": project["id"],
        "before_scene_id": scenes[0]["scene_id"],
        "after_scene_id": scenes[-1]["scene_id"],
        "provider": "demo",
        "result": analysis,
    }
    r = client.post("/api/projects/analyses", json=save_payload, headers=headers)
    assert r.status_code == 201
    record_id = r.json()["id"]

    r = client.get(f"/api/projects/{project['id']}/analyses", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get(f"/api/projects/analyses/{record_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["result_json"]["overall_severity"] == analysis["overall_severity"]


def test_cannot_access_other_users_project():
    token_a = _register_and_login("a@example.com", "passwordone1")
    token_b = _register_and_login("b@example.com", "passwordtwo1")
    bbox = {"min_lon": 80.2, "min_lat": 13.0, "max_lon": 80.3, "max_lat": 13.1}
    project = client.post(
        "/api/projects",
        json={"name": "Private", "bbox": bbox},
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()

    r = client.get(
        f"/api/projects/{project['id']}/analyses",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 404
