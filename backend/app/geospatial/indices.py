"""
Spectral index calculations. Pure functions over numpy arrays — no I/O,
easily unit-testable (see tests/test_indices.py).
"""
from __future__ import annotations

import numpy as np

EPS = 1e-8


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Normalized Difference Vegetation Index. Range [-1, 1]."""
    return (nir - red) / (nir + red + EPS)


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Water Index (McFeeters). Range [-1, 1]."""
    return (green - nir) / (green + nir + EPS)


def ndbi(swir1: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Built-up Index. Range [-1, 1]."""
    return (swir1 - nir) / (swir1 + nir + EPS)


def coverage_fraction(index_array: np.ndarray, threshold: float, above: bool = True) -> float:
    """Fraction of pixels above (or below) a threshold, e.g. NDVI > 0.3 = vegetation."""
    if above:
        mask = index_array > threshold
    else:
        mask = index_array < threshold
    return float(np.mean(mask))


def index_stats(index_array: np.ndarray) -> dict:
    return {
        "mean": float(np.mean(index_array)),
        "min": float(np.min(index_array)),
        "max": float(np.max(index_array)),
        "std": float(np.std(index_array)),
    }
