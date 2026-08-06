from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

import numpy as np

from .schemas import (
    AggregationDetail,
    AnalysisDetail,
    DamageAnalysisResponse,
    ImageAnalysisSummary,
    ModelDetail,
)


PRIORITY_BY_SEVERITY = {
    "normal": None,
    "minor": "LOW",
    "moderate": "NORMAL",
    "severe": "HIGH",
}

SEVERITY_LABELS = {
    "normal": "정상 추정",
    "minor": "경미 추정",
    "moderate": "보통 추정",
    "severe": "심각 추정",
}


class Analyzer(Protocol):
    def predict(
        self,
        image: np.ndarray,
        *,
        imgsz: int,
        device: str | int,
        image_quality_ok: bool = True,
    ) -> tuple[dict[str, Any], np.ndarray, np.ndarray]: ...


class AnalysisInputError(ValueError):
    pass


@dataclass(frozen=True)
class InputImage:
    filename: str
    image: np.ndarray


@dataclass(frozen=True)
class _AnalyzedImage:
    index: int
    filename: str
    payload: dict[str, Any]
    damage_score: int
    damage_ratio: float
    damage_ratio_percent: float
    severity: str
    confidence_score: float | None

    @property
    def damaged(self) -> bool:
        return self.damage_score > 0


def calculate_damage_score(damage_ratio_percent: float) -> int:
    """Map the model's damaged-area ratio to the ERD severity score bands."""
    percent = max(0.0, min(float(damage_ratio_percent), 100.0))
    if percent < 0.5:
        return 0
    if percent < 5.0:
        return round(1 + ((percent - 0.5) / 4.5) * 29)
    if percent < 15.0:
        return round(31 + ((percent - 5.0) / 10.0) * 39)
    return round(71 + ((percent - 15.0) / 85.0) * 29)


def read_and_verify_sha256(
    model_path: Path,
    sha256_path: Path,
    *,
    verify: bool,
) -> str:
    if not model_path.is_file():
        raise FileNotFoundError(f"AI model not found: {model_path}")
    if not sha256_path.is_file():
        raise FileNotFoundError(f"AI model SHA-256 file not found: {sha256_path}")

    expected = sha256_path.read_text(encoding="utf-8").strip().split()[0].lower()
    if len(expected) != 64:
        raise ValueError(f"Invalid AI model SHA-256: {sha256_path}")
    if verify:
        digest = hashlib.sha256()
        with model_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        if actual != expected:
            raise ValueError(
                f"AI model SHA-256 mismatch: expected={expected}, actual={actual}"
            )
    return expected


class DamageAnalysisService:
    def __init__(
        self,
        analyzer: Analyzer,
        *,
        model_path: Path,
        model_sha256: str,
        imgsz: int,
        device: str,
    ) -> None:
        self.analyzer = analyzer
        self.model_path = model_path
        self.model_sha256 = model_sha256
        self.imgsz = imgsz
        self.device = device

    def analyze_images(self, images: Sequence[InputImage]) -> DamageAnalysisResponse:
        if not images:
            raise AnalysisInputError("At least one image is required.")

        started_at = time.perf_counter()
        analyzed = [self._analyze_one(index, item) for index, item in enumerate(images)]
        selected = max(
            analyzed,
            key=lambda item: (
                item.damage_score,
                item.damage_ratio,
                item.confidence_score if item.confidence_score is not None else -1.0,
            ),
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

        analysis = selected.payload["analysis"]
        model = selected.payload["model"]
        repair_required = selected.severity in {"moderate", "severe"}

        return DamageAnalysisResponse(
            damaged=selected.damaged,
            damage_score=selected.damage_score,
            damage_type=None,
            repair_required=repair_required,
            repair_priority=PRIORITY_BY_SEVERITY[selected.severity],
            confidence_score=(
                selected.confidence_score if selected.damaged else None
            ),
            analysis_detail=AnalysisDetail(
                model=ModelDetail(
                    name=str(model["name"]),
                    weights=str(model["weights"]),
                    weights_sha256=self.model_sha256,
                    classes={str(key): str(value) for key, value in model["classes"].items()},
                ),
                aggregation=AggregationDetail(
                    image_count=len(analyzed),
                    selected_image_index=selected.index,
                ),
                damage_ratio=selected.damage_ratio,
                damage_ratio_percent=selected.damage_ratio_percent,
                estimated_severity=selected.severity,
                estimated_severity_label=str(
                    analysis.get(
                        "estimated_severity_label",
                        SEVERITY_LABELS[selected.severity],
                    )
                ),
                review_required=bool(analysis.get("review_required", False)),
                review_reasons=[str(reason) for reason in analysis.get("review_reasons", [])],
                advisory_only=bool(analysis.get("advisory_only", True)),
                regions=selected.payload["regions"],
                quality={
                    str(key): float(value)
                    for key, value in selected.payload.get("quality", {}).items()
                },
                images=[self._summary(item) for item in analyzed],
                inference_ms=elapsed_ms,
            ),
        )

    def warmup(self) -> None:
        image = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
        self.analyzer.predict(image, imgsz=self.imgsz, device=self.device)

    def _analyze_one(self, index: int, item: InputImage) -> _AnalyzedImage:
        payload, _, _ = self.analyzer.predict(
            item.image,
            imgsz=self.imgsz,
            device=self.device,
        )
        tactile_pixels = int(
            payload.get("regions", {}).get("tactile_block", {}).get("pixels", 0)
        )
        if tactile_pixels <= 0:
            raise AnalysisInputError(
                f"Tactile block was not detected in image index {index}."
            )

        analysis = payload["analysis"]
        ratio = max(0.0, min(float(analysis["damage_ratio"]), 1.0))
        ratio_percent = round(ratio * 100, 2)
        score = calculate_damage_score(ratio * 100)
        severity = str(analysis["estimated_severity"])
        if severity not in PRIORITY_BY_SEVERITY:
            raise RuntimeError(f"Unknown estimated severity: {severity}")

        raw_confidence = payload["regions"]["damage"].get("confidence")
        confidence = (
            None
            if raw_confidence is None
            else round(max(0.0, min(float(raw_confidence), 1.0)), 4)
        )
        return _AnalyzedImage(
            index=index,
            filename=item.filename,
            payload=payload,
            damage_score=score,
            damage_ratio=round(ratio, 6),
            damage_ratio_percent=ratio_percent,
            severity=severity,
            confidence_score=confidence,
        )

    def _summary(self, item: _AnalyzedImage) -> ImageAnalysisSummary:
        analysis = item.payload["analysis"]
        return ImageAnalysisSummary(
            index=item.index,
            filename=item.filename,
            damaged=item.damaged,
            damage_score=item.damage_score,
            damage_ratio=item.damage_ratio,
            damage_ratio_percent=item.damage_ratio_percent,
            estimated_severity=item.severity,
            confidence_score=item.confidence_score if item.damaged else None,
            review_required=bool(analysis.get("review_required", False)),
        )
