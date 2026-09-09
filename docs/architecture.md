# Architecture

## System overview

```mermaid
flowchart LR
    User((User)) --> FE[React + MapLibre Frontend]
    FE -->|REST /api| BE[FastAPI Backend]
    BE --> AUTH[JWT Auth\nstdlib-only, Phase 17]
    BE --> SAT[Satellite Provider Abstraction]
    SAT --> DEMO[Demo Provider\nsynthetic, no credentials]
    SAT -.future.-> S2[Sentinel-2 Provider\nneeds credentials]
    BE --> GEO[Geospatial: NDVI/NDWI/NDBI]
    BE --> CD[Baseline Change Detection\nindex differencing]
    BE --> MLCD[ML Change Detection\nK-means clustering, Phase 10]
    CD -.Phase 10 remainder.-> DEEP[Deep learning change model\nnot yet trained]
    BE --> TS[Time-series + trend detection\nPhase 13]
    BE --> LAYERS[GIS layer PNG rendering\nPhase 12]
    BE --> RPT[Report generator\nrules-based NLG, Phase 14]
    BE --> EXP[CSV / GeoJSON export\nPhase 25]
    BE --> DB[(SQLite via SQLAlchemy\nPhase 17)]
    DB -.swap DATABASE_URL.-> PG[(Postgres/PostGIS)]
    BE -.not wired.-> QUEUE[Redis + Celery workers\nPhase 22]
```

**What's real today**: Frontend → Backend → Demo Provider → Indices →
baseline + unsupervised-ML change detection → GIS layer overlays →
time-series → report generation → JWT-authenticated project/analysis
persistence (SQLite) → CSV/GeoJSON export. All synchronous (no job queue
yet), all backed by real computation — nothing in this list returns
hardcoded numbers.

**What's scaffolded, not wired in**: the *trained* deep-learning change
model (Phase 10's supervised half — `app/ml/change_model.py` deliberately
raises `NotImplementedError` rather than fake it), Redis/Celery async jobs,
PDF export, the AI chat assistant, and the predictive-analysis module. Each
has a clear extension point (see "Extension points" below).

## Request flow (current)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as FastAPI
    participant P as DemoProvider
    participant AN as Analysis Service
    participant DB as SQLite

    U->>FE: Register / log in
    FE->>BE: POST /api/auth/register, /login
    BE->>DB: create/verify User (PBKDF2 hash)
    BE-->>FE: JWT access token

    U->>FE: Draw region (shift+drag on map)
    U->>FE: Pick date range, click "Find imagery"
    FE->>BE: POST /api/satellite/search
    BE->>P: search(bbox, dates)
    P-->>BE: list[SceneMetadata]
    BE-->>FE: scenes

    U->>FE: Pick before/after scenes, "Run change detection"
    FE->>BE: POST /api/analysis/run
    BE->>AN: run_analysis(bbox, before_id, after_id)
    AN->>P: fetch(before_id), fetch(after_id)
    P-->>AN: SceneRaster (band arrays)
    AN->>AN: NDVI/NDWI/NDBI + differencing + region labeling
    AN->>AN: K-means clustering pass (ml/unsupervised_change.py)
    AN-->>BE: summary + baseline regions + ML regions
    BE-->>FE: AnalyzeResponse

    U->>FE: Toggle a map layer / view time-series / generate report
    FE->>BE: POST /api/analysis/layers | /time-series | /report/generate
    BE-->>FE: georeferenced PNG overlays | trend series | structured report

    U->>FE: "Save to project"
    FE->>BE: POST /api/projects/analyses (Authorization: Bearer <jwt>)
    BE->>DB: persist AnalysisRecord (full result JSON)
    BE-->>FE: saved record

    FE-->>U: Dashboard: stat cards, chart, region list, layers, report
```

## Folder structure

```
earthvision-ai/
├── backend/
│   └── app/
│       ├── api/            # FastAPI routers: routes, auth_routes, project_routes, extras_routes
│       ├── analysis/        # baseline change detection + time_series.py (Phase 13)
│       ├── geospatial/      # NDVI/NDWI/NDBI, area math, rendering.py (PNG layer export, Phase 12)
│       ├── ml/              # unsupervised_change.py (Phase 10, real) + change_model.py (deep model, stub)
│       ├── satellite/       # provider abstraction + demo provider + registry
│       ├── schemas/         # Pydantic request/response models (analysis, auth, project, extras)
│       ├── services/        # orchestration: analysis_service.py, layers_service.py
│       ├── core/            # config.py (settings), security.py (JWT+PBKDF2, stdlib-only), deps.py (auth dependency)
│       ├── models/          # SQLAlchemy models: user.py, project.py, analysis.py
│       ├── database/        # session.py (engine/session/init_db)
│       ├── reports/         # report_generator.py (Phase 14), export.py (Phase 25 — CSV/GeoJSON)
│       ├── workers/         # (Phase 22: Celery tasks — not yet implemented)
│       └── main.py
├── frontend/
│   └── src/
│       ├── components/      # MapSelector, AnalysisPanel, ResultsDashboard,
│       │                    # LayerControls, TimeSeriesPanel, ReportPanel,
│       │                    # AuthWidget, ExportAndSave
│       ├── lib/api.ts        # typed backend client (all endpoints)
│       └── store/            # Zustand app state (incl. auth token, layers, active layer)
├── docs/                    # this documentation
├── docker/                  # (compose files reference backend/frontend Dockerfiles directly)
├── data/                    # local dev data (gitignored, not committed)
└── docker-compose.yml
```

## Extension points (how each stubbed piece plugs in without a rewrite)

- **Real satellite provider**: implement `SatelliteProvider` (see
  `app/satellite/base.py`), register it in `app/satellite/registry.py`. No
  other file changes needed — `analysis_service.py` only calls the interface.
- **Trained deep-learning change model**: implement
  `SiameseChangeDetector.predict()` in `app/ml/change_model.py` once trained
  on LEVIR-CD/OSCD (see `docs/datasets.md`); call it from
  `analysis_service.run_analysis` alongside the existing baseline and
  K-means passes, surfaced as a third `deep_ml_regions` field. The unsupervised
  K-means pass (`app/ml/unsupervised_change.py`) already demonstrates the
  pattern of running a second detector and reporting agreement (IoU) against
  the baseline — the trained model would slot in the same way.
- **PostgreSQL/PostGIS**: change `DATABASE_URL` in `.env` (see
  `.env.example`) from the SQLite default to a `postgresql+psycopg2://...`
  URL and install `psycopg2-binary` — the SQLAlchemy models in `app/models/`
  don't change. Add GeoAlchemy2 geometry columns for true spatial indexing
  when moving off SQLite.
- **Async jobs**: `app/workers/` is where Celery tasks
  (`download_imagery`, `preprocess`, `run_analysis`) would live; the
  `docker-compose.yml` has commented-out `redis`/`worker` services ready to
  uncomment once implemented. `/api/analysis/run` would become a
  "queued → downloading → preprocessing → analyzing → completed" polling
  endpoint instead of a synchronous call.
- **PDF export / AI chat / predictive analysis**: not yet started. PDF export
  would extend `app/reports/export.py` (which already has the CSV/GeoJSON
  pattern to follow); the chat assistant and predictive module are natural
  next additions once an LLM API key or a trained forecasting model is
  available — the structured `AnalyzeResponse` and `AnalysisRecord` data
  already give them something real to ground answers in.
