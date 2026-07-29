from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


@dataclass(frozen=True)
class DamageLocation:
    latitude: float
    longitude: float
    sensor_offset_m: float = 0.0


@dataclass(frozen=True)
class DamageEvent:
    event_id: str
    captured_at: str
    location: DamageLocation
    image_path: str
    detector_name: str
    confidence: float
    label: str = "mock_damage"


class DamageRepository:
    """Stores damage events as an image file plus a JSON sidecar."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.image_dir = self.base_dir / "images"
        self.event_dir = self.base_dir / "events"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.event_dir.mkdir(parents=True, exist_ok=True)

    def save_event(
        self,
        image: np.ndarray,
        location: DamageLocation,
        label: str = "mock_damage",
        detector_name: str = "mock_damage_detector",
        confidence: float = 1.0,
        captured_at: Optional[datetime] = None,
    ) -> DamageEvent:
        now = captured_at or datetime.now(timezone.utc)
        event_id = self._make_event_id(now)
        image_path = self.image_dir / f"{event_id}.jpg"
        event_path = self.event_dir / f"{event_id}.json"

        if not cv2.imwrite(str(image_path), image):
            raise RuntimeError(f"Failed to write damage image: {image_path}")

        event = DamageEvent(
            event_id=event_id,
            captured_at=now.isoformat(),
            location=location,
            image_path=str(image_path),
            detector_name=detector_name,
            confidence=confidence,
            label=label,
        )
        with event_path.open("w", encoding="utf-8") as fp:
            json.dump(self.to_dict(event), fp, ensure_ascii=False, indent=2)
        return event

    def list_event_files(self) -> list[Path]:
        return sorted(self.event_dir.glob("*.json"))

    @staticmethod
    def load_event_file(event_path: str | Path) -> dict:
        with Path(event_path).open("r", encoding="utf-8") as fp:
            return json.load(fp)

    @staticmethod
    def mark_uploaded(event_path: str | Path, uploaded_at: Optional[datetime] = None) -> None:
        path = Path(event_path)
        event = DamageRepository.load_event_file(path)
        event["uploaded"] = True
        event["uploadedAt"] = (uploaded_at or datetime.now(timezone.utc)).isoformat()
        with path.open("w", encoding="utf-8") as fp:
            json.dump(event, fp, ensure_ascii=False, indent=2)

    @staticmethod
    def to_dict(event: DamageEvent) -> dict:
        return asdict(event)

    @staticmethod
    def to_json(event: DamageEvent) -> str:
        return json.dumps(DamageRepository.to_dict(event), ensure_ascii=False)

    @staticmethod
    def _make_event_id(captured_at: datetime) -> str:
        stamp = captured_at.strftime("%Y%m%dT%H%M%S%fZ")
        suffix = uuid.uuid4().hex[:8]
        return f"damage_{stamp}_{suffix}"
