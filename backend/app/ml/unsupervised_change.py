"""
Phase 10 — AI/ML change detection.

This is deliberately an UNSUPERVISED method (K-means clustering over
per-pixel spectral difference vectors), not a supervised deep-learning
model. Why: a supervised Siamese/U-Net model (see app/ml/change_model.py)
needs labeled training data and a real training run to report honest
accuracy numbers — neither exists in this environment. Clustering needs no
training data, runs today, and is a legitimate ML technique for anomaly/
change detection in remote sensing (widely used as a baseline in the
literature, e.g. change vector analysis + clustering).

What it does:
  1. Build a per-pixel feature vector from band differences (before -> after)
     plus the three spectral index deltas.
  2. Standardize features, run K-means with k=3 (stable/minor-change/
     major-change clusters), ordered by mean change magnitude.
  3. The highest-magnitude cluster is treated as "ML-detected change".

This *complements* the baseline threshold method — the API returns both,
and their agreement (IoU between the two masks) is itself a useful
diagnostic, which is what the spec's research component (section 30) asks
to compare.
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans

from app.geospatial import indices as idx


def ml_change_mask(
    before_bands: dict[str, np.ndarray],
    after_bands: dict[str, np.ndarray],
    n_clusters: int = 3,
    random_state: int = 42,
) -> dict:
    band_names = sorted(before_bands.keys())
    h, w = before_bands[band_names[0]].shape

    diff_features = [
        (after_bands[b] - before_bands[b]).flatten() for b in band_names
    ]

    ndvi_before = idx.ndvi(before_bands["nir"], before_bands["red"])
    ndvi_after = idx.ndvi(after_bands["nir"], after_bands["red"])
    ndwi_before = idx.ndwi(before_bands["green"], before_bands["nir"])
    ndwi_after = idx.ndwi(after_bands["green"], after_bands["nir"])
    ndbi_before = idx.ndbi(before_bands["swir1"], before_bands["nir"])
    ndbi_after = idx.ndbi(after_bands["swir1"], after_bands["nir"])

    index_diffs = [
        (ndvi_after - ndvi_before).flatten(),
        (ndwi_after - ndwi_before).flatten(),
        (ndbi_after - ndbi_before).flatten(),
    ]

    features = np.stack(diff_features + index_diffs, axis=1)  # (n_pixels, n_features)

    mean = features.mean(axis=0)
    std = features.std(axis=0) + 1e-8
    features_std = (features - mean) / std

    k = min(n_clusters, max(1, features_std.shape[0]))
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=random_state)
    labels = kmeans.fit_predict(features_std)

    # Rank clusters by mean absolute change magnitude (raw, unstandardized
    # feature space) so "highest magnitude" is physically meaningful.
    magnitude = np.abs(features).mean(axis=1)
    cluster_magnitudes = [
        float(magnitude[labels == c].mean()) if np.any(labels == c) else 0.0
        for c in range(k)
    ]
    change_cluster = int(np.argmax(cluster_magnitudes))

    change_mask = (labels == change_cluster).reshape(h, w)

    return {
        "change_mask": change_mask,
        "method": "kmeans_spectral_difference_clustering",
        "n_clusters": k,
        "cluster_magnitudes": cluster_magnitudes,
        "change_cluster_index": change_cluster,
    }


def mask_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Intersection-over-union between two boolean masks — used to compare
    the baseline (index-differencing) and ML (clustering) methods, per the
    spec's research component (section 30)."""
    intersection = np.logical_and(mask_a, mask_b).sum()
    union = np.logical_or(mask_a, mask_b).sum()
    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    return float(intersection / union)
