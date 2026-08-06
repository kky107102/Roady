from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .policy import (
    AnalysisPolicy,
    ModelQuality,
    PRIORITY_BY_SEVERITY,
    SEVERITY_LABELS,
    classify_severity,
    decide_review,
)

TACTILE_BLOCK = 0
DAMAGE = 1


def _resize_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    height, width = shape
    return cv2.resize(
        mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST
    ).astype(bool)


def _mask_iou(left: np.ndarray, right: np.ndarray) -> float:
    union = np.logical_or(left, right).sum()
    return 0.0 if union == 0 else float(np.logical_and(left, right).sum() / union)


def _deduplicate(items: list[tuple[float, np.ndarray]], threshold: float):
    kept: list[tuple[float, np.ndarray]] = []
    for confidence, mask in sorted(items, key=lambda item: item[0], reverse=True):
        if all(_mask_iou(mask, previous) < threshold for _, previous in kept):
            kept.append((confidence, mask))
    return kept


def _union(items: list[tuple[float, np.ndarray]], shape: tuple[int, int]) -> np.ndarray:
    merged = np.zeros(shape, dtype=bool)
    for _, mask in items:
        merged |= mask
    return merged


def _polygons(mask: np.ndarray) -> list[list[list[int]]]:
    contours, _ = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    result: list[list[list[int]]] = []
    for contour in contours:
        if cv2.contourArea(contour) < 2:
            continue
        epsilon = 0.001 * cv2.arcLength(contour, True)
        simplified = cv2.approxPolyDP(contour, epsilon, True)
        result.append([[int(x), int(y)] for [[x, y]] in simplified.tolist()])
    return result


def _bbox(mask: np.ndarray) -> list[int] | None:
    ys, xs = np.where(mask)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


class ServerDamageAnalyzer:
    """YOLO Seg 결과를 관리자용 분석 JSON과 시각화 산출물로 변환한다."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        policy: AnalysisPolicy = AnalysisPolicy(),
        quality: ModelQuality = ModelQuality(),
    ) -> None:
        from ultralytics import YOLO

        self.model_path = Path(model_path)
        self.model = YOLO(str(self.model_path))
        self.policy = policy
        self.quality = quality

    def predict(
        self,
        image: str | Path | np.ndarray,
        *,
        imgsz: int = 1024,
        device: str | int = "cpu",
        image_quality_ok: bool = True,
    ) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
        result = self.model.predict(
            source=image,
            imgsz=imgsz,
            conf=min(self.policy.damage_confidence, self.policy.tactile_confidence),
            device=device,
            verbose=False,
        )[0]
        return self.analyze_result(result, image_quality_ok=image_quality_ok)

    def analyze_result(
        self, result: Any, *, image_quality_ok: bool = True
    ) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
        height, width = result.orig_shape
        original = result.orig_img.copy()
        candidates: dict[int, list[tuple[float, np.ndarray]]] = {
            TACTILE_BLOCK: [], DAMAGE: []
        }
        if result.boxes is not None and result.masks is not None:
            classes = result.boxes.cls.detach().cpu().numpy().astype(int)
            confidences = result.boxes.conf.detach().cpu().numpy().astype(float)
            masks = result.masks.data.detach().cpu().numpy()
            for class_id, confidence, mask in zip(classes, confidences, masks):
                if class_id not in candidates:
                    continue
                threshold = (
                    self.policy.tactile_confidence
                    if class_id == TACTILE_BLOCK
                    else self.policy.damage_confidence
                )
                if confidence >= threshold:
                    candidates[class_id].append(
                        (float(confidence), _resize_mask(mask, (height, width)))
                    )

        tactile_items = _deduplicate(candidates[TACTILE_BLOCK], self.policy.duplicate_mask_iou)
        damage_items = _deduplicate(candidates[DAMAGE], self.policy.duplicate_mask_iou)
        tactile_mask = _union(tactile_items, (height, width))
        raw_damage_mask = _union(damage_items, (height, width))
        damage_mask = raw_damage_mask & tactile_mask

        tactile_pixels = int(tactile_mask.sum())
        damage_pixels = int(damage_mask.sum())
        ratio = 0.0 if tactile_pixels == 0 else damage_pixels / tactile_pixels
        estimated = classify_severity(ratio, self.policy)
        priority_code, priority_label = PRIORITY_BY_SEVERITY[estimated]
        tactile_conf = max((conf for conf, _ in tactile_items), default=None)
        damage_conf = max((conf for conf, _ in damage_items), default=None)
        reasons = decide_review(
            ratio=ratio,
            tactile_pixels=tactile_pixels,
            tactile_confidence=tactile_conf,
            damage_confidence=damage_conf,
            image_quality_ok=image_quality_ok,
            quality=self.quality,
            policy=self.policy,
        )

        overlay = original.copy()
        tactile_contours, _ = cv2.findContours(
            tactile_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        damage_contours, _ = cv2.findContours(
            damage_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(overlay, tactile_contours, -1, (64, 220, 120), 2)
        tint = overlay.copy()
        cv2.drawContours(tint, damage_contours, -1, (40, 40, 230), cv2.FILLED)
        overlay = cv2.addWeighted(tint, 0.35, overlay, 0.65, 0)
        cv2.drawContours(overlay, damage_contours, -1, (40, 40, 230), 2)

        payload: dict[str, Any] = {
            "schema_version": "1.0",
            "model": {
                "name": "yolo26s-seg-server-v1",
                "weights": self.model_path.name,
                "classes": {"0": "tactile_block", "1": "damage"},
            },
            "artifacts": {"original_image": None, "overlay_image": None, "mask_image": None},
            "regions": {
                "tactile_block": {
                    "bbox_xyxy": _bbox(tactile_mask), "polygons": _polygons(tactile_mask),
                    "confidence": tactile_conf, "pixels": tactile_pixels,
                },
                "damage": {
                    "bbox_xyxy": _bbox(damage_mask), "polygons": _polygons(damage_mask),
                    "confidence": damage_conf, "pixels": damage_pixels,
                    "raw_pixels": int(raw_damage_mask.sum()),
                    "outside_tactile_pixels": int((raw_damage_mask & ~tactile_mask).sum()),
                    "merged_instance_count": len(damage_items),
                },
            },
            "analysis": {
                "damage_detected": damage_pixels > 0,
                "damage_ratio": round(ratio, 6),
                "damage_ratio_percent": round(ratio * 100, 2),
                "estimated_severity": estimated,
                "estimated_severity_label": SEVERITY_LABELS[estimated],
                "repair_priority": priority_code,
                "repair_priority_label": priority_label,
                "review_required": bool(reasons),
                "review_reasons": reasons,
                "advisory_only": True,
            },
            "quality": {
                "positive_damage_dice": self.quality.positive_damage_dice,
                "damage_f2": self.quality.damage_f2,
                "ratio_mae_pp": self.quality.ratio_mae_pp,
                "severity_macro_f1": self.quality.severity_macro_f1,
            },
        }
        return payload, overlay, damage_mask
