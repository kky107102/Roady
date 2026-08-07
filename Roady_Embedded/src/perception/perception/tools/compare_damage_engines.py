from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from perception.algorithms.tensorrt_lower_limb_detector import (
    TensorRTDetection,
    TensorRTLowerLimbDetector,
)


CLASS_NAMES = ("tactile_block", "damage_candidate")
COLORS = ((40, 210, 40), (30, 30, 240))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _percentile(values: list[float], percentile: float) -> float:
    return float(np.percentile(np.asarray(values), percentile))


def _run_engine(
    label: str,
    engine_path: Path,
    video_path: Path,
    confidence: float,
    iou: float,
    warmup: int,
) -> tuple[list[list[dict]], dict]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    ok, first_frame = capture.read()
    if not ok:
        raise RuntimeError(f"Could not read first frame: {video_path}")

    detector = TensorRTLowerLimbDetector(
        engine_path,
        confidence=confidence,
        iou_threshold=iou,
        class_names=CLASS_NAMES,
    )
    try:
        for _ in range(warmup):
            detector.detect(first_frame)

        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        results: list[list[dict]] = []
        latencies_ms: list[float] = []
        class_counts: Counter[str] = Counter()
        started = time.perf_counter()
        frame_index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            inference_started = time.perf_counter()
            detections, _ = detector.detect(frame)
            latencies_ms.append((time.perf_counter() - inference_started) * 1000.0)
            serialized = [asdict(detection) for detection in detections]
            results.append(serialized)
            class_counts.update(detection.label for detection in detections)
            frame_index += 1
            if frame_index % 100 == 0:
                print(f"[{label}] {frame_index} frames", flush=True)
        elapsed = time.perf_counter() - started
    finally:
        capture.release()
        detector.close()

    mean_ms = float(np.mean(latencies_ms))
    metrics = {
        "label": label,
        "engine": str(engine_path),
        "engine_sha256": _sha256(engine_path),
        "frames": len(results),
        "wall_time_sec_including_decode": elapsed,
        "throughput_fps_including_decode": len(results) / elapsed,
        "latency_ms": {
            "mean": mean_ms,
            "p50": _percentile(latencies_ms, 50),
            "p95": _percentile(latencies_ms, 95),
            "p99": _percentile(latencies_ms, 99),
            "min": min(latencies_ms),
            "max": max(latencies_ms),
        },
        "model_pipeline_fps": 1000.0 / mean_ms,
        "detections": dict(class_counts),
        "frames_with_damage_candidate": sum(
            any(item["label"] == "damage_candidate" for item in frame_result)
            for frame_result in results
        ),
    }
    return results, metrics


def _draw_detections(frame: np.ndarray, detections: list[dict]) -> None:
    for detection in detections:
        class_id = int(detection["class_id"])
        color = COLORS[class_id]
        x1, y1, x2, y2 = (int(round(value)) for value in detection["xyxy"])
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = f'{detection["label"]} {detection["confidence"]:.2f}'
        cv2.putText(
            frame, text, (x1, max(22, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, color, 2, cv2.LINE_AA,
        )


def _add_header(frame: np.ndarray, label: str, metrics: dict, frame_detections: list[dict]) -> None:
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 70), (0, 0, 0), -1)
    damage_count = sum(item["label"] == "damage_candidate" for item in frame_detections)
    line1 = f"{label} | model pipeline {metrics['model_pipeline_fps']:.1f} FPS"
    line2 = f"mean {metrics['latency_ms']['mean']:.2f} ms | damage candidates: {damage_count}"
    cv2.putText(frame, line1, (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, line2, (14, 57), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (220, 220, 220), 1, cv2.LINE_AA)


def _write_comparison(
    source: Path,
    output: Path,
    v2_results: list[list[dict]],
    v3_results: list[list[dict]],
    v2_metrics: dict,
    v3_metrics: dict,
    panel_width: int,
) -> None:
    capture = cv2.VideoCapture(str(source))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    panel_height = round(source_height * panel_width / source_width)
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps,
        (panel_width * 2, panel_height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not open output video: {output}")
    try:
        frame_index = 0
        frame_limit = min(len(v2_results), len(v3_results))
        while frame_index < frame_limit:
            ok, frame = capture.read()
            if not ok:
                break
            left = frame.copy()
            right = frame.copy()
            _draw_detections(left, v2_results[frame_index])
            _draw_detections(right, v3_results[frame_index])
            left = cv2.resize(left, (panel_width, panel_height))
            right = cv2.resize(right, (panel_width, panel_height))
            _add_header(left, "v2", v2_metrics, v2_results[frame_index])
            _add_header(right, "v3", v3_metrics, v3_results[frame_index])
            writer.write(np.hstack((left, right)))
            frame_index += 1
    finally:
        capture.release()
        writer.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two damage TensorRT engines on one video")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--v2", type=Path, required=True)
    parser.add_argument("--v3", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--confidence", type=float, default=0.15)
    parser.add_argument("--iou", type=float, default=0.45)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--panel-width", type=int, default=960)
    args = parser.parse_args()

    paths = [args.video, args.v2, args.v3]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    v2_results, v2_metrics = _run_engine(
        "v2", args.v2.resolve(), args.video.resolve(), args.confidence, args.iou, args.warmup
    )
    v3_results, v3_metrics = _run_engine(
        "v3", args.v3.resolve(), args.video.resolve(), args.confidence, args.iou, args.warmup
    )
    _write_comparison(
        args.video, args.output, v2_results, v3_results,
        v2_metrics, v3_metrics, args.panel_width,
    )
    report = {
        "source_video": str(args.video.resolve()),
        "output_video": str(args.output.resolve()),
        "confidence": args.confidence,
        "iou_threshold": args.iou,
        "warmup_iterations": args.warmup,
        "v2": v2_metrics,
        "v3": v3_metrics,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
