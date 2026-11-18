"""Temporal persistence summaries for per-observation categorical maps.

Persistence describes evidence across available observations, not permanence
in the real world. Invalid/cloud-obscured pixels are excluded from every rate.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PersistenceConfig:
    persistent_fraction: float = 0.75
    temporary_fraction: float = 0.25
    minimum_valid_observations: int = 3

    def __post_init__(self) -> None:
        if not 0 <= self.temporary_fraction < self.persistent_fraction <= 1:
            raise ValueError("Require 0 <= temporary_fraction < persistent_fraction <= 1.")
        if self.minimum_valid_observations < 2:
            raise ValueError("minimum_valid_observations must be at least 2.")


def summarize_persistence(
    class_maps: list[np.ndarray],
    valid_masks: list[np.ndarray] | None = None,
    config: PersistenceConfig = PersistenceConfig(),
) -> dict:
    """Compare the first valid class with later observations pixel by pixel."""
    if len(class_maps) < 2:
        raise ValueError("At least two observations are required.")
    shape = class_maps[0].shape
    if any(arr.shape != shape for arr in class_maps):
        raise ValueError("All class maps must share the same aligned grid.")
    if valid_masks is None:
        valid_masks = [np.ones(shape, dtype=bool) for _ in class_maps]
    if len(valid_masks) != len(class_maps) or any(mask.shape != shape for mask in valid_masks):
        raise ValueError("A same-shaped validity mask is required for each observation.")

    stack = np.stack(class_maps)
    valid = np.stack(valid_masks).astype(bool)
    count = valid.sum(axis=0)
    first_idx = np.argmax(valid, axis=0)
    first_class = np.take_along_axis(stack, first_idx[None], axis=0)[0]
    valid_change = valid & (stack != first_class[None])
    changed_count = valid_change.sum(axis=0)
    followup_count = np.maximum(count - 1, 0)
    change_fraction = np.divide(changed_count, followup_count, out=np.zeros(shape, dtype=np.float32), where=followup_count > 0)
    enough = count >= config.minimum_valid_observations

    status = np.full(shape, "insufficient_observations", dtype=object)
    status[enough & (change_fraction >= config.persistent_fraction)] = "persistent_change"
    status[enough & (change_fraction <= config.temporary_fraction) & (changed_count > 0)] = "temporary_change"
    status[enough & (change_fraction > config.temporary_fraction) & (change_fraction < config.persistent_fraction)] = "inconsistent_change"
    status[enough & (changed_count == 0)] = "unchanged"

    return {
        "status_map": status,
        "change_fraction_map": change_fraction,
        "valid_observation_count": count,
        "summary": {
            key: int(np.count_nonzero(status == key))
            for key in ("persistent_change", "temporary_change", "inconsistent_change", "insufficient_observations", "unchanged")
        },
        "config": {
            "persistent_fraction": config.persistent_fraction,
            "temporary_fraction": config.temporary_fraction,
            "minimum_valid_observations": config.minimum_valid_observations,
        },
        "disclaimer": "Persistence is evidence across available valid observations; it does not prove permanent real-world transformation.",
    }
