"""Compare frame-level damage events with the tracked event pipeline on videos."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-dir", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--every", type=int, default=2)
    parser.add_argument("--image-size", type=int, default=768)
    parser.add_argument("--confirm-count", type=int, default=3)
    parser.add_argument("--stable-observation-count", type=int, default=2)
    parser.add_argument("--event-images", type=Path)
    parser.add_argument("--videos", nargs="*")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    perception_src = Path(__file__).resolve().parents[1] / "src" / "perception"
    sys.path.insert(0, str(perception_src))
    from perception.algorithms.damage_detector import DamageDetector
    from perception.algorithms.damage_event_pipeline import DamageEventPipeline

    names = args.videos or [path.name for path in sorted(args.video_dir.glob("*.mp4"))]
    detector = DamageDetector(
        args.model, confidence=0.225, image_size=args.image_size, device="cpu"
    )
    results = []
    started = time.perf_counter()
    for name in names:
        path = args.video_dir / name
        capture = cv2.VideoCapture(str(path))
        fps = capture.get(cv2.CAP_PROP_FPS)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        pipeline = DamageEventPipeline(
            detector=detector,
            detection_threshold=0.225,
            confirm_count=args.confirm_count,
            confirm_window_sec=2.0,
            min_confirm_duration_sec=0.2,
            min_observation_interval_sec=0.1,
            candidate_timeout_sec=1.2,
            reported_track_cooldown_sec=10.0,
            minimum_event_confidence=0.375,
            group_by_tactile_unit=True,
            stable_observation_count=args.stable_observation_count,
        )
        processed = damage_boxes = damage_frames = tactile_frames = event_count = 0
        damage_detected_timestamps_sec = []
        observations_per_event = []
        tracked_event_details = []
        index = -1
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            index += 1
            if index % args.every:
                continue
            processed += 1
            timestamp = index / fps
            ready = pipeline.process(frame, timestamp)
            detections = pipeline.last_detections
            count = sum(item.label == "damage_candidate" for item in detections)
            damage_boxes += count
            damage_frames += int(count > 0)
            if count > 0:
                damage_detected_timestamps_sec.append(timestamp)
            tactile_frames += int(any(item.label == "tactile_block" for item in detections))
            for event in ready:
                candidate = next(
                    item for item in pipeline.candidates
                    if item.candidate_id == event.candidate_id
                )
                event_count += 1
                observations_per_event.append(event.observation_count)
                detail = {
                    "candidate_id": event.candidate_id,
                    "first_seen_sec": candidate.first_seen_at,
                    "last_seen_sec": candidate.last_seen_at,
                    "emitted_sec": timestamp,
                    "observation_count": event.observation_count,
                    "best_score": event.best_score,
                }
                tracked_event_details.append(detail)
                if args.event_images:
                    target = args.event_images / path.stem
                    target.mkdir(parents=True, exist_ok=True)
                    cv2.imwrite(
                        str(target / f"event_{event_count:02d}_{candidate.last_seen_at:.2f}s.jpg"),
                        event.original_image,
                    )
                pipeline.acknowledge(event.candidate_id)
        for event in pipeline.flush(total_frames / fps + 2.0):
            candidate = next(
                item for item in pipeline.candidates
                if item.candidate_id == event.candidate_id
            )
            event_count += 1
            observations_per_event.append(event.observation_count)
            tracked_event_details.append(
                {
                    "candidate_id": event.candidate_id,
                    "first_seen_sec": candidate.first_seen_at,
                    "last_seen_sec": candidate.last_seen_at,
                    "emitted_sec": total_frames / fps + 2.0,
                    "observation_count": event.observation_count,
                    "best_score": event.best_score,
                }
            )
            if args.event_images:
                target = args.event_images / path.stem
                target.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(
                    str(target / f"event_{event_count:02d}_{candidate.last_seen_at:.2f}s.jpg"),
                    event.original_image,
                )
            pipeline.acknowledge(event.candidate_id)
        capture.release()
        results.append(
            {
                "video": name,
                "duration_sec": total_frames / fps,
                "fps": fps,
                "total_frames": total_frames,
                "processed_frames": processed,
                "damage_detection_boxes": damage_boxes,
                "damage_detected_frames": damage_frames,
                "damage_detected_timestamps_sec": damage_detected_timestamps_sec,
                "tactile_detected_frames": tactile_frames,
                "naive_frame_events": damage_frames,
                "tracked_events": event_count,
                "duplicate_reduction_pct": (
                    100.0 * (damage_frames - event_count) / damage_frames
                    if damage_frames
                    else None
                ),
                "observations_per_tracked_event": observations_per_event,
                "tracked_event_details": tracked_event_details,
            }
        )
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    detector.close()
    totals = {
        "duration_sec": sum(row["duration_sec"] for row in results),
        "processed_frames": sum(row["processed_frames"] for row in results),
        "damage_detection_boxes": sum(row["damage_detection_boxes"] for row in results),
        "damage_detected_frames": sum(row["damage_detected_frames"] for row in results),
        "naive_frame_events": sum(row["naive_frame_events"] for row in results),
        "tracked_events": sum(row["tracked_events"] for row in results),
    }
    baseline = totals["naive_frame_events"]
    totals["duplicate_reduction_pct"] = (
        100.0 * (baseline - totals["tracked_events"]) / baseline if baseline else None
    )
    report = {
        "method": {
            "model": str(args.model.resolve()),
            "process_every_n_frames": args.every,
            "image_size": args.image_size,
            "baseline": "one event per processed frame containing >=1 damage_candidate",
            "operating_speed_mps": 0.10,
            "detection_threshold": 0.225,
            "confirm_count": args.confirm_count,
            "confirm_window_sec": 2.0,
            "min_confirm_duration_sec": 0.2,
            "min_observation_interval_sec": 0.1,
            "candidate_timeout_sec": 1.2,
            "reported_track_cooldown_sec": 10.0,
            "minimum_event_confidence": 0.375,
            "stable_observation_count": args.stable_observation_count,
            "group_by_tactile_unit": True,
            "improved": "DamageEventPipeline deployment parameters from bringup launch",
        },
        "videos": results,
        "totals": totals,
        "wall_time_sec": time.perf_counter() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
