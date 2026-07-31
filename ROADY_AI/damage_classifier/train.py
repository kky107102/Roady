from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
os.environ.setdefault("YOLO_CONFIG_DIR", str(WORKSPACE))
os.environ.setdefault("MPLCONFIGDIR", str(WORKSPACE / "ROADY_AI/.matplotlib"))

import torch
from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ROADY damage presence classifier.")
    parser.add_argument(
        "--data",
        type=Path,
        default=WORKSPACE / "ROADY_AI/datasets/damage_presence_cls_v1",
    )
    parser.add_argument("--model", default="yolo11n-cls.pt")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--batch", type=int, default=-1)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--name", default="damage_presence_yolo11n_cls_320_v1")
    args = parser.parse_args()

    for split in ("train", "val", "test"):
        for class_name in ("damage_suspected", "normal"):
            directory = args.data / split / class_name
            if not directory.is_dir() or not any(directory.iterdir()):
                raise FileNotFoundError(f"Missing or empty classification directory: {directory}")

    device: int | str = 0 if torch.cuda.is_available() else "cpu"
    print(
        json.dumps(
            {
                "data": str(args.data),
                "model": args.model,
                "device": str(device),
                "imgsz": args.imgsz,
                "batch": args.batch,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    model = YOLO(args.model)
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        project=str(WORKSPACE / "ROADY_AI/runs"),
        name=args.name,
        workers=args.workers,
        seed=42,
        deterministic=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        cos_lr=True,
        warmup_epochs=3.0,
        patience=10,
        hsv_h=0.01,
        hsv_s=0.35,
        hsv_v=0.25,
        degrees=4.0,
        translate=0.08,
        scale=0.20,
        fliplr=0.5,
        flipud=0.0,
        erasing=0.1,
        auto_augment="randaugment",
        dropout=0.1,
        plots=True,
        val=True,
    )


if __name__ == "__main__":
    main()
