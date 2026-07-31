from __future__ import annotations

import argparse
import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
os.environ.setdefault("YOLO_CONFIG_DIR", str(WORKSPACE))

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="손상 분류기를 Jetson TensorRT FP16 엔진으로 변환한다.")
    parser.add_argument(
        "--weights",
        type=Path,
        default=WORKSPACE / "ROADY_AI/models/edge/damage_presence_yolo11n_cls_best.pt",
    )
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--workspace", type=float, default=2.0)
    parser.add_argument("--device", default=0)
    args = parser.parse_args()

    output = YOLO(str(args.weights)).export(
        format="engine",
        imgsz=args.imgsz,
        half=True,
        dynamic=False,
        workspace=args.workspace,
        device=args.device,
    )
    print(output)


if __name__ == "__main__":
    main()
