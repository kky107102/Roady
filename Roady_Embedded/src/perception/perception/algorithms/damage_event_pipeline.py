from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Protocol

import cv2
import numpy as np

from perception.algorithms.damage_classifier import DamageClassification
from perception.algorithms.damage_detector import DamageDetection


BBox = tuple[float, float, float, float]


class Detector(Protocol):
    def detect(self, image: np.ndarray): ...


class Classifier(Protocol):
    def classify(self, image: np.ndarray) -> DamageClassification: ...


@dataclass(frozen=True)
class DamageEvidence:
    bbox: BBox
    score: float
    sources: frozenset[str]


@dataclass
class DamageCandidate:
    candidate_id: int
    first_seen_at: float
    last_seen_at: float
    last_bbox: BBox
    observation_times: deque[float] = field(default_factory=deque)
    best_score: float = 0.0
    best_quality: float = -1.0
    best_original: np.ndarray | None = None
    best_roi: np.ndarray | None = None
    best_location: tuple[float, float] | None = None
    confirmed: bool = False
    ready_emitted: bool = False


@dataclass(frozen=True)
class ReadyDamageEvent:
    candidate_id: int
    original_image: np.ndarray
    tactile_roi: np.ndarray
    observation_count: int
    best_score: float
    location: tuple[float, float] | None


class DamageEventPipeline:
    """Combines detect/classify evidence and emits one representative event.

    Matching is image-coordinate based for now. A ground/world-coordinate matcher
    can replace ``_match_candidate`` when odometry and camera calibration arrive.
    """

    def __init__(
        self,
        detector: Detector,
        classifier: Classifier | None = None,
        detection_threshold: float = 0.15,
        classification_threshold: float = 0.275,
        confirm_count: int = 3,
        confirm_window_sec: float = 2.0,
        candidate_timeout_sec: float = 1.0,
        tile_size: int = 320,
        tile_overlap: float = 0.30,
        match_center_ratio: float = 0.20,
    ) -> None:
        if confirm_count < 1:
            raise ValueError("confirm_count must be positive")
        if not 0.0 <= tile_overlap < 1.0:
            raise ValueError("tile_overlap must be in [0, 1)")
        self.detector = detector
        self.classifier = classifier
        self.detection_threshold = detection_threshold
        self.classification_threshold = classification_threshold
        self.confirm_count = confirm_count
        self.confirm_window_sec = confirm_window_sec
        self.candidate_timeout_sec = candidate_timeout_sec
        self.tile_size = tile_size
        self.tile_overlap = tile_overlap
        self.match_center_ratio = match_center_ratio
        self._candidates: dict[int, DamageCandidate] = {}
        self._next_id = 1

    @property
    def candidates(self) -> tuple[DamageCandidate, ...]:
        return tuple(self._candidates.values())

    def process(
        self,
        frame: np.ndarray,
        timestamp: float,
        location: tuple[float, float] | None = None,
    ) -> list[ReadyDamageEvent]:
        if frame is None or frame.size == 0:
            raise ValueError("frame is empty")
        detections, _ = self.detector.detect(frame)
        evidence = self._collect_detector_evidence(detections)
        evidence.extend(self._collect_classifier_evidence(frame, detections))
        merged = self._merge_frame_evidence(evidence)

        for item in merged:
            candidate = self._match_candidate(item.bbox, frame.shape)
            if candidate is None:
                candidate = self._new_candidate(item, timestamp)
            self._observe(candidate, item, frame, timestamp, location)

        return self._finalize_expired(timestamp)

    def flush(self, timestamp: float) -> list[ReadyDamageEvent]:
        """Finalize confirmed tracks at shutdown or end of a recorded sequence."""
        return self._finalize_expired(timestamp, force=True)

    def acknowledge(self, candidate_id: int) -> None:
        """Remove a ready candidate only after its event is safely persisted."""
        candidate = self._candidates.get(candidate_id)
        if candidate is None or not candidate.ready_emitted:
            raise KeyError(f"candidate is not awaiting acknowledgement: {candidate_id}")
        del self._candidates[candidate_id]

    def retry(self, candidate_id: int) -> None:
        """Allow a failed persistence attempt to be emitted on the next frame."""
        candidate = self._candidates.get(candidate_id)
        if candidate is None or not candidate.ready_emitted:
            raise KeyError(f"candidate is not awaiting retry: {candidate_id}")
        candidate.ready_emitted = False

    def _collect_detector_evidence(
        self, detections: list[DamageDetection]
    ) -> list[DamageEvidence]:
        return [
            DamageEvidence(
                bbox=detection.xyxy,
                score=detection.confidence,
                sources=frozenset({"detector"}),
            )
            for detection in detections
            if detection.label == "damage_candidate"
            and detection.confidence >= self.detection_threshold
        ]

    def _collect_classifier_evidence(
        self,
        frame: np.ndarray,
        detections: list[DamageDetection],
    ) -> list[DamageEvidence]:
        if self.classifier is None:
            return []
        items: list[DamageEvidence] = []
        for detection in detections:
            if detection.label != "tactile_block":
                continue
            clipped = _clip_bbox(detection.xyxy, frame.shape[1], frame.shape[0])
            x1, y1, x2, y2 = (int(round(value)) for value in clipped)
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            for tile_bbox, tile in overlapping_tiles(
                roi, self.tile_size, self.tile_overlap
            ):
                classification = self.classifier.classify(tile)
                if classification.damage_score < self.classification_threshold:
                    continue
                tx1, ty1, tx2, ty2 = tile_bbox
                items.append(
                    DamageEvidence(
                        bbox=(x1 + tx1, y1 + ty1, x1 + tx2, y1 + ty2),
                        score=classification.damage_score,
                        sources=frozenset({"classifier"}),
                    )
                )
        return items

    def _merge_frame_evidence(
        self, evidence: list[DamageEvidence]
    ) -> list[DamageEvidence]:
        remaining = list(evidence)
        merged: list[DamageEvidence] = []
        while remaining:
            group = [remaining.pop(0)]
            changed = True
            while changed:
                changed = False
                group_box = _union_bbox([item.bbox for item in group])
                for item in list(remaining):
                    if _iou(group_box, item.bbox) > 0.05:
                        group.append(item)
                        remaining.remove(item)
                        changed = True
            combined_score = 1.0
            sources: set[str] = set()
            for item in group:
                combined_score *= 1.0 - item.score
                sources.update(item.sources)
            merged.append(
                DamageEvidence(
                    bbox=_union_bbox([item.bbox for item in group]),
                    score=1.0 - combined_score,
                    sources=frozenset(sources),
                )
            )
        return merged

    def _new_candidate(
        self, evidence: DamageEvidence, timestamp: float
    ) -> DamageCandidate:
        candidate = DamageCandidate(
            candidate_id=self._next_id,
            first_seen_at=timestamp,
            last_seen_at=timestamp,
            last_bbox=evidence.bbox,
        )
        self._candidates[candidate.candidate_id] = candidate
        self._next_id += 1
        return candidate

    def _match_candidate(
        self, bbox: BBox, frame_shape: tuple[int, ...]
    ) -> DamageCandidate | None:
        diagonal = float(np.hypot(frame_shape[1], frame_shape[0]))
        best: DamageCandidate | None = None
        best_cost = float("inf")
        for candidate in self._candidates.values():
            if candidate.ready_emitted:
                continue
            overlap = _iou(candidate.last_bbox, bbox)
            distance = _center_distance(candidate.last_bbox, bbox) / max(diagonal, 1.0)
            if overlap <= 0.01 and distance > self.match_center_ratio:
                continue
            cost = distance - overlap
            if cost < best_cost:
                best = candidate
                best_cost = cost
        return best

    def _observe(
        self,
        candidate: DamageCandidate,
        evidence: DamageEvidence,
        frame: np.ndarray,
        timestamp: float,
        location: tuple[float, float] | None,
    ) -> None:
        candidate.last_seen_at = timestamp
        candidate.last_bbox = evidence.bbox
        # Detector and classifier evidence from one processed frame must count
        # as one observation even if imperfect merging associates both here.
        if not candidate.observation_times or candidate.observation_times[-1] != timestamp:
            candidate.observation_times.append(timestamp)
        cutoff = timestamp - self.confirm_window_sec
        while candidate.observation_times and candidate.observation_times[0] < cutoff:
            candidate.observation_times.popleft()
        if len(candidate.observation_times) >= self.confirm_count:
            candidate.confirmed = True
        candidate.best_score = max(candidate.best_score, evidence.score)

        quality = image_quality(frame, evidence.bbox, evidence.score)
        if quality > candidate.best_quality:
            candidate.best_quality = quality
            candidate.best_original = frame.copy()
            candidate.best_roi = expanded_crop(frame, evidence.bbox, scale=1.5)
            candidate.best_location = location

    def _finalize_expired(
        self, timestamp: float, force: bool = False
    ) -> list[ReadyDamageEvent]:
        ready: list[ReadyDamageEvent] = []
        for candidate_id, candidate in self._candidates.items():
            expired = timestamp - candidate.last_seen_at >= self.candidate_timeout_sec
            if candidate.ready_emitted or (not force and not expired):
                continue
            if (
                not candidate.confirmed
                or candidate.best_original is None
                or candidate.best_roi is None
            ):
                if expired or force:
                    candidate.ready_emitted = True
                continue
            candidate.ready_emitted = True
            ready.append(
                ReadyDamageEvent(
                    candidate_id=candidate.candidate_id,
                    original_image=candidate.best_original,
                    tactile_roi=candidate.best_roi,
                    observation_count=len(candidate.observation_times),
                    best_score=candidate.best_score,
                    location=candidate.best_location,
                )
            )
        # Unconfirmed expired candidates are no longer useful and have no event
        # that needs acknowledgement.
        for candidate_id in [
            key
            for key, candidate in self._candidates.items()
            if candidate.ready_emitted and not candidate.confirmed
        ]:
            del self._candidates[candidate_id]
        return ready


def overlapping_tiles(
    roi: np.ndarray,
    tile_size: int = 320,
    overlap: float = 0.30,
) -> list[tuple[tuple[int, int, int, int], np.ndarray]]:
    if roi is None or roi.size == 0:
        raise ValueError("roi is empty")
    height, width = roi.shape[:2]
    tile_width = min(tile_size, width)
    tile_height = min(tile_size, height)
    stride_x = max(1, int(round(tile_width * (1.0 - overlap))))
    stride_y = max(1, int(round(tile_height * (1.0 - overlap))))
    xs = _tile_starts(width, tile_width, stride_x)
    ys = _tile_starts(height, tile_height, stride_y)
    return [
        ((x, y, x + tile_width, y + tile_height), roi[y : y + tile_height, x : x + tile_width])
        for y in ys
        for x in xs
    ]


def _tile_starts(length: int, tile_length: int, stride: int) -> list[int]:
    if length <= tile_length:
        return [0]
    starts = list(range(0, length - tile_length + 1, stride))
    last = length - tile_length
    if starts[-1] != last:
        starts.append(last)
    return starts


def image_quality(frame: np.ndarray, bbox: BBox, confidence: float) -> float:
    crop = expanded_crop(frame, bbox, scale=1.0)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    sharpness = min(float(cv2.Laplacian(gray, cv2.CV_64F).var()) / 500.0, 1.0)
    x1, y1, x2, y2 = _clip_bbox(bbox, frame.shape[1], frame.shape[0])
    area_ratio = ((x2 - x1) * (y2 - y1)) / float(frame.shape[0] * frame.shape[1])
    size_score = min(area_ratio / 0.08, 1.0)
    margin = 3.0
    complete = float(
        x1 > margin
        and y1 > margin
        and x2 < frame.shape[1] - margin
        and y2 < frame.shape[0] - margin
    )
    return 0.35 * confidence + 0.30 * sharpness + 0.20 * size_score + 0.15 * complete


def expanded_crop(frame: np.ndarray, bbox: BBox, scale: float = 1.5) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0
    width = max(x2 - x1, 1.0) * scale
    height = max(y2 - y1, 1.0) * scale
    clipped = _clip_bbox(
        (center_x - width / 2, center_y - height / 2, center_x + width / 2, center_y + height / 2),
        frame.shape[1],
        frame.shape[0],
    )
    cx1, cy1, cx2, cy2 = (int(round(value)) for value in clipped)
    return frame[cy1:cy2, cx1:cx2].copy()


def _clip_bbox(bbox: BBox, width: int, height: int) -> BBox:
    x1, y1, x2, y2 = bbox
    return (
        max(0.0, min(float(width - 1), x1)),
        max(0.0, min(float(height - 1), y1)),
        max(1.0, min(float(width), x2)),
        max(1.0, min(float(height), y2)),
    )


def _union_bbox(boxes: list[BBox]) -> BBox:
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _iou(first: BBox, second: BBox) -> float:
    x1 = max(first[0], second[0])
    y1 = max(first[1], second[1])
    x2 = min(first[2], second[2])
    y2 = min(first[3], second[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = first_area + second_area - intersection
    return intersection / union if union > 0 else 0.0


def _center_distance(first: BBox, second: BBox) -> float:
    first_center = ((first[0] + first[2]) / 2, (first[1] + first[3]) / 2)
    second_center = ((second[0] + second[2]) / 2, (second[1] + second[3]) / 2)
    return float(np.hypot(first_center[0] - second_center[0], first_center[1] - second_center[1]))
