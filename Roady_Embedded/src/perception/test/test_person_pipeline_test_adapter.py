import numpy as np
from perception.algorithms.lower_limb_detector import LowerLimbDetection
from perception.algorithms.person_pipeline_test_adapter import PersonAsTactileDetector


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


def test_lower_limb_detection_becomes_damage_candidate_for_pipeline():
    adapter = adapter_with([lower_limb("lower_leg", 0.77)])

    detections, _ = adapter.detect(np.zeros((200, 200, 3), dtype=np.uint8))

    assert len(detections) == 1
    assert detections[0].label == "damage_candidate"
    assert detections[0].confidence == 0.77
    assert detections[0].xyxy == (0.0, 0.0, 136.0, 200.0)


def test_non_lower_limb_detection_is_ignored():
    adapter = adapter_with([lower_limb("person", 0.68)])

    detections, _ = adapter.detect(np.zeros((100, 100, 3), dtype=np.uint8))

    assert detections == []
