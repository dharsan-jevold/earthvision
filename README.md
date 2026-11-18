# EarthVision AI — Satellite Earth Intelligence & Change Detection Platform

An AI-powered platform for detecting, quantifying, and classifying land-use
change (vegetation, water, built-up area) between two dates over a
user-selected geographic region, using spectral-index analysis, unsupervised
ML change detection, and a full GIS dashboard.

**Project status: 12 of the spec's 20 phases are implemented and runnable
end-to-end** (1–14 with a couple of partials — see the table below).
Everything from region selection through change detection, GIS layer
overlays, time-series trends, report generation, and authenticated
project/analysis persistence works today, on synthetic demo data (clearly
labeled). See `docs/architecture.md` for exactly what's real vs. scaffolded
and why, and "Honest limitations" below.

| Phase | Status |
|---|---|
| 1–9 (repo, map, provider, NDVI/NDWI/NDBI, baseline change detection) | ✅ Done |
| 10 (AI change detection) | ✅ Done — unsupervised K-means clustering, not a trained deep model (see methodology.md) |
| 11 (change classification) | ✅ Done |
| 12 (GIS dashboard w/ layer toggles) | ✅ Done — NDVI/NDWI/NDBI/change-mask overlays on the map |
| 13 (time-series analysis) | ✅ Done |
| 14 (AI report generation) | ✅ Done — rules-based NLG, explicitly not LLM-authored (see methodology.md) |
| 17 (auth/database) | ✅ Done — JWT auth + SQLite persistence of projects/analyses |
| 25 (export) | ✅ Done — CSV, GeoJSON (PNG map export not yet built) |
| 5 (real preprocessing pipeline) | ⚠️ Partial |
| 18 (testing) | ⚠️ Partial — backend only, 36 tests |
| 20 (documentation) | ⚠️ Partial |
| 15 (AI chat assistant), 16 (predictive analysis) | ❌ Not started |

## What works right now

1. Register/login (JWT auth).
2. Draw a region on an interactive map (Shift+drag).
3. Pick a date range → search returns available (synthetic) imagery scenes.
4. Pick before/after scenes → run change detection.
5. See NDVI/NDWI/NDBI-derived vegetation, water, and built-up change stats,
   an overall severity rating, and a list of classified, geolocated change
   regions with confidence scores — computed live from the spectral-index
   differencing baseline (real math, not hardcoded numbers).
6. Toggle GIS map layers (NDVI/NDWI/NDBI/baseline-change/ML-change) as
   georeferenced overlays directly on the map, with baseline-vs-ML agreement
   (IoU) shown.
7. Run multi-date time-series analysis with trend detection (increasing/
   decreasing/stable) charted per indicator.
8. Generate a structured analytical report (executive summary, key findings,
   ranked significant areas, explicitly-labeled hypotheses for possible
   causes, recommendations).
9. Save analyses to named projects and reload them later.
10. Export results as CSV or GeoJSON.

## Run locally

You only need Python 3.10+ and Node.js/npm. The backend uses SQLite by default,
so there is no database server to install or start. Start the backend and
frontend in two separate terminals.

### Backend

From the project root, run:

```bash
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt  # optional: test dependencies
python -m uvicorn app.main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

If PowerShell blocks virtual environment activation, run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal,
then activate `.venv` again. On macOS/Linux, create and activate the environment
with `python3 -m venv .venv` and `source .venv/bin/activate` instead.

### Frontend

Open a second terminal from the project root:

```bash
cd frontend
npm install
npm run dev
# App at http://localhost:5173
```

The frontend defaults to `http://localhost:8000/api`; no `.env` file is needed
for local development. Set `VITE_API_BASE` in `frontend/.env` only if the API
is running at a different address.

### Tests
```bash
cd backend
python -m pytest tests/ -v
# 36 tests: index math, change detection, ML clustering, time-series,
# report generation, export, auth/persistence, full API flow
```

### Research pipeline status

The existing two-date demo analysis remains available. Reusable preprocessing
primitives now provide aligned-band validation, cloud/shadow and missing-value
masks, reflectance clipping, and patch iteration. Temporal persistence helpers
exclude invalid observations and expose configurable thresholds; they describe
evidence across the available dates and do not prove permanent change.

The supervised multi-temporal model, real Sentinel-2/Landsat acquisition,
calibrated model uncertainty, and experimentally validated metrics still
require training/reference data and further integration. Index-based and
synthetic demo outputs are baselines, not trained semantic predictions. No
research performance scores are reported without labeled evaluation data.

Optional training scaffold: install a CUDA-compatible PyTorch build, prepare
geographically separate `.npz` archives with `observations[N,T,C,H,W]` and
`labels[N,T,H,W]` (`-1` for ignored pixels), then run from `backend`:

```bash
python -m pip install -r requirements-ml.txt
python scripts/train_temporal.py --train data/train.npz --validation data/validation.npz
```

The split must be by geographic region, not random neighboring patches. The
provided metric helpers calculate segmentation/change and calibration scores
only when reference labels are supplied; the training script does not claim
those scores by itself.

## Why demo data, and how to connect a real satellite provider

No satellite API credentials are available in this environment, so the app
ships a `DemoProvider` that generates synthetic-but-structurally-realistic
multispectral scenes (deterministic per bbox+date, so results are
reproducible). It is labeled `is_demo: true` everywhere — API responses and
the UI both surface a visible "DEMO DATA" badge.

The provider interface (`backend/app/satellite/base.py`) is designed so a
real provider (Sentinel-2 via Copernicus Data Space, Landsat via USGS, or
Google Earth Engine) can be added by implementing `SatelliteProvider` and
registering it in `backend/app/satellite/registry.py` — no other code
changes required. See `docs/architecture.md` → "Extension points."

## Documentation

- `docs/architecture.md` — system diagrams, data flow, folder structure, extension points
- `docs/methodology.md` — NDVI/NDWI/NDBI formulas, change-detection algorithm, severity thresholds, known limitations
- `docs/datasets.md` — public datasets for training the (not-yet-trained) deep-learning change model

## Honest limitations (read this)

- **Demo data, not real satellite imagery.** Do not present analysis results
  from this build as real environmental findings.
- **No trained deep-learning model.** `app/ml/change_model.py` (the
  Siamese/U-Net interface) deliberately raises `NotImplementedError` rather
  than fabricate accuracy numbers. The running "AI change detection" is
  unsupervised K-means clustering (`app/ml/unsupervised_change.py`) — a real,
  legitimate ML technique, but not the trained supervised model the spec's
  Phase 10 ultimately envisions.
- **Report generation is rules-based NLG, not an LLM.** No language-model API
  key is available in this backend, so `app/reports/report_generator.py` is a
  deterministic template over structured data, explicitly labeled as such —
  it does not "hallucinate" causes; it tags every possible-cause statement as
  an unverified hypothesis.
- **SQLite, not PostgreSQL/PostGIS.** The database models are ORM-based
  (SQLAlchemy) and swap to Postgres by changing `DATABASE_URL` — no code
  changes needed — but PostGIS-specific spatial queries aren't used yet.
- **No async job queue.** Everything runs synchronously in-request. Fine at
  demo resolution; real imagery at full resolution needs the Celery/Redis
  pipeline described in the spec (Phase 22), which is still just scaffolded.
- **No PDF export, AI chat assistant, or predictive-analysis module yet.**
  CSV and GeoJSON export work; PNG map export and PDF reports don't yet.

## Suggested next increments (in spec order)

1. Wire Rasterio-based preprocessing for a real provider (Phase 3–5).
2. Add Celery/Redis so `/analysis/run` becomes async with progress polling (Phase 22).
3. Train the Siamese U-Net on LEVIR-CD, wire `predict()` in, report real eval metrics (Phase 10, supervised half).
4. PDF report export and PNG map export (Phase 25, remainder).
5. AI chat assistant grounded in stored analysis results, and the predictive-analysis module (Phases 15–16).
6. Frontend test coverage (Phase 18, remainder).
