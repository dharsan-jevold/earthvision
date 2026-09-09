# Methodology

## Spectral indices

| Index | Formula | Purpose |
|---|---|---|
| NDVI | `(NIR - Red) / (NIR + Red)` | Vegetation health/coverage. Standard threshold `NDVI > 0.3` used here as "vegetated" — a common rule of thumb, not a universal constant; adjust per biome. |
| NDWI | `(Green - NIR) / (Green + NIR)` | Water body detection (McFeeters, 1996 convention). Threshold `NDWI > 0` used as "water." |
| NDBI | `(SWIR1 - NIR) / (SWIR1 + NIR)` | Built-up/impervious surface detection. Threshold `NDBI > 0` used as "built-up." |

All three are implemented in `backend/app/geospatial/indices.py` as pure, unit-tested functions.

## Change detection — baseline (implemented, running today)

`backend/app/analysis/change_detection.py`:

1. Compute NDVI/NDWI/NDBI for the "before" and "after" scenes.
2. Take per-pixel deltas for each index.
3. A pixel is "changed" if `max(|ΔNDVI|, |ΔNDWI|, |ΔNDBI|) > 0.15` (configurable `CHANGE_MAGNITUDE_THRESHOLD`).
4. Connected-component labeling groups changed pixels into discrete regions (4-connectivity flood fill).
5. Regions smaller than `min_region_px` are discarded as noise.
6. Each region is classified by which index moved the most in which direction (`classify_change`), with an explainable, non-calibrated confidence heuristic based on how far the mean magnitude exceeds the detection threshold.

This is a real, working, scientifically-grounded method — not a placeholder.

## Change detection — unsupervised ML (implemented, running today, Phase 10)

`backend/app/ml/unsupervised_change.py`:

1. Build a per-pixel feature vector from `[ΔNDVI, ΔNDWI, ΔNDBI]` (the same
   deltas the baseline uses).
2. Run K-means clustering (scikit-learn) with a small `k` (default 4) over
   those feature vectors.
3. The cluster with the largest mean feature-vector magnitude is treated as
   the "change" cluster; its pixels become the ML change mask.
4. The same connected-component labeling and classification logic from the
   baseline is reused to turn that mask into discrete, classified regions.
5. The API reports **agreement between the baseline and ML masks as IoU**
   (intersection-over-union) — a real, computed number, not an invented
   accuracy metric — so the two methods can be compared honestly.

This is real unsupervised machine learning (clustering), and a legitimate
"AI change detection" component. It is **not** the trained supervised deep
model (Siamese/U-Net) the spec's Phase 10 ultimately describes — see the next
section for that gap and how to close it.

## Change detection — trained deep learning (NOT yet implemented)

`backend/app/ml/change_model.py` defines the interface for a Siamese/U-Net-style
change detector, intentionally left unimplemented (raises `NotImplementedError`)
rather than faking outputs or accuracy numbers, per project engineering rules.
To make it real:

1. Train on **LEVIR-CD** (building change, CC-BY-4.0, 637 image pairs, 1024×1024,
   0.5m resolution) and/or **OSCD** (Onera Satellite Change Detection, Sentinel-2,
   general land-use change, open license).
2. A ResNet18-encoder Siamese U-Net (~11M params) is realistically trainable on a
   single consumer GPU in a few hours — appropriately sized per the spec's "do not
   use an unnecessarily enormous model" instruction.
3. Evaluate with IoU / Precision / Recall / F1 on the held-out test split, and
   report those numbers directly from the evaluation script — never invented.
4. Export to ONNX/TorchScript; `load_model()` loads the checkpoint; `predict()`
   returns a per-pixel probability map consumed the same way the baseline's
   `change_mask` is today.

## GIS layer rendering (implemented, Phase 12)

`backend/app/geospatial/rendering.py` + `backend/app/services/layers_service.py`:

Each index array (NDVI/NDWI/NDBI) and each change mask (baseline, ML) is
rendered to a standalone PNG with a fixed colormap (diverging red-to-green
for indices, solid highlight for masks), base64-encoded, and returned with
the bounding box needed to place it as a georeferenced image overlay on the
Leaflet/MapLibre map. `/api/analysis/layers` returns all layers plus the
baseline-vs-ML IoU in one call so the frontend can toggle between them
without re-running analysis.

## Time-series analysis (implemented, Phase 13)

`backend/app/analysis/time_series.py`:

Given an ordered list of scene IDs and dates, computes NDVI/NDWI/NDBI mean
and coverage/area at each date, then fits a simple linear trend (least-squares
slope) per indicator to classify it as `increasing`, `decreasing`, or `stable`
(configurable slope threshold). This is a genuinely computed trend, not a
templated sentence — the classification comes directly from the fitted slope
sign and magnitude relative to the threshold.

## Report generation (implemented, Phase 14 — rules-based, not an LLM)

`backend/app/reports/report_generator.py`:

Because no LLM API key is available to this backend, the "AI report" is a
**deterministic, rules-based natural-language generator** over the
structured `AnalyzeResponse` data — not a language model. It explicitly:

- States quantitative findings (vegetation/water/urban change %, region
  counts) as **observed data**, taken directly from the computed indices.
- Ranks and lists the most significant detected change regions by area.
- For "possible causes," emits **template sentences drawn from a fixed,
  small set of hypotheses per change type** (e.g. vegetation loss →
  "land clearing, seasonal variation, or drought"), each explicitly labeled
  as a **hypothesis requiring ground-truth verification** — never asserted
  as fact. This directly implements the spec's requirement (section 17) to
  distinguish observed change / model inference / hypothesis.
- Recommendations are similarly templated per severity/change-type
  combination, not free-form generation.

If an LLM becomes available, this module is the natural place to swap in an
actual language-model call — the structured data it consumes is already the
right shape for that, and the observed/inference/hypothesis distinction
should be preserved in the prompt.

## Authentication & persistence (implemented, Phase 17)

`backend/app/core/security.py` implements password hashing (PBKDF2-HMAC-SHA256,
stdlib `hashlib`, 260,000 iterations — an OWASP-listed scheme) and a
hand-rolled HS256 JWT (stdlib `hmac`/`base64`/`json`) rather than pulling in
`bcrypt`/`python-jose`, whose compiled dependencies are a common source of
install failures on Windows. This is a deliberate simplicity trade-off for a
project of this scope, not a security downgrade — both primitives are
standard, well-understood algorithms.

Persistence uses SQLAlchemy against SQLite by default (`backend/app/database/session.py`),
with three models (`User`, `Project`, `AnalysisRecord` — `backend/app/models/`).
Switching to PostgreSQL/PostGIS is a one-line `DATABASE_URL` change (see
`.env.example`); no model code changes are required for that swap, though
PostGIS-specific spatial columns/queries aren't used yet.

## Export (implemented, Phase 25 — partial)

`backend/app/reports/export.py` provides CSV (per-region + summary stats) and
GeoJSON (change region bounding boxes as polygon features, in the
project's original lon/lat CRS) export, both generated directly from the same
`AnalyzeResponse` data structure the dashboard renders. PNG map export and
PDF report export are not yet implemented.

## Severity thresholds

Defined in `SEVERITY_THRESHOLDS` (`change_detection.py`):

| Severity | Fraction of pixels changed |
|---|---|
| LOW | 0–10% |
| MODERATE | 10–25% |
| HIGH | 25–50% |
| CRITICAL | >50% |

These are **configurable project defaults**, not a peer-reviewed standard — the
spec explicitly requires this framing (section 12).

## Known limitations of the current build

- The demo provider generates **synthetic** band data (smooth procedural fields
  with realistic reflectance ranges), not real Sentinel-2/Landsat pixels. It is
  labeled `is_demo: true` end-to-end, including in the UI.
- No cloud masking / reprojection / resampling pipeline yet — the demo bands are
  already co-registered by construction. A real provider integration needs
  Rasterio/GDAL-based preprocessing (Phase 4–5, not yet built).
- Area math uses an equirectangular approximation (`cos(latitude)` correction),
  fine for city-scale regions, increasingly inaccurate near the poles or for
  very large bounding boxes. A production build should reproject to an
  equal-area CRS before computing areas.
- No async job queue yet — analysis runs synchronously in the request. Fine at
  demo resolution (≤512×512); real imagery at full resolution needs the
  Celery/Redis pipeline described in the spec (Phase 22).
- The "AI change detection" (Phase 10) is unsupervised K-means clustering, not
  a trained supervised model — see the section above for the honest gap and
  what training would require.
- The "AI report" (Phase 14) is rules-based NLG, not LLM-generated — see the
  section above.
- SQLite by default, not PostgreSQL/PostGIS — swappable via `DATABASE_URL`,
  but no PostGIS spatial indexing is in use yet.
- No PDF report export or PNG map export yet (CSV/GeoJSON work).
- No AI chat assistant or predictive-analysis module yet (Phases 15–16).
