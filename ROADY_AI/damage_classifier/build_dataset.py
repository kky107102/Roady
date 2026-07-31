from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build normal/damage_suspected classification data from ROI detect tiles."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--train-negative-ratio",
        type=float,
        default=1.5,
        help="Maximum normal/damage_suspected image ratio in train.",
    )
    return parser.parse_args()


def stable_score(stem: str) -> int:
    return int.from_bytes(hashlib.sha256(stem.encode("utf-8")).digest()[:8], "big")


def link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def main() -> None:
    args = parse_args()
    if args.output.exists() and any(args.output.rglob("*")):
        raise FileExistsError(f"Output must be absent or empty: {args.output}")
    if args.train_negative_ratio < 1.0:
        raise ValueError("--train-negative-ratio must be at least 1.0")

    report: dict[str, object] = {
        "source": str(args.source.resolve()),
        "output": str(args.output.resolve()),
        "train_negative_ratio": args.train_negative_ratio,
        "splits": {},
    }

    for split in ("train", "val", "test"):
        image_dir = args.source / "images" / split
        label_dir = args.source / "labels" / split
        images = sorted(
            (path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS),
            key=lambda path: path.name,
        )
        positives: list[Path] = []
        negatives: list[Path] = []
        errors: list[str] = []

        for image in images:
            label = label_dir / f"{image.stem}.txt"
            if not label.is_file():
                errors.append(f"missing label: {image.name}")
                continue
            lines = [line for line in label.read_text(encoding="utf-8").splitlines() if line.strip()]
            (positives if lines else negatives).append(image)

        selected_negatives = negatives
        if split == "train":
            limit = int(len(positives) * args.train_negative_ratio)
            selected_negatives = sorted(negatives, key=lambda path: stable_score(path.stem))[:limit]

        counts = Counter()
        for class_name, selected in (
            ("damage_suspected", positives),
            ("normal", selected_negatives),
        ):
            for image in selected:
                link_or_copy(image, args.output / split / class_name / image.name)
                counts[class_name] += 1

        report["splits"][split] = {
            "source_images": len(images),
            "damage_suspected": counts["damage_suspected"],
            "normal": counts["normal"],
            "excluded_train_negatives": (
                len(negatives) - len(selected_negatives) if split == "train" else 0
            ),
            "errors": errors[:50],
        }
        if errors:
            raise RuntimeError(f"{split}: {len(errors)} source image/label mismatches")

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
