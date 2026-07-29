from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DamageDetection:
    label: str
    confidence: float


class MockDamageDetector:
    """Temporary detector used until the real damage model is integrated."""

    def __init__(self, confidence: float = 1.0):
        self.confidence = confidence

    def detect(self, image: np.ndarray) -> DamageDetection:
        if image is None or image.size == 0:
            raise ValueError("image is empty")
        return DamageDetection(label="mock_damage", confidence=self.confidence)
