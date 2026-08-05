import numpy as np

from perception.algorithms.damage_detector import DamageDetection, MockDamageDetector
from perception.algorithms.damage_event_pipeline import DamageEventPipeline


def detection(label, confidence, xyxy):
    return DamageDetection(
        class_id=0 if label == "tactile_block" else 1,
        label=label,
        confidence=confidence,
        xyxy=xyxy,
    )


def test_tactile_block_alone_does_not_create_evidence():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [detection("tactile_block", 0.9, (100, 100, 420, 420))]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        confirm_count=1,
    )

    assert pipeline.process(frame, timestamp=0.0, location=(37.5, 127.0)) == []
    ready = pipeline.flush(timestamp=0.1)

    assert ready == []


def test_same_candidate_requires_three_frames_then_emits_once():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [detection("damage_candidate", 0.7, (200, 200, 320, 320))]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
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
    assert pipeline.candidates[0].reported
    assert pipeline.process(frame, timestamp=6.0) == []
    assert pipeline.candidates == ()


def test_ready_candidate_can_retry_until_persisted():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [detection("damage_candidate", 0.7, (200, 200, 320, 320))]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        confirm_count=1,
        min_confirm_duration_sec=0.0,
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


def test_overlapping_damage_detections_in_one_frame_count_once():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [
            detection("damage_candidate", 0.9, (100, 100, 420, 420)),
            detection("damage_candidate", 0.8, (120, 120, 400, 400)),
        ]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        confirm_count=2,
    )

    pipeline.process(frame, timestamp=0.0)

    assert len(pipeline.candidates) == 1
    assert len(pipeline.candidates[0].observation_times) == 1
    assert not pipeline.candidates[0].confirmed


def test_three_rapid_frames_do_not_confirm_before_minimum_duration():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [detection("damage_candidate", 0.7, (200, 200, 320, 320))]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        confirm_count=3,
        min_confirm_duration_sec=0.4,
        min_observation_interval_sec=0.1,
    )

    pipeline.process(frame, timestamp=0.0)
    pipeline.process(frame, timestamp=0.1)
    pipeline.process(frame, timestamp=0.2)

    assert not pipeline.candidates[0].confirmed

    pipeline.process(frame, timestamp=0.4)

    assert pipeline.candidates[0].confirmed


def test_reported_track_suppresses_repeated_event_during_cooldown():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [detection("damage_candidate", 0.7, (200, 200, 320, 320))]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        confirm_count=1,
        min_confirm_duration_sec=0.0,
        candidate_timeout_sec=0.5,
        reported_track_cooldown_sec=5.0,
    )
    pipeline.process(frame, timestamp=0.0)
    detector.detections = []
    ready = pipeline.process(frame, timestamp=0.5)
    pipeline.acknowledge(ready[0].candidate_id)

    detector.detections = [
        detection("damage_candidate", 0.8, (202, 202, 322, 322))
    ]
    assert pipeline.process(frame, timestamp=1.0) == []

    detector.detections = []
    assert pipeline.process(frame, timestamp=5.9) == []
    assert len(pipeline.candidates) == 1
    assert pipeline.candidates[0].reported
    assert pipeline.process(frame, timestamp=6.0) == []
    assert pipeline.candidates == ()
