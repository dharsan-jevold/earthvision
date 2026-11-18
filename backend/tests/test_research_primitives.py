import numpy as np
import pytest

from app.analysis.persistence import PersistenceConfig, summarize_persistence
from app.geospatial.preprocessing import iter_patches, normalize_reflectance, valid_observation_mask
from app.ml.uncertainty import calibration_metrics, summarize_probabilities
from app.ml.research_metrics import binary_change_metrics, risk_coverage, segmentation_metrics


def test_persistence_excludes_missing_observations_and_reports_disclaimer():
    maps = [np.zeros((2, 2), dtype=np.uint8) for _ in range(4)]
    maps[1][0, 0] = 1
    maps[2][0, 0] = 1
    maps[3][0, 0] = 1
    valid = [np.ones((2, 2), bool) for _ in maps]
    valid[1][0, 1] = False
    result = summarize_persistence(maps, valid, PersistenceConfig(minimum_valid_observations=4))
    assert result["status_map"][0, 0] == "persistent_change"
    assert result["status_map"][0, 1] == "insufficient_observations"
    assert "does not prove permanent" in result["disclaimer"]


def test_persistence_thresholds_are_configurable_and_validated():
    config = PersistenceConfig(persistent_fraction=0.6, temporary_fraction=0.2, minimum_valid_observations=2)
    result = summarize_persistence([np.zeros((1, 1)), np.ones((1, 1))], config=config)
    assert result["status_map"][0, 0] == "persistent_change"
    with pytest.raises(ValueError):
        PersistenceConfig(persistent_fraction=0.2, temporary_fraction=0.5)


def test_preprocessing_masks_invalid_cloud_and_shadow_pixels():
    bands = {"red": np.ones((2, 2)), "nir": np.ones((2, 2))}
    bands["red"][0, 0] = np.nan
    cloud = np.array([[False, True], [False, False]])
    shadow = np.array([[False, False], [True, False]])
    valid = valid_observation_mask(bands, cloud, shadow)
    assert valid.tolist() == [[False, False], [False, True]]
    assert normalize_reflectance({"red": np.array([-1, 0.5, 2])})["red"].tolist() == [0.0, 0.5, 1.0]


def test_patch_iterator_and_uncertainty_metrics():
    patches = list(iter_patches(np.zeros((5, 5)), 3, stride=2))
    assert [(row, col) for row, col, _ in patches] == [(0, 0), (0, 2), (2, 0), (2, 2)]
    probabilities = np.array([[[0.9, 0.5]], [[0.1, 0.5]]], dtype=np.float32)
    summary = summarize_probabilities(probabilities)
    assert summary["mean_confidence"] == pytest.approx(0.7)
    assert summary["uncertainty_map"][0, 1] == pytest.approx(1.0)
    metrics = calibration_metrics(np.array([[0.9, 0.1], [0.2, 0.8]]), np.array([0, 1]))
    assert metrics["ece"] == pytest.approx(0.15)
    assert metrics["brier_score"] == pytest.approx(0.05)


def test_research_metrics_are_computed_from_supplied_labels():
    metrics = segmentation_metrics(np.array([0, 1, 1, 1]), np.array([0, 1, 0, 1]), 2)
    assert metrics["overall_accuracy"] == pytest.approx(0.75)
    assert metrics["sample_count"] == 4
    change = binary_change_metrics(np.array([0, 1, 1]), np.array([0, 1, 0]))
    assert change == {"precision": 0.5, "recall": 1.0, "f1": pytest.approx(2 / 3), "iou": 0.5}
    curve = risk_coverage(np.array([0.9, 0.4, 0.8]), np.array([True, False, True]), points=3)
    assert curve[-1]["coverage"] == 1.0
    assert curve[-1]["risk"] == pytest.approx(1 / 3)
