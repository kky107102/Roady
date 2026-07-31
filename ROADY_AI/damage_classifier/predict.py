from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
os.environ.setdefault("YOLO_CONFIG_DIR", str(WORKSPACE))

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="점자블록 ROI의 손상 유무를 분류한다.")
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--model",
        type=Path,
        default=WORKSPACE / "ROADY_AI/models/edge/damage_presence_yolo11n_cls_best.pt",
    )
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--threshold", type=float, default=0.275)
    parser.add_argument("--device", default=0)
    args = parser.parse_args()

    if not 0.0 <= args.threshold <= 1.0:
        raise ValueError("--threshold must be between 0 and 1")
    if not args.source.exists():
        raise FileNotFoundError(args.source)

    result = YOLO(str(args.model)).predict(
        source=str(args.source),
        imgsz=args.imgsz,
        device=args.device,
        verbose=False,
    )[0]
    probabilities = result.probs
    if probabilities is None:
        raise RuntimeError("Classification probabilities are missing")

    names = result.names
    scores = {names[index]: float(score) for index, score in enumerate(probabilities.data.tolist())}
    damage_score = scores.get("damage_suspected")
    if damage_score is None:
        raise RuntimeError(f"damage_suspected class is missing: {sorted(scores)}")

    print(
        json.dumps(
            {
                "source": str(args.source),
                "damage_score": damage_score,
                "threshold": args.threshold,
                "damage_suspected": damage_score >= args.threshold,
                "probabilities": scores,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
