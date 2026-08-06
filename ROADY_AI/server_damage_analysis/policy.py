from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisPolicy:
    """서비스 잠정 정책. 비율 값은 0~1 범위다."""

    normal_limit: float = 0.005
    minor_limit: float = 0.05
    moderate_limit: float = 0.15
    boundary_margin: float = 0.01
    tactile_confidence: float = 0.25
    damage_confidence: float = 0.05
    duplicate_mask_iou: float = 0.70
    minimum_tactile_pixels: int = 100
    minimum_damage_confidence_for_auto: float = 0.70
    minimum_positive_damage_dice: float = 0.70
    maximum_ratio_mae_pp: float = 3.0
    minimum_severity_macro_f1: float = 0.80


@dataclass(frozen=True)
class ModelQuality:
    """고정된 검증 지표. v1의 서비스 기준 평가 결과다."""

    positive_damage_dice: float = 0.08300269501207208
    damage_f2: float = 0.826086956521739
    ratio_mae_pp: float = 6.084992637708795
    severity_macro_f1: float = 0.21873215305539692


SEVERITY_LABELS = {
    "normal": "정상 추정",
    "minor": "경미 추정",
    "moderate": "보통 추정",
    "severe": "심각 추정",
}

PRIORITY_BY_SEVERITY = {
    "normal": ("none", "이상 없음"),
    "minor": ("monitor", "경과 관찰"),
    "moderate": ("inspection_required", "보수 확인 필요"),
    "severe": ("repair_candidate", "보수 필수 후보"),
}


def classify_severity(ratio: float, policy: AnalysisPolicy) -> str:
    if ratio < policy.normal_limit:
        return "normal"
    if ratio < policy.minor_limit:
        return "minor"
    if ratio < policy.moderate_limit:
        return "moderate"
    return "severe"


def decide_review(
    *,
    ratio: float,
    tactile_pixels: int,
    tactile_confidence: float | None,
    damage_confidence: float | None,
    image_quality_ok: bool,
    quality: ModelQuality,
    policy: AnalysisPolicy,
) -> list[str]:
    reasons: list[str] = []
    if not image_quality_ok:
        reasons.append("image_quality_insufficient")
    if tactile_pixels < policy.minimum_tactile_pixels:
        reasons.append("tactile_mask_missing_or_small")
    if tactile_confidence is None or tactile_confidence < policy.tactile_confidence:
        reasons.append("tactile_confidence_low")
    if ratio > 0 and (
        damage_confidence is None
        or damage_confidence < policy.minimum_damage_confidence_for_auto
    ):
        reasons.append("damage_confidence_low")
    if any(
        abs(ratio - threshold) <= policy.boundary_margin
        for threshold in (policy.normal_limit, policy.minor_limit, policy.moderate_limit)
    ):
        reasons.append("severity_boundary_ambiguous")
    if quality.positive_damage_dice < policy.minimum_positive_damage_dice:
        reasons.append("damage_mask_quality_below_target")
    if quality.ratio_mae_pp > policy.maximum_ratio_mae_pp:
        reasons.append("damage_ratio_error_above_target")
    if quality.severity_macro_f1 < policy.minimum_severity_macro_f1:
        reasons.append("severity_quality_below_target")
    return list(dict.fromkeys(reasons))
