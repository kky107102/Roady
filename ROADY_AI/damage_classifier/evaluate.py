from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

WORKSPACE = Path(__file__).resolve().parents[2]
os.environ.setdefault("YOLO_CONFIG_DIR", str(WORKSPACE))
os.environ.setdefault("MPLCONFIGDIR", str(WORKSPACE / "ROADY_AI/.matplotlib"))

from ultralytics import YOLO
from ultralytics.data.augment import classify_transforms


SOURCE_PATTERN = re.compile(r"^(?P<source>.+)_b(?P<block>\d+)_t(?P<tile>\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--source-detect", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--batch", type=int, default=128)
    return parser.parse_args()


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def metrics_at_threshold(rows: list[dict[str, object]], threshold: float) -> dict[str, float]:
    tp = fp = tn = fn = 0
    for row in rows:
        predicted_damage = float(row["damage_score"]) >= threshold
        actual_damage = row["actual"] == "damage_suspected"
        if predicted_damage and actual_damage:
            tp += 1
        elif predicted_damage:
            fp += 1
        elif actual_damage:
            fn += 1
        else:
            tn += 1
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    specificity = safe_div(tn, tn + fp)
    f1 = safe_div(2 * precision * recall, precision + recall)
    f2 = safe_div(5 * precision * recall, 4 * precision + recall)
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "false_positive_rate": 1.0 - specificity,
        "accuracy": safe_div(tp + tn, tp + fp + tn + fn),
        "f1": f1,
        "f2": f2,
    }


def image_features(path: Path) -> tuple[float, float, float]:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return 0.0, 0.0, 0.0
    return (
        float(image.mean()),
        float(image.std()),
        float(cv2.Laplacian(image, cv2.CV_64F).var()),
    )


def label_features(label_path: Path) -> tuple[int, float]:
    if not label_path.is_file():
        return 0, 0.0
    areas = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 5:
            areas.append(float(parts[3]) * float(parts[4]))
    return len(areas), max(areas, default=0.0)


def area_bucket(area: float) -> str:
    if area < 0.01:
        return "tiny_lt_1pct"
    if area < 0.03:
        return "small_1_to_3pct"
    if area < 0.10:
        return "medium_3_to_10pct"
    return "large_ge_10pct"


def quality_bucket(brightness: float, contrast: float, blur: float) -> str:
    if brightness < 55:
        return "dark"
    if brightness > 205:
        return "bright"
    if contrast < 25:
        return "low_contrast"
    if blur < 80:
        return "blurry"
    return "nominal"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_gallery(rows: list[dict[str, object]], output: Path, title: str) -> None:
    selected = rows[:48]
    if not selected:
        return
    tile_w, tile_h = 320, 230
    columns = 4
    canvas = np.full(
        ((len(selected) + columns - 1) // columns * tile_h, columns * tile_w, 3),
        245,
        dtype=np.uint8,
    )
    for index, row in enumerate(selected):
        image = cv2.imread(str(row["path"]))
        if image is None:
            continue
        scale = min(tile_w / image.shape[1], 175 / image.shape[0])
        resized = cv2.resize(
            image,
            (max(1, int(image.shape[1] * scale)), max(1, int(image.shape[0] * scale))),
        )
        x = (index % columns) * tile_w
        y = (index // columns) * tile_h
        canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
        label = (
            f"score={float(row['damage_score']):.3f} "
            f"area={float(row['max_box_area']):.3f}"
        )
        cv2.putText(
            canvas,
            label,
            (x + 4, y + 194),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            Path(str(row["path"])).name[:43],
            (x + 4, y + 216),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.37,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )
    cv2.putText(
        canvas,
        title,
        (8, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 180),
        2,
        cv2.LINE_AA,
    )
    cv2.imwrite(str(output), canvas)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    test_root = args.dataset / "test"
    dataset = ImageFolder(
        str(test_root),
        transform=classify_transforms(size=args.imgsz),
    )
    loader = DataLoader(
        dataset,
        batch_size=args.batch,
        shuffle=False,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
    )

    model = YOLO(str(args.model))
    damage_index = next(index for index, name in model.names.items() if name == "damage_suspected")
    rows: list[dict[str, object]] = []
    network = model.model.cuda().eval()
    cursor = 0
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
        for images, targets in loader:
            logits = network(images.cuda(non_blocking=True))
            if isinstance(logits, (tuple, list)):
                logits = logits[0]
            is_probability = (
                float(logits.min()) >= 0.0
                and float(logits.max()) <= 1.0
                and torch.allclose(
                    logits.sum(dim=1),
                    torch.ones(logits.shape[0], device=logits.device),
                    atol=1e-3,
                )
            )
            probabilities = (logits if is_probability else logits.softmax(dim=1)).float().cpu()
            for offset, (target, probability) in enumerate(zip(targets.tolist(), probabilities)):
                path = Path(dataset.samples[cursor + offset][0])
                rows.append(
                    {
                        "path": str(path.resolve()),
                        "filename": path.name,
                        "actual": dataset.classes[target],
                        "damage_score": float(probability[damage_index].item()),
                    }
                )
            cursor += len(targets)

    write_csv(args.output / "test_predictions.csv", rows)
    sweep = [
        metrics_at_threshold(rows, round(float(threshold), 3))
        for threshold in np.arange(0.05, 0.951, 0.025)
    ]
    write_csv(args.output / "threshold_sweep.csv", sweep)

    target_options = [
        item for item in sweep if item["recall"] >= 0.85 and item["false_positive_rate"] <= 0.20
    ]
    recommended = max(target_options, key=lambda item: item["precision"], default=None)
    if recommended is None:
        recommended = max(sweep, key=lambda item: item["f2"])

    default_metrics = metrics_at_threshold(rows, 0.5)
    false_negatives = [
        row
        for row in rows
        if row["actual"] == "damage_suspected" and float(row["damage_score"]) < 0.5
    ]
    detailed: list[dict[str, object]] = []
    source_counts: Counter[str] = Counter()
    area_counts: Counter[str] = Counter()
    quality_counts: Counter[str] = Counter()
    tile_counts: Counter[str] = Counter()
    for row in false_negatives:
        path = Path(str(row["path"]))
        match = SOURCE_PATTERN.match(path.stem)
        source = match.group("source") if match else path.stem
        block = int(match.group("block")) if match else -1
        tile = int(match.group("tile")) if match else -1
        source_label = args.source_detect / "labels" / "test" / f"{path.stem}.txt"
        box_count, max_area = label_features(source_label)
        brightness, contrast, blur = image_features(path)
        area_name = area_bucket(max_area)
        quality_name = quality_bucket(brightness, contrast, blur)
        source_counts[source] += 1
        area_counts[area_name] += 1
        quality_counts[quality_name] += 1
        tile_counts[str(tile)] += 1
        detailed.append(
            {
                **row,
                "source_group": source,
                "block_index": block,
                "tile_index": tile,
                "box_count": box_count,
                "max_box_area": max_area,
                "area_bucket": area_name,
                "brightness": brightness,
                "contrast": contrast,
                "laplacian_variance": blur,
                "quality_bucket": quality_name,
            }
        )
    detailed.sort(key=lambda row: float(row["damage_score"]))
    write_csv(args.output / "false_negatives_default_050.csv", detailed)

    source_rows = [
        {"source_group": source, "false_negative_tiles": count}
        for source, count in source_counts.most_common()
    ]
    write_csv(args.output / "false_negative_source_groups.csv", source_rows)
    make_gallery(detailed, args.output / "fn_high_confidence_normal_gallery.jpg", "Damage FN: lowest damage scores")
    make_gallery(
        sorted(detailed, key=lambda row: float(row["damage_score"]), reverse=True),
        args.output / "fn_near_threshold_gallery.jpg",
        "Damage FN: scores nearest 0.5",
    )

    summary = {
        "test_images": len(rows),
        "class_counts": dict(Counter(str(row["actual"]) for row in rows)),
        "default_threshold": default_metrics,
        "recommended_threshold": recommended,
        "false_negative_analysis": {
            "count": len(detailed),
            "unique_source_groups": len(source_counts),
            "area_buckets": dict(area_counts),
            "quality_buckets": dict(quality_counts),
            "tile_indices": dict(tile_counts),
            "top_source_groups": source_rows[:20],
        },
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
