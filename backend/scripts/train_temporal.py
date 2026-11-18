"""Train a temporal segmentation model from pre-split NumPy patch archives.

Each archive contains observations [N,T,C,H,W] and labels [N,T,H,W]; label -1
marks ignored pixels. Training and validation archives must use separate regions.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from app.ml.temporal_model import TemporalSegmentationModel


def load_archive(path: Path):
    data = np.load(path)
    observations = torch.from_numpy(data["observations"].astype("float32"))
    labels = torch.from_numpy(data["labels"].astype("int64"))
    if observations.ndim != 5 or labels.shape != (observations.shape[0], observations.shape[1], observations.shape[3], observations.shape[4]):
        raise ValueError(f"Invalid observations/labels dimensions in {path}")
    return TensorDataset(observations, labels)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("checkpoints/temporal.pt"))
    parser.add_argument("--classes", type=int, default=5)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train = DataLoader(load_archive(args.train), batch_size=args.batch_size, shuffle=True)
    validation = DataLoader(load_archive(args.validation), batch_size=args.batch_size)
    in_channels = train.dataset.tensors[0].shape[2]
    model = TemporalSegmentationModel(in_channels, args.classes, args.width).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    amp_enabled = device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)
    best_val = float("inf")
    for epoch in range(args.epochs):
        model.train(); train_loss = 0.0
        for observations, labels in train:
            observations, labels = observations.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp_enabled):
                logits = model(observations)
                loss = torch.nn.functional.cross_entropy(logits.flatten(0, 1), labels.flatten(0, 1), ignore_index=-1)
            scaler.scale(loss).backward(); scaler.step(optimizer); scaler.update()
            train_loss += loss.item()
        model.eval(); val_loss = 0.0
        with torch.no_grad():
            for observations, labels in validation:
                observations, labels = observations.to(device), labels.to(device)
                val_loss += torch.nn.functional.cross_entropy(model(observations).flatten(0, 1), labels.flatten(0, 1), ignore_index=-1).item()
        val_loss /= max(1, len(validation))
        print(json.dumps({"epoch": epoch + 1, "train_loss": train_loss / max(1, len(train)), "validation_loss": val_loss, "device": str(device)}))
        if val_loss < best_val:
            best_val = val_loss; args.output.parent.mkdir(parents=True, exist_ok=True)
            torch.save({"state_dict": model.state_dict(), "config": {"in_channels": in_channels, "num_classes": args.classes, "width": args.width}, "seed": args.seed, "epoch": epoch + 1, "validation_loss": val_loss}, args.output)
    print(f"Best checkpoint: {args.output}; scores are training diagnostics, not research metrics.")


if __name__ == "__main__":
    main()
