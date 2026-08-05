from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from perception.algorithms.damage_detector import DamageDetection
from perception.algorithms.lower_limb_detector import LowerLimbDetector


class PersonAsTactileDetector:
    """Test-only adapter mapping foot/lower-leg boxes to damage candidates."""

    def __init__(
        self,
        model_path: str | Path,
        confidence: float = 0.15,
        image_size: int = 640,
        device: str = "0",
    ) -> None:
        self._backend = LowerLimbDetector(
            model_path=model_path,
            confidence=confidence,
            image_size=image_size,
            device=device,
        )
        self.last_detections: tuple[DamageDetection, ...] = ()

    def detect(self, image: np.ndarray) -> tuple[list[DamageDetection], Any]:
        detections, raw = self._backend.detect(image)
        height, width = image.shape[:2]
        mapped = [
            DamageDetection(
                class_id=1,
                label="damage_candidate",
                confidence=detection.confidence,
                xyxy=_expand_bbox(detection.xyxy, width, height, scale=1.8),
            )
            for detection in detections
            if detection.label in {"foot", "lower_leg"}
        ]
        self.last_detections = tuple(mapped)
        return mapped, raw

    def close(self) -> None:
        self._backend.close()


def _expand_bbox(
    bbox: tuple[float, float, float, float],
    image_width: int,
    image_height: int,
    scale: float,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0
    expanded_width = (x2 - x1) * scale
    expanded_height = (y2 - y1) * scale
    return (
        max(0.0, center_x - expanded_width / 2.0),
        max(0.0, center_y - expanded_height / 2.0),
        min(float(image_width), center_x + expanded_width / 2.0),
        min(float(image_height), center_y + expanded_height / 2.0),
    )
