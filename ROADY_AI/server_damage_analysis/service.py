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
    ReviewReason,
)


PRIORITY_BY_SEVERITY = {
    "normal": None,
    "minor": "LOW",
    "moderate": "NORMAL",
    "severe": "HIGH",
}

SCORE_FLOOR_BY_SEVERITY = {
    "normal": 0,
    "minor": 1,
    "moderate": 31,
    "severe": 71,
}

MISSING_LARGE_THRESHOLD_PERCENT = 15.0

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
        input_metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], np.ndarray, np.ndarray]: ...


class AnalysisInputError(ValueError):
    pass


@dataclass(frozen=True)
class InputImage:
    filename: str
    image: np.ndarray
    input_metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class _AnalyzedImage:
    index: int
    filename: str
    payload: dict[str, Any]
    damage_score: int | None
    damage_ratio: float | None
    damage_ratio_percent: float | None
    severity: str | None
    confidence_score: float | None
    damage_detected: bool | None

    @property
    def damaged(self) -> bool | None:
        return self.damage_detected


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
                item.damage_score if item.damage_score is not None else -1,
                item.damage_ratio if item.damage_ratio is not None else -1.0,
                item.confidence_score if item.confidence_score is not None else -1.0,
            ),
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

        analysis = selected.payload["analysis"]
        summary = selected.payload.get("summary", analysis)
        model = selected.payload["model"]
        repair_required = (
            None
            if selected.severity is None
            else selected.severity in {"moderate", "severe"}
        )
        severity_label = analysis.get("estimated_severity_label")
        if severity_label is None and selected.severity is not None:
            severity_label = SEVERITY_LABELS[selected.severity]

        return DamageAnalysisResponse(
            damaged=selected.damaged,
            damage_score=selected.damage_score,
            damage_type=self._damage_type(selected.payload),
            repair_required=repair_required,
            repair_priority=(
                None
                if selected.severity is None
                else PRIORITY_BY_SEVERITY[selected.severity]
            ),
            confidence_score=(
                selected.confidence_score if selected.damaged is True else None
            ),
            analysis_detail=AnalysisDetail(
                model=ModelDetail(
                    name=str(model["name"]),
                    weights=str(model.get("weights", self.model_path.name)),
                    weights_sha256=self.model_sha256,
                    classes=self._model_classes(model),
                ),
                aggregation=AggregationDetail(
                    image_count=len(analyzed),
                    selected_image_index=selected.index,
                ),
                damage_ratio=selected.damage_ratio,
                damage_ratio_percent=selected.damage_ratio_percent,
                estimated_severity=selected.severity,
                estimated_severity_label=(
                    None if severity_label is None else str(severity_label)
                ),
                review_required=bool(summary.get("review_required", False)),
                review_reasons=self._review_reasons(summary),
                advisory_only=bool(summary.get("advisory_only", True)),
                regions=selected.payload["regions"],
                units=list(selected.payload.get("units", [])),
                summary=dict(selected.payload.get("summary", analysis)),
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
            input_metadata=item.input_metadata,
        )
        analysis = payload["analysis"]
        summary = payload.get("summary", analysis)
        raw_ratio_percent = summary.get("max_damage_ratio_percent")
        if raw_ratio_percent is None:
            raw_ratio_percent = analysis.get("damage_ratio_percent")
        if raw_ratio_percent is None and analysis.get("damage_ratio") is not None:
            raw_ratio_percent = float(analysis["damage_ratio"]) * 100
        ratio_percent = (
            None
            if raw_ratio_percent is None
            else round(max(0.0, min(float(raw_ratio_percent), 100.0)), 2)
        )
        ratio = None if ratio_percent is None else round(ratio_percent / 100, 6)
        raw_severity = summary.get("estimated_severity", analysis.get("estimated_severity"))
        severity = None if raw_severity is None else str(raw_severity)
        if severity is not None and severity not in PRIORITY_BY_SEVERITY:
            raise RuntimeError(f"Unknown estimated severity: {severity}")
        provisional_score = (
            None if ratio_percent is None else calculate_damage_score(ratio_percent)
        )
        damage_detected = self._damage_detected(
            payload,
            summary,
            analysis,
            provisional_score,
        )
        score = provisional_score
        if score is None and damage_detected is True and severity is not None:
            score = SCORE_FLOOR_BY_SEVERITY[severity]

        raw_confidence = payload.get("regions", {}).get("damage", {}).get("confidence")
        if raw_confidence is None:
            raw_confidence = self._maximum_damage_confidence(payload)
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
            damage_ratio=ratio,
            damage_ratio_percent=ratio_percent,
            severity=severity,
            confidence_score=confidence,
            damage_detected=damage_detected,
        )

    @staticmethod
    def _damage_detected(
        payload: dict[str, Any],
        summary: dict[str, Any],
        analysis: dict[str, Any],
        score: int | None,
    ) -> bool | None:
        if str(payload.get("schema_version", "1.0")) != "2.0":
            return bool(score and score > 0)
        value = summary.get("damage_detected", analysis.get("damage_detected"))
        return value if isinstance(value, bool) else None

    @staticmethod
    def _damage_type(payload: dict[str, Any]) -> str | None:
        if str(payload.get("schema_version", "1.0")) != "2.0":
            return None
        summary = payload.get("summary", {})
        dominant = summary.get("dominant_damage_type")
        if dominant == "crack":
            return "CRACK"
        if dominant == "wear":
            return "WEAR"
        if dominant != "missing":
            return None

        worst_unit_id = summary.get("worst_unit_id")
        unit = next(
            (
                item
                for item in payload.get("units", [])
                if item.get("local_unit_id") == worst_unit_id
            ),
            None,
        )
        if unit is None:
            return None
        ratio = (
            unit.get("damage_types", {})
            .get("missing", {})
            .get("ratio_percent")
        )
        if ratio is None:
            return "LARGE_MISSING"
        return (
            "LARGE_MISSING"
            if float(ratio) >= MISSING_LARGE_THRESHOLD_PERCENT
            else "SMALL_MISSING"
        )

    @staticmethod
    def _review_reasons(summary: dict[str, Any]) -> list[ReviewReason]:
        normalized: list[ReviewReason] = []
        for reason in summary.get("review_reasons", []):
            if isinstance(reason, dict):
                code = str(reason.get("code", "UNKNOWN"))
                message = str(reason.get("message", code))
            else:
                code = str(reason)
                message = code
            normalized.append(ReviewReason(code=code, message=message))
        return normalized

    @staticmethod
    def _model_classes(model: dict[str, Any]) -> dict[str, str]:
        classes = model.get("classes")
        if isinstance(classes, dict):
            return {str(key): str(value) for key, value in classes.items()}
        return {
            str(index): str(name)
            for index, name in enumerate(model.get("class_names", []))
        }

    @staticmethod
    def _maximum_damage_confidence(payload: dict[str, Any]) -> float | None:
        values = [
            details.get("confidence")
            for unit in payload.get("units", [])
            for name, details in unit.get("damage_types", {}).items()
            if name in {"missing", "crack", "wear"}
            and details.get("confidence") is not None
        ]
        return max(values) if values else None

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
            confidence_score=item.confidence_score if item.damaged is True else None,
            review_required=bool(
                item.payload.get("summary", analysis).get("review_required", False)
            ),
        )
