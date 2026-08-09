from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from perception.algorithms.damage_detector import DamageDetection, MockDamageDetector
from perception.algorithms.damage_event_pipeline import DamageEventPipeline


def box(label: str, confidence: float, xyxy) -> DamageDetection:
    return DamageDetection(
        class_id=0 if label == "tactile_block" else 1,
        label=label,
        confidence=confidence,
        xyxy=tuple(float(value) for value in xyxy),
    )


def draw_frame(frame, detections, candidates, title):
    annotated = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = (int(value) for value in detection.xyxy)
        color = (255, 140, 0) if detection.label == "tactile_block" else (0, 0, 255)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)
        cv2.putText(
            annotated,
            f"MOCK {detection.label} {detection.confidence:.2f}",
            (x1, max(28, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            color,
            2,
        )
    for candidate in candidates:
        x1, y1, x2, y2 = (int(value) for value in candidate.last_bbox)
        status = "READY" if candidate.ready_emitted else (
            "CONFIRMED" if candidate.confirmed else "TRACKING"
        )
        color = (255, 0, 255) if status == "READY" else (
            (0, 200, 0) if status == "CONFIRMED" else (0, 165, 255)
        )
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 5)
        cv2.putText(
            annotated,
            f"ID {candidate.candidate_id} {status} obs={len(candidate.observation_times)}",
            (x1, min(annotated.shape[0] - 12, y2 + 28)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
        )
    cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 55), (0, 0, 0), -1)
    cv2.putText(
        annotated,
        title,
        (18, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )
    return annotated


def main() -> None:
    parser = argparse.ArgumentParser(description="Visual mock of the damage event pipeline")
    parser.add_argument(
        "--image",
        type=Path,
        default=Path(
            "/home/ssafy/roady_dataset/obstacle_lower_limb/"
            "obstacle_20260804_184738_337692.jpg"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/damage_mock_visual"),
    )
    args = parser.parse_args()
    frame = cv2.imread(str(args.image.expanduser().resolve()))
    if frame is None:
        raise FileNotFoundError(args.image)
    args.output.mkdir(parents=True, exist_ok=True)

    detector = MockDamageDetector()
    pipeline = DamageEventPipeline(
        detector=detector,
        confirm_count=3,
        confirm_window_sec=2.0,
        candidate_timeout_sec=1.0,
    )
    tactile = box("tactile_block", 0.91, (45, 20, 1270, 710))
    damage_sequence = [
        box("damage_candidate", 0.54, (555, 180, 760, 315)),
        box("damage_candidate", 0.67, (610, 235, 865, 405)),
        box("damage_candidate", 0.82, (675, 300, 995, 525)),
    ]
    timestamps = [0.0, 0.4, 0.8]
    outputs = []
    for index, (damage, timestamp) in enumerate(zip(damage_sequence, timestamps), 1):
        detector.detections = [tactile, damage]
        pipeline.process(
            frame,
            timestamp=timestamp,
            location=(37.5012748, 127.039625 + index * 0.0001),
        )
        status = "CONFIRMED" if pipeline.candidates[0].confirmed else "TRACKING"
        path = args.output / f"frame_{index:02d}_{status.lower()}.jpg"
        cv2.imwrite(
            str(path),
            draw_frame(
                frame,
                detector.detections,
                pipeline.candidates,
                f"FRAME {index}: candidate {status}",
            ),
        )
        outputs.append(str(path))

    detector.detections = []
    ready = pipeline.process(frame, timestamp=2.0)
    if len(ready) != 1:
        raise RuntimeError(f"expected one ready event, got {len(ready)}")
    ready_frame = args.output / "frame_04_ready.jpg"
    cv2.imwrite(
        str(ready_frame),
        draw_frame(frame, [], pipeline.candidates, "FRAME 4: event READY after timeout"),
    )
    outputs.append(str(ready_frame))

    event = ready[0]
    original_path = args.output / "event_representative_original.jpg"
    roi_path = args.output / "event_representative_roi.jpg"
    cv2.imwrite(str(original_path), event.original_image)
    cv2.imwrite(str(roi_path), event.tactile_roi)
    summary = {
        "candidate_id": event.candidate_id,
        "observation_count": event.observation_count,
        "best_score": event.best_score,
        "location": event.location,
        "visual_frames": outputs,
        "representative_original": str(original_path),
        "representative_roi": str(roi_path),
    }
    summary_path = args.output / "event_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    pipeline.acknowledge(event.candidate_id)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
