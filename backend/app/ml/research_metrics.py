"""Evaluation metrics for labeled, geographically held-out research sets."""
from __future__ import annotations

import numpy as np


def segmentation_metrics(prediction: np.ndarray, target: np.ndarray, num_classes: int) -> dict:
    pred, truth = np.asarray(prediction).ravel(), np.asarray(target).ravel()
    valid = (truth >= 0) & (truth < num_classes)
    pred, truth = pred[valid], truth[valid]
    cm = np.bincount(num_classes * truth + pred, minlength=num_classes ** 2).reshape(num_classes, num_classes)
    tp = np.diag(cm).astype(float)
    fp, fn = cm.sum(0) - tp, cm.sum(1) - tp
    denom = 2 * tp + fp + fn
    f1 = np.divide(2 * tp, denom, out=np.zeros_like(tp), where=denom > 0)
    union = tp + fp + fn
    iou = np.divide(tp, union, out=np.zeros_like(tp), where=union > 0)
    return {"overall_accuracy": float(tp.sum() / max(1, cm.sum())), "mean_iou": float(iou[union > 0].mean()) if np.any(union > 0) else 0.0, "per_class_f1": f1.tolist(), "per_class_iou": iou.tolist(), "confusion_matrix": cm.tolist(), "sample_count": int(valid.sum())}


def binary_change_metrics(prediction: np.ndarray, target: np.ndarray) -> dict:
    pred, truth = np.asarray(prediction, bool), np.asarray(target, bool)
    if pred.shape != truth.shape:
        raise ValueError("prediction and target shapes must match")
    tp = int(np.count_nonzero(pred & truth)); fp = int(np.count_nonzero(pred & ~truth)); fn = int(np.count_nonzero(~pred & truth))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": precision, "recall": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0, "iou": tp / (tp + fp + fn) if tp + fp + fn else 0.0}


def risk_coverage(confidence: np.ndarray, correct: np.ndarray, points: int = 20) -> list[dict]:
    conf, ok = np.asarray(confidence).ravel(), np.asarray(correct, bool).ravel()
    if conf.shape != ok.shape or points < 2:
        raise ValueError("Matching confidence/correctness arrays and at least two points are required.")
    order = np.argsort(-conf)
    results = []
    for coverage in np.linspace(1 / points, 1, points):
        n = max(1, int(np.ceil(coverage * len(order))))
        results.append({"coverage": float(n / len(order)), "risk": float(1 - ok[order[:n]].mean())})
    return results
