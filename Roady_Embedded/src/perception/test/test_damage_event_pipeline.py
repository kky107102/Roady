import numpy as np

from perception.algorithms.damage_detector import DamageDetection, MockDamageDetector
from perception.algorithms.damage_event_pipeline import (
    DamageEventPipeline,
    RoiSelection,
    assess_frame_quality,
    select_analysis_roi,
)


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


def test_selects_single_tactile_bbox_related_to_damage():
    selection = select_analysis_roi(
        damage_bbox=(120, 120, 160, 160),
        tactile_boxes=[(100, 100, 200, 200), (300, 300, 400, 400)],
        frame_shape=(480, 640, 3),
        tactile_margin_ratio=0.20,
    )

    assert selection.roi_source == "tactile_block"
    assert selection.tactile_detection_count == 1
    assert selection.bbox == (80.0, 80.0, 220.0, 220.0)
    assert not selection.roi_fallback_used


def test_related_tactile_boxes_are_merged_before_margin():
    selection = select_analysis_roi(
        damage_bbox=(180, 120, 240, 180),
        tactile_boxes=[(100, 100, 200, 200), (190, 100, 290, 200)],
        frame_shape=(480, 640, 3),
        tactile_margin_ratio=0.20,
    )

    assert selection.tactile_detection_count == 2
    assert selection.bbox == (62.0, 80.0, 328.0, 220.0)
    assert selection.analysis_unit_hint == "block_or_block_group"


def test_tactile_margin_is_clipped_to_image_boundary():
    selection = select_analysis_roi(
        damage_bbox=(5, 5, 25, 25),
        tactile_boxes=[(0, 0, 50, 50)],
        frame_shape=(100, 100, 3),
        tactile_margin_ratio=0.20,
    )

    assert selection.bbox == (0.0, 0.0, 60.0, 60.0)


def test_damage_bbox_fallback_includes_explicit_metadata():
    selection = select_analysis_roi(
        damage_bbox=(100, 100, 200, 200),
        tactile_boxes=[],
        frame_shape=(480, 640, 3),
        fallback_scale=1.5,
    )

    assert selection.bbox == (75.0, 75.0, 225.0, 225.0)
    assert selection.metadata() == {
        "roi_source": "damage_fallback",
        "analysis_unit_hint": "unknown",
        "tactile_detection_count": 0,
        "roi_fallback_used": True,
    }


def test_frame_quality_gate_distinguishes_verified_and_fallback_roi():
    rng = np.random.default_rng(42)
    frame = rng.integers(0, 256, (480, 640, 3), dtype=np.uint8)
    tactile = RoiSelection(
        bbox=(100, 100, 300, 300),
        roi_source="tactile_block",
        analysis_unit_hint="block_or_block_group",
        tactile_detection_count=1,
        roi_fallback_used=False,
    )
    common = dict(
        frame=frame,
        damage_bbox=(150, 150, 200, 200),
        confidence=0.8,
        previous_center=(200, 200),
        previous_area=40_000,
        frame_edge_margin_px=3,
        minimum_roi_width_px=32,
        minimum_roi_height_px=32,
        minimum_roi_area_px=1024,
        minimum_sharpness=10.0,
        stable_area_change_ratio=0.10,
        stable_center_shift_ratio=0.03,
    )

    passed = assess_frame_quality(roi_selection=tactile, **common)
    fallback = assess_frame_quality(
        roi_selection=RoiSelection(
            bbox=tactile.bbox,
            roi_source="damage_fallback",
            analysis_unit_hint="unknown",
            tactile_detection_count=0,
            roi_fallback_used=True,
        ),
        **common,
    )

    assert passed.hard_gate_passed
    assert passed.stable
    assert not fallback.hard_gate_passed
    assert "TACTILE_RELATION_UNAVAILABLE" in fallback.rejection_reasons


def test_pipeline_uses_tactile_roi_and_records_quality_metadata():
    rng = np.random.default_rng(7)
    frame = rng.integers(0, 256, (480, 640, 3), dtype=np.uint8)
    detector = MockDamageDetector(
        [
            detection("tactile_block", 0.9, (100, 100, 300, 300)),
            detection("damage_candidate", 0.8, (150, 150, 200, 200)),
        ]
    )
    pipeline = DamageEventPipeline(
        detector=detector,
        confirm_count=2,
        min_confirm_duration_sec=0.1,
        stable_observation_count=1,
        candidate_timeout_sec=0.5,
    )
    pipeline.process(frame, timestamp=0.0)
    pipeline.process(frame, timestamp=0.2)
    detector.detections = []
    ready = pipeline.process(frame, timestamp=0.71)

    assert len(ready) == 1
    assert ready[0].metadata["roi_source"] == "tactile_block"
    assert ready[0].metadata["analysis_unit_hint"] == "block_or_block_group"
    assert ready[0].metadata["frame_quality_verified"] is True
    assert ready[0].analysis_roi.shape[:2] == (280, 280)
    assert np.array_equal(ready[0].tactile_roi, ready[0].analysis_roi)
