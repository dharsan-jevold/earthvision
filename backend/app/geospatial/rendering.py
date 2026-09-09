"""
Phase 12 — GIS dashboard layer rendering.

Converts a 2D float array (index values, or a boolean change mask) into a
colored, semi-transparent PNG that the frontend overlays directly on the
map using MapLibre's image source (georeferenced by the same bbox used to
fetch the data — pixel [0,0] is the top-left/NW corner).
"""
from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image

# Diverging colormap for index layers: red (low/negative) -> white (zero) -> green (high/positive)
def _diverging_colormap(normalized: np.ndarray) -> np.ndarray:
    # normalized in [-1, 1]
    r = np.where(normalized < 0, 255, 255 - (normalized * 255).clip(0, 255).astype(np.uint8))
    g = np.where(normalized < 0, 255 + (normalized * 255).clip(-255, 0).astype(np.int16), 255).clip(0, 255).astype(np.uint8)
    b = np.where(normalized < 0, 255 + (normalized * 255).clip(-255, 0).astype(np.int16), 255 - (normalized * 255).clip(0, 255).astype(np.uint8)).clip(0, 255).astype(np.uint8)
    return np.stack([r, g, b], axis=-1)


def render_index_png(index_array: np.ndarray, opacity: int = 190) -> str:
    """Render an index array (values roughly in [-1, 1]) as a base64 PNG data URL."""
    clipped = np.clip(index_array, -1, 1)
    rgb = _diverging_colormap(clipped)
    alpha = np.full(clipped.shape, opacity, dtype=np.uint8)
    rgba = np.dstack([rgb, alpha])
    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def render_mask_png(mask: np.ndarray, color: tuple[int, int, int] = (239, 68, 68), opacity: int = 160) -> str:
    """Render a boolean mask as a solid-color, semi-transparent PNG (0 = fully transparent)."""
    h, w = mask.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0] = color[0]
    rgba[..., 1] = color[1]
    rgba[..., 2] = color[2]
    rgba[..., 3] = np.where(mask, opacity, 0).astype(np.uint8)
    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"
