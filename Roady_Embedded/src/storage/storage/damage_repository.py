from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence

import cv2
import numpy as np


@dataclass(frozen=True)
class DamageLocation:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class DamageEvent:
    event_id: str
    robot_id: int
    description: str
    latitude: float
    longitude: float
    captured_at: str
    image_paths: tuple[str, ...]
    metadata: dict[str, Any] | None = None
    upload_image_paths: Optional[tuple[str, ...]] = None


class DamageRepository:
    """Stores each captured image and its pending robot event on disk."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.image_dir = self.base_dir / "images"
        self.pending_dir = self.base_dir / "pending"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def save_event(
        self,
        images: Sequence[np.ndarray],
        location: DamageLocation,
        robot_id: int = 1,
        description: str = "도로 균열 감지",
        captured_at: Optional[datetime] = None,
        metadata: dict[str, Any] | None = None,
        upload_image_indices: Optional[Sequence[int]] = None,
    ) -> DamageEvent:
        if not 1 <= len(images) <= 3:
            raise ValueError("an event must contain between 1 and 3 images")
        if any(image is None or image.size == 0 for image in images):
            raise ValueError("event images must not be empty")
        if robot_id < 1:
            raise ValueError("robot_id must be a positive integer")
        if not description.strip():
            raise ValueError("description must not be blank")
        if not -90.0 <= location.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if not -180.0 <= location.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        if upload_image_indices is not None:
            if not upload_image_indices:
                raise ValueError("at least one upload image must be selected")
            if len(set(upload_image_indices)) != len(upload_image_indices):
                raise ValueError("upload image indices must be unique")
            if any(index < 0 or index >= len(images) for index in upload_image_indices):
                raise ValueError("upload image index is out of range")

        now = captured_at or datetime.now().astimezone()
        if now.tzinfo is None:
            now = now.astimezone()
        event_id = self._make_event_id(now)
        event_path = self.pending_dir / f"{event_id}.json"

        image_paths = [
            self.image_dir / f"{event_id}_{index:02d}.jpg"
            for index in range(1, len(images) + 1)
        ]
        for image, image_path in zip(images, image_paths):
            if not cv2.imwrite(str(image_path), image):
                self._remove_files(image_paths)
                raise RuntimeError(f"Failed to write damage image: {image_path}")

        event = DamageEvent(
            event_id=event_id,
            robot_id=robot_id,
            description=description,
            latitude=location.latitude,
            longitude=location.longitude,
            captured_at=now.replace(tzinfo=None).isoformat(timespec="seconds"),
            image_paths=tuple(path.name for path in image_paths),
            metadata=metadata,
            upload_image_paths=(
                tuple(image_paths[index].name for index in upload_image_indices)
                if upload_image_indices is not None
                else None
            ),
        )
        try:
            self._write_json_atomically(event_path, self.to_dict(event))
        except Exception:
            self._remove_files(image_paths)
            raise
        return event

    def list_pending_events(self) -> list[Path]:
        return sorted(self.pending_dir.glob("*.json"))

    @staticmethod
    def load_event_file(event_path: str | Path) -> dict:
        with Path(event_path).open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def resolve_image_paths(self, event: dict) -> list[Path]:
        return [self._resolve_image_name(name) for name in event.get("images", [])]

    def resolve_upload_image_paths(self, event: dict) -> list[Path]:
        # Production events store [representative original, expanded ROI].
        # Upload only the first image so queued events created under an older
        # upload policy also send the original camera frame rather than the ROI.
        image_paths = self.resolve_image_paths(event)
        return image_paths[:1]

    def delete_event(self, event_path: str | Path) -> None:
        path = Path(event_path)
        if path.parent.resolve() != self.pending_dir.resolve():
            raise ValueError("event file must be inside the pending directory")

        event = self.load_event_file(path)
        if event.get("eventId") != path.stem:
            raise ValueError("eventId does not match the event filename")

        self._remove_files(self.resolve_image_paths(event))
        path.unlink(missing_ok=True)

    @staticmethod
    def to_dict(event: DamageEvent) -> dict:
        payload = {
            "eventId": event.event_id,
            "robotId": event.robot_id,
            "description": event.description,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "capturedAt": event.captured_at,
            "images": list(event.image_paths),
        }
        if event.metadata is not None:
            payload["metadata"] = event.metadata
        if event.upload_image_paths is not None:
            payload["uploadImages"] = list(event.upload_image_paths)
        return payload

    @staticmethod
    def to_json(event: DamageEvent) -> str:
        return json.dumps(DamageRepository.to_dict(event), ensure_ascii=False)

    @staticmethod
    def _make_event_id(captured_at: datetime) -> str:
        stamp = captured_at.strftime("%Y%m%dT%H%M%S%f")
        suffix = uuid.uuid4().hex[:8]
        return f"damage_{stamp}_{suffix}"

    @staticmethod
    def _write_json_atomically(path: Path, payload: dict) -> None:
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        with temporary_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
            fp.flush()
            os.fsync(fp.fileno())
        temporary_path.replace(path)

    @staticmethod
    def _remove_files(paths: Sequence[Path]) -> None:
        for path in paths:
            path.unlink(missing_ok=True)

    def _resolve_image_name(self, image_name: str) -> Path:
        name = Path(image_name)
        if name.name != image_name:
            raise ValueError(f"invalid image filename: {image_name}")
        return self.image_dir / name
