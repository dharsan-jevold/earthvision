"""Uncertainty and calibration helpers for class-probability maps."""
from __future__ import annotations

import numpy as np


def summarize_probabilities(probabilities: np.ndarray) -> dict:
    """Return max-probability confidence and normalized predictive entropy.

    Max softmax probability is a confidence score, not a calibrated probability.
    """
    probs = np.asarray(probabilities, dtype=np.float32)
    if probs.ndim < 2 or probs.shape[0] < 2:
        raise ValueError("Expected class probabilities with shape [classes, ...].")
    if not np.isfinite(probs).all() or np.any(probs < 0):
        raise ValueError("Probabilities must be finite and non-negative.")
    total = probs.sum(axis=0, keepdims=True)
    if np.any(total <= 0):
        raise ValueError("Each pixel must have positive probability mass.")
    probs = probs / total
    confidence = probs.max(axis=0)
    entropy = -(probs * np.log(np.clip(probs, 1e-8, 1))).sum(axis=0) / np.log(probs.shape[0])
    return {"confidence_map": confidence, "uncertainty_map": entropy, "mean_confidence": float(confidence.mean()), "mean_uncertainty": float(entropy.mean()), "confidence_kind": "maximum class probability; not calibrated"}


def calibration_metrics(probabilities: np.ndarray, labels: np.ndarray, bins: int = 15) -> dict:
    """Compute multiclass ECE and Brier score on a labeled evaluation set."""
    probs = np.asarray(probabilities, dtype=np.float64)
    labels = np.asarray(labels)
    if probs.ndim != 2 or labels.ndim != 1 or len(labels) != len(probs):
        raise ValueError("Expected probabilities [samples, classes] and labels [samples].")
    if bins < 1 or np.any(labels < 0) or np.any(labels >= probs.shape[1]):
        raise ValueError("Invalid bin count or class label.")
    probs = probs / np.clip(probs.sum(axis=1, keepdims=True), 1e-12, None)
    predicted = probs.argmax(axis=1)
    confidence = probs.max(axis=1)
    correct = predicted == labels
    ece = 0.0
    edges = np.linspace(0, 1, bins + 1)
    for i in range(bins):
        in_bin = (confidence >= edges[i]) & (confidence <= edges[i + 1] if i == bins - 1 else confidence < edges[i + 1])
        if in_bin.any():
            ece += float(in_bin.mean() * abs(correct[in_bin].mean() - confidence[in_bin].mean()))
    one_hot = np.eye(probs.shape[1])[labels]
    return {"ece": ece, "brier_score": float(np.mean(np.sum((probs - one_hot) ** 2, axis=1))), "sample_count": len(labels), "bins": bins}
