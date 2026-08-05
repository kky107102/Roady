from __future__ import annotations

import argparse
import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
os.environ.setdefault("YOLO_CONFIG_DIR", str(WORKSPACE))

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Jetson용 TensorRT FP16 엔진을 생성한다.")
    parser.add_argument(
        "--weights",
        type=Path,
        default=WORKSPACE / "ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt",
    )
    parser.add_argument("--imgsz", type=int, default=768)
    parser.add_argument("--workspace", type=float, default=2.0)
    parser.add_argument("--device", default=0)
    args = parser.parse_args()

    model = YOLO(str(args.weights))
    output = model.export(
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
