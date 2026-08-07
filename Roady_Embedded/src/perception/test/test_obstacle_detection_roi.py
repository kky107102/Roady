import numpy as np
import pytest

from perception.algorithms.lower_limb_detector import LowerLimbDetection
from perception.nodes.obstacle_detection_node import (
    crop_ratio_roi,
    offset_detections,
    split_near_field,
    validate_roi_ratios,
)


def _detection(y1: float, y2: float) -> LowerLimbDetection:
    return LowerLimbDetection(
        class_id=0, label="foot", confidence=0.8, xyxy=(400.0, y1, 500.0, y2)
    )


def test_central_roi_uses_expected_pixels():
    image = np.zeros((720, 1280, 3), dtype=np.uint8)

    roi, bounds = crop_ratio_roi(image, (0.25, 0.20, 0.75, 1.0))

    assert bounds == (320, 144, 960, 720)
    assert roi.shape == (576, 640, 3)


def test_roi_detection_coordinates_are_restored_to_full_image():
    detection = LowerLimbDetection(
        class_id=0,
        label="foot",
        confidence=0.8,
        xyxy=(10.0, 20.0, 110.0, 220.0),
    )

    shifted = offset_detections([detection], 320, 144)

    assert shifted[0].xyxy == (330.0, 164.0, 430.0, 364.0)


def test_invalid_roi_is_rejected():
    with pytest.raises(ValueError):
        validate_roi_ratios((0.75, 0.2, 0.25, 1.0))


def test_disabled_gates_keep_every_detection():
    far = _detection(100.0, 200.0)

    near, rejected = split_near_field([far], 720, 0.0, 0.0)

    assert near == [far]
    assert rejected == []


def test_ground_gate_rejects_boxes_ending_above_the_line():
    close = _detection(400.0, 700.0)
    distant = _detection(300.0, 420.0)

    near, rejected = split_near_field([close, distant], 720, 0.65, 0.0)

    assert near == [close]
    assert rejected == [distant]


def test_ground_gate_alone_does_not_admit_every_box_via_height():
    """A disabled height gate must not act as an always-true OR term."""
    distant = _detection(300.0, 420.0)

    near, rejected = split_near_field([distant], 720, 0.65, 0.0)

    assert near == []
    assert rejected == [distant]


def test_tall_box_survives_when_ground_contact_is_occluded():
    tall_but_high = _detection(100.0, 430.0)

    near, rejected = split_near_field([tall_but_high], 720, 0.65, 0.4)

    assert near == [tall_but_high]
    assert rejected == []
