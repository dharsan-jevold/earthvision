# Datasets (for training the Phase-10 deep-learning change detector)

None of these are downloaded or bundled in this repo — the app runs entirely
on synthetic demo data until a training run is done. This documents what to
use when that phase happens.

## LEVIR-CD
- **Source**: https://justchenhao.github.io/LEVIR/
- **License**: CC-BY-4.0 (verify current terms on the source page before use)
- **Content**: 637 pairs of 1024×1024 Google Earth image patches, 0.5m/pixel,
  5–14 year time span, building construction/destruction change masks.
- **Use case**: primary training set for the Siamese change detector — building
  change is the best-annotated, highest-quality public change-detection task.

## OSCD (Onera Satellite Change Detection)
- **Source**: https://rcdaudt.github.io/oscd/
- **License**: open for research use (check current terms)
- **Content**: 24 pairs of Sentinel-2 multispectral images (13 bands),
  general urban change detection (not just buildings).
- **Use case**: closer to this project's actual sensor (Sentinel-2), useful for
  fine-tuning after LEVIR-CD pretraining, and for the NDVI/NDWI/NDBI-adjacent
  evaluation described in the research component (spec section 30).

## WHU-CD
- **Source**: http://gpcv.whu.edu.cn/data/building_dataset.html
- **License**: research use — verify before redistribution
- **Content**: Building change detection, aerial imagery, single large scene
  split into tiles.
- **Use case**: secondary/validation set for building-change generalization.

## SEN12MS
- **Source**: https://mediatum.ub.tum.de/1474000
- **License**: CC-BY
- **Content**: Paired Sentinel-1 SAR + Sentinel-2 optical + MODIS land cover,
  not natively a change-detection dataset (single-date), but useful for
  land-cover-aware pretraining or auxiliary supervision.

## Before downloading anything

1. Re-check each dataset's current license page — licenses and hosting can
   change; do not assume the terms above are still current.
2. Respect any required attribution.
3. Do not commit raw dataset files to this git repo — use `data/` (gitignored)
   or object storage, and document the download script instead.
