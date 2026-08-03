from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class LowerLimbDetection:
    class_id: int
    label: str
    confidence: float
    xyxy: tuple[float, float, float, float]


class LowerLimbDetector:
    """Small Ultralytics adapter shared by PyTorch and TensorRT models."""

    def __init__(
        self,
        model_path: str | Path,
        confidence: float = 0.25,
        image_size: int = 640,
        device: str = "0",
    ) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is required: pip install -r ROADY_AI/requirements.txt"
            ) from exc

        path = Path(model_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        self._model = YOLO(str(path), task="detect")
        self._confidence = confidence
        self._image_size = image_size
        self._device = device

    def detect(self, image: np.ndarray) -> tuple[list[LowerLimbDetection], Any]:
        if image is None or image.size == 0:
            raise ValueError("image is empty")

        result = self._model.predict(
            source=image,
            imgsz=self._image_size,
            conf=self._confidence,
            device=self._device,
            verbose=False,
        )[0]
        detections: list[LowerLimbDetection] = []
        if result.boxes is None:
            return detections, result

        names = result.names
        for box in result.boxes:
            class_id = int(box.cls.item())
            coordinates = box.xyxy[0].tolist()
            detections.append(
                LowerLimbDetection(
                    class_id=class_id,
                    label=str(names[class_id]),
                    confidence=float(box.conf.item()),
                    xyxy=tuple(float(value) for value in coordinates),
                )
            )
        return detections, result
