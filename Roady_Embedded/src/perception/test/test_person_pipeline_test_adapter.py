import numpy as np
import pytest

from perception.algorithms.lower_limb_detector import LowerLimbDetection
from perception.algorithms.person_pipeline_test_adapter import (
    PersonAsTactileDetector,
    PersonRoiClassifier,
)


class FakeLowerLimbBackend:
    def __init__(self, detections):
        self.detections = detections

    def detect(self, _image):
        return self.detections, None

    def close(self):
        return None


def lower_limb(label, confidence=0.8):
    return LowerLimbDetection(
        class_id=0,
        label=label,
        confidence=confidence,
        xyxy=(10.0, 20.0, 100.0, 160.0),
    )


def adapter_with(detections):
    adapter = PersonAsTactileDetector.__new__(PersonAsTactileDetector)
    adapter._backend = FakeLowerLimbBackend(detections)
    return adapter


def test_lower_limb_detection_becomes_tactile_roi_for_pipeline():
    adapter = adapter_with([lower_limb("lower_leg", 0.77)])

    detections, _ = adapter.detect(np.zeros((200, 200, 3), dtype=np.uint8))

    assert len(detections) == 1
    assert detections[0].label == "tactile_block"
    assert detections[0].confidence == 0.77
    assert detections[0].xyxy == (0.0, 0.0, 136.0, 200.0)


def test_second_stage_uses_person_confidence_as_classification_score():
    adapter = adapter_with([lower_limb("foot", 0.68)])
    classifier = PersonRoiClassifier(adapter)

    result = classifier.classify(np.zeros((100, 100, 3), dtype=np.uint8))

    assert result.damage_score == 0.68
    assert result.normal_score == pytest.approx(0.32)


def test_second_stage_is_negative_when_crop_has_no_lower_limb():
    adapter = adapter_with([])

    result = PersonRoiClassifier(adapter).classify(
        np.zeros((100, 100, 3), dtype=np.uint8)
    )

    assert result.damage_score == 0.0
    assert result.normal_score == 1.0
