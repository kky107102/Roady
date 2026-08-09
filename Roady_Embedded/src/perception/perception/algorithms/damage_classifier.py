from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class DamageClassification:
    damage_score: float
    normal_score: float


class DamageClassifier:
    """YOLO classification adapter for a tactile-block ROI or tile."""

    def __init__(
        self,
        model_path: str | Path,
        image_size: int = 320,
        device: str = "0",
    ) -> None:
        path = Path(model_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is required for damage classification"
            ) from exc
        self._model = YOLO(str(path), task="classify")
        self._image_size = image_size
        self._device = device

    def classify(self, image: np.ndarray) -> DamageClassification:
        if image is None or image.size == 0:
            raise ValueError("image is empty")
        result = self._model.predict(
            source=image,
            imgsz=self._image_size,
            device=self._device,
            verbose=False,
        )[0]
        if result.probs is None:
            raise RuntimeError("classification model returned no probabilities")
        probabilities = result.probs.data.detach().cpu().tolist()
        by_name = {
            str(result.names[index]): float(score)
            for index, score in enumerate(probabilities)
        }
        if "damage_suspected" not in by_name or "normal" not in by_name:
            raise RuntimeError(f"unexpected classifier classes: {sorted(by_name)}")
        return DamageClassification(
            damage_score=by_name["damage_suspected"],
            normal_score=by_name["normal"],
        )

    def close(self) -> None:
        return None


class MockDamageClassifier:
    """Deterministic test double with the same interface as DamageClassifier."""

    def __init__(self, damage_score: float = 0.0):
        self.damage_score = float(damage_score)

    def classify(self, image: np.ndarray) -> DamageClassification:
        if image is None or image.size == 0:
            raise ValueError("image is empty")
        return DamageClassification(
            damage_score=self.damage_score,
            normal_score=1.0 - self.damage_score,
        )

    def close(self) -> None:
        return None
