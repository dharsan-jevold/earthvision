"""
Learned change-detection model — NOT YET IMPLEMENTED.

Per the engineering rules in the spec ("Do NOT invent model accuracy"),
this module deliberately does not pretend to run a trained model. It
defines the exact interface the real thing will implement, so the API
and frontend can be wired against it now.

Plan to make this real (Phase 10):
  1. Train a lightweight Siamese U-Net (e.g. ResNet18 encoder, ~11M params)
     on LEVIR-CD (building change) and/or OSCD (Sentinel-2, general change),
     both public and appropriately licensed — see docs/datasets.md.
  2. Export to ONNX or TorchScript, load once at startup in `load_model()`.
  3. `predict()` takes the same before/after band stacks as the baseline
     detector and returns a per-pixel change probability map + a reported
     confidence, sourced from an actual validation-set evaluation (IoU/F1/
     precision/recall computed in tests/test_ml_eval.py) — not asserted.

Until that training run happens, `predict()` raises NotImplementedError
rather than returning fabricated numbers, and the API/analysis service
falls back to the spectral-index baseline (app/analysis/change_detection.py),
which IS real and IS what the app runs today.
"""
from __future__ import annotations

import numpy as np


class SiameseChangeDetector:
    model_name = "siamese-unet-resnet18"
    is_trained = False

    def load_model(self, checkpoint_path: str) -> None:
        raise NotImplementedError(
            "No trained checkpoint exists yet. Train against LEVIR-CD/OSCD "
            "(see docs/datasets.md and docs/methodology.md) and point this "
            "at the resulting checkpoint."
        )

    def predict(self, before_bands: dict[str, np.ndarray], after_bands: dict[str, np.ndarray]) -> np.ndarray:
        raise NotImplementedError(
            "Learned change detector is not trained/available in this build. "
            "The API uses the spectral-index baseline instead — see "
            "app/analysis/change_detection.py. This is intentional: the spec "
            "explicitly forbids inventing model accuracy."
        )
