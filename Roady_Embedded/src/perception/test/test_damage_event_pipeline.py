import numpy as np

from perception.algorithms.damage_classifier import MockDamageClassifier
from perception.algorithms.damage_detector import DamageDetection, MockDamageDetector
from perception.algorithms.damage_event_pipeline import (
    DamageEventPipeline,
    overlapping_tiles,
)


def detection(label, confidence, xyxy):
    return DamageDetection(
        class_id=0 if label == "tactile_block" else 1,
        label=label,
        confidence=confidence,
        xyxy=xyxy,
    )


def test_overlapping_tiles_cover_final_edges():
    roi = np.zeros((400, 700, 3), dtype=np.uint8)

    tiles = overlapping_tiles(roi, tile_size=320, overlap=0.30)
    boxes = [box for box, _ in tiles]

    assert any(box[2] == 700 for box in boxes)
    assert any(box[3] == 400 for box in boxes)
    assert all(tile.shape[:2] == (320, 320) for _, tile in tiles)


def test_detector_or_classifier_can_create_evidence():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [detection("tactile_block", 0.9, (100, 100, 420, 420))]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        classifier=MockDamageClassifier(damage_score=0.8),
        confirm_count=1,
    )

    assert pipeline.process(frame, timestamp=0.0, location=(37.5, 127.0)) == []
    ready = pipeline.flush(timestamp=0.1)

    assert len(ready) == 1
    assert ready[0].best_score >= 0.8
    assert ready[0].original_image.shape == frame.shape
    assert ready[0].tactile_roi.size > 0
    assert ready[0].location == (37.5, 127.0)


def test_same_candidate_requires_three_frames_then_emits_once():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [detection("damage_candidate", 0.7, (200, 200, 320, 320))]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        classifier=MockDamageClassifier(),
        confirm_count=3,
        confirm_window_sec=2.0,
        candidate_timeout_sec=1.0,
    )

    assert pipeline.process(frame, timestamp=0.0) == []
    assert pipeline.process(frame, timestamp=0.4) == []
    assert pipeline.process(frame, timestamp=0.8) == []

    detector.detections = []
    assert pipeline.process(frame, timestamp=1.7) == []
    ready = pipeline.process(frame, timestamp=1.8)

    assert len(ready) == 1
    assert ready[0].observation_count == 3
    assert pipeline.process(frame, timestamp=3.5) == []
    pipeline.acknowledge(ready[0].candidate_id)
    assert pipeline.candidates == ()


def test_ready_candidate_can_retry_until_persisted():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [detection("damage_candidate", 0.7, (200, 200, 320, 320))]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        classifier=MockDamageClassifier(),
        confirm_count=1,
        candidate_timeout_sec=0.5,
    )
    pipeline.process(frame, timestamp=0.0)
    detector.detections = []

    first = pipeline.process(frame, timestamp=0.5)
    assert len(first) == 1
    pipeline.retry(first[0].candidate_id)
    second = pipeline.process(frame, timestamp=0.6)

    assert len(second) == 1
    assert second[0].candidate_id == first[0].candidate_id


def test_detector_and_classifier_in_one_frame_count_once():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [
            detection("tactile_block", 0.9, (100, 100, 420, 420)),
            detection("damage_candidate", 0.8, (120, 120, 400, 400)),
        ]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        classifier=MockDamageClassifier(damage_score=0.8),
        confirm_count=2,
    )

    pipeline.process(frame, timestamp=0.0)

    assert len(pipeline.candidates) == 1
    assert len(pipeline.candidates[0].observation_times) == 1
    assert not pipeline.candidates[0].confirmed
