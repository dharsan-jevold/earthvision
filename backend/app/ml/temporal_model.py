"""Optional PyTorch shared-encoder temporal semantic segmentation model.

Input tensors use [batch, time, bands, height, width]. The same encoder is
applied at every date and temporal attention operates independently per pixel.
This is a research baseline architecture, not a trained model.
"""
from __future__ import annotations

try:
    import torch
    from torch import nn
    import torch.nn.functional as F
except ImportError as exc:  # provide a useful error without making torch mandatory
    raise ImportError("Install the optional ML dependencies with requirements-ml.txt to use TemporalSegmentationModel.") from exc


class TemporalSegmentationModel(nn.Module):
    def __init__(self, in_channels: int, num_classes: int = 5, width: int = 32, heads: int = 4, dropout: float = 0.1):
        super().__init__()
        if width % heads:
            raise ValueError("width must be divisible by heads")
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, width, 3, stride=2, padding=1), nn.BatchNorm2d(width), nn.GELU(),
            nn.Conv2d(width, width, 3, stride=2, padding=1), nn.BatchNorm2d(width), nn.GELU(),
            nn.Dropout2d(dropout),
        )
        layer = nn.TransformerEncoderLayer(width, heads, dim_feedforward=width * 4, dropout=dropout, batch_first=True, norm_first=True)
        self.temporal = nn.TransformerEncoder(layer, num_layers=2, enable_nested_tensor=False)
        self.decoder = nn.Sequential(nn.Conv2d(width, width, 3, padding=1), nn.GELU(), nn.Dropout2d(dropout), nn.Conv2d(width, num_classes, 1))

    def forward(self, observations: torch.Tensor, valid_time_mask: torch.Tensor | None = None) -> torch.Tensor:
        if observations.ndim != 5:
            raise ValueError("Expected observations shaped [B,T,C,H,W].")
        batch, steps, channels, height, width = observations.shape
        if channels != self.in_channels or steps < 2:
            raise ValueError("Input channel count must match and at least two dates are required.")
        encoded = self.encoder(observations.reshape(batch * steps, channels, height, width))
        _, features, small_h, small_w = encoded.shape
        encoded = encoded.reshape(batch, steps, features, small_h, small_w).permute(0, 3, 4, 1, 2)
        sequence = encoded.reshape(batch * small_h * small_w, steps, features)
        padding_mask = None
        if valid_time_mask is not None:
            if valid_time_mask.shape != (batch, steps):
                raise ValueError("valid_time_mask must have shape [B,T].")
            padding_mask = ~valid_time_mask.bool().repeat_interleave(small_h * small_w, dim=0)
        sequence = self.temporal(sequence, src_key_padding_mask=padding_mask)
        sequence = sequence.reshape(batch, small_h, small_w, steps, features).permute(0, 3, 4, 1, 2)
        decoded = self.decoder(sequence.reshape(batch * steps, features, small_h, small_w))
        decoded = F.interpolate(decoded, size=(height, width), mode="bilinear", align_corners=False)
        return decoded.reshape(batch, steps, self.num_classes, height, width)


def monte_carlo_probabilities(model: nn.Module, observations: torch.Tensor, samples: int = 8) -> torch.Tensor:
    """Dropout sample probabilities; returns mean probabilities and variance."""
    if samples < 2:
        raise ValueError("At least two MC samples are required.")
    model.train()  # retain dropout while batch norm is set to eval below
    for module in model.modules():
        if isinstance(module, nn.modules.batchnorm._BatchNorm):
            module.eval()
    with torch.no_grad():
        draws = torch.stack([model(observations).softmax(dim=2) for _ in range(samples)])
    return draws.mean(dim=0), draws.var(dim=0, unbiased=False)
