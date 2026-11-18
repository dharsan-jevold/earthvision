"""Small reusable preprocessing primitives for aligned multispectral arrays."""
from __future__ import annotations

from collections.abc import Iterator

import numpy as np


def valid_observation_mask(
    bands: dict[str, np.ndarray],
    cloud_mask: np.ndarray | None = None,
    shadow_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Mask cloud/shadow pixels and any pixels with missing band values."""
    if not bands:
        raise ValueError("At least one band is required.")
    arrays = list(bands.values())
    if any(array.shape != arrays[0].shape for array in arrays):
        raise ValueError("Bands must be aligned to the same grid before masking.")
    valid = np.logical_and.reduce([np.isfinite(array) for array in arrays])
    for mask in (cloud_mask, shadow_mask):
        if mask is not None:
            if mask.shape != arrays[0].shape:
                raise ValueError("Cloud and shadow masks must match the band grid.")
            valid &= ~mask.astype(bool)
    return valid


def normalize_reflectance(
    bands: dict[str, np.ndarray],
    lower: float = 0.0,
    upper: float = 1.0,
) -> dict[str, np.ndarray]:
    """Clip reflectance into a declared range; no scene-wise leakage-prone scaling."""
    if not lower < upper:
        raise ValueError("lower must be less than upper.")
    return {name: np.clip(np.asarray(array, dtype=np.float32), lower, upper) for name, array in bands.items()}


def iter_patches(array: np.ndarray, patch_size: int, stride: int | None = None) -> Iterator[tuple[int, int, np.ndarray]]:
    """Yield row, column, patch; skip incomplete edge patches."""
    if array.ndim < 2 or patch_size < 1:
        raise ValueError("Expected an array with two spatial dimensions and positive patch_size.")
    stride = patch_size if stride is None else stride
    if stride < 1:
        raise ValueError("stride must be positive.")
    height, width = array.shape[-2:]
    for row in range(0, height - patch_size + 1, stride):
        for col in range(0, width - patch_size + 1, stride):
            yield row, col, array[..., row:row + patch_size, col:col + patch_size]
