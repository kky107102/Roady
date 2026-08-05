from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from perception.algorithms.lower_limb_detector import LowerLimbDetector


@dataclass(frozen=True)
class DamageDetection:
    class_id: int
    label: str
    confidence: float
    xyxy: tuple[float, float, float, float]


class DamageDetector:
    """YOLO adapter for tactile-block and damage-candidate detection."""

    CLASS_NAMES = ("tactile_block", "damage_candidate")

    def __init__(
        self,
        model_path: str | Path,
        confidence: float = 0.15,
        image_size: int = 640,
        device: str = "0",
    ) -> None:
        self._detector = LowerLimbDetector(
            model_path=model_path,
            confidence=confidence,
            image_size=image_size,
            device=device,
            class_names=self.CLASS_NAMES,
        )

    def detect(self, image: np.ndarray) -> tuple[list[DamageDetection], Any]:
        detections, raw_result = self._detector.detect(image)
        return [
            DamageDetection(
                class_id=item.class_id,
                label=item.label,
                confidence=item.confidence,
                xyxy=item.xyxy,
            )
            for item in detections
            if item.label in self.CLASS_NAMES
        ], raw_result

    def close(self) -> None:
        self._detector.close()


class MockDamageDetector:
    """Deterministic test double with the same interface as DamageDetector."""

    def __init__(self, detections: list[DamageDetection] | None = None):
        self.detections = detections or []

    def detect(self, image: np.ndarray) -> tuple[list[DamageDetection], None]:
        if image is None or image.size == 0:
            raise ValueError("image is empty")
        return list(self.detections), None

    def close(self) -> None:
        return None
