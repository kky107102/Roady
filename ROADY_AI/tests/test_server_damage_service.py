from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ROADY_AI.server_damage_analysis.service import (
    AnalysisInputError,
    DamageAnalysisService,
    InputImage,
    calculate_damage_score,
)


@pytest.mark.parametrize(
    ("percent", "expected"),
    [
        (0.0, 0),
        (0.49, 0),
        (0.5, 1),
        (4.99, 30),
        (5.0, 31),
        (8.59, 45),
        (14.99, 70),
        (15.0, 71),
        (100.0, 100),
    ],
)
def test_damage_score_matches_erd_severity_bands(percent: float, expected: int):
    assert calculate_damage_score(percent) == expected


def test_service_maps_model_result_to_database_contract():
    service = make_service(FakeAnalyzer([payload(0.0859, 0.84321)]))

    response = service.analyze_images([input_image("damage.jpg")])

    assert response.damaged is True
    assert response.damage_score == 45
    assert response.damage_type is None
    assert response.repair_required is True
    assert response.repair_priority == "NORMAL"
    assert response.confidence_score == 0.8432
    assert response.analysis_detail.damage_ratio_percent == 8.59
    assert response.analysis_detail.estimated_severity == "moderate"
    assert response.analysis_detail.model.weights_sha256 == "a" * 64


def test_service_selects_highest_risk_image():
    service = make_service(
        FakeAnalyzer(
            [
                payload(0.02, 0.91),
                payload(0.20, 0.81),
                payload(0.08, 0.95),
            ]
        )
    )

    response = service.analyze_images(
        [
            input_image("minor.jpg"),
            input_image("severe.jpg"),
            input_image("moderate.jpg"),
        ]
    )

    assert response.damage_score == 73
    assert response.repair_required is True
    assert response.repair_priority == "HIGH"
    assert response.confidence_score == 0.81
    assert response.analysis_detail.aggregation.image_count == 3
    assert response.analysis_detail.aggregation.selected_image_index == 1
    assert len(response.analysis_detail.images) == 3


def test_service_returns_normal_contract_below_damage_threshold():
    service = make_service(FakeAnalyzer([payload(0.004, 0.88)]))

    response = service.analyze_images([input_image("normal.jpg")])

    assert response.damaged is False
    assert response.damage_score == 0
    assert response.repair_required is False
    assert response.repair_priority is None
    assert response.confidence_score is None


def test_service_rejects_result_without_tactile_block():
    service = make_service(FakeAnalyzer([payload(0.0, None, tactile_pixels=0)]))

    with pytest.raises(AnalysisInputError, match="Tactile block was not detected"):
        service.analyze_images([input_image("missing.jpg")])


class FakeAnalyzer:
    def __init__(self, payloads: list[dict]):
        self.payloads = iter(payloads)

    def predict(self, image, *, imgsz, device, image_quality_ok=True):
        del image, imgsz, device, image_quality_ok
        return next(self.payloads), np.zeros((2, 2, 3)), np.zeros((2, 2))


def make_service(analyzer: FakeAnalyzer) -> DamageAnalysisService:
    return DamageAnalysisService(
        analyzer,
        model_path=Path("yolo26s_seg_v1_best.pt"),
        model_sha256="a" * 64,
        imgsz=1024,
        device="cpu",
    )


def input_image(filename: str) -> InputImage:
    return InputImage(filename=filename, image=np.zeros((10, 10, 3), dtype=np.uint8))


def payload(
    ratio: float,
    confidence: float | None,
    *,
    tactile_pixels: int = 1000,
) -> dict:
    if ratio < 0.005:
        severity = "normal"
    elif ratio < 0.05:
        severity = "minor"
    elif ratio < 0.15:
        severity = "moderate"
    else:
        severity = "severe"
    damage_pixels = round(tactile_pixels * ratio)
    return {
        "schema_version": "1.0",
        "model": {
            "name": "yolo26s-seg-server-v1",
            "weights": "yolo26s_seg_v1_best.pt",
            "classes": {"0": "tactile_block", "1": "damage"},
        },
        "regions": {
            "tactile_block": {
                "bbox_xyxy": [0, 0, 10, 10],
                "polygons": [],
                "confidence": 0.9,
                "pixels": tactile_pixels,
            },
            "damage": {
                "bbox_xyxy": [1, 1, 2, 2] if damage_pixels else None,
                "polygons": [],
                "confidence": confidence,
                "pixels": damage_pixels,
                "raw_pixels": damage_pixels,
                "outside_tactile_pixels": 0,
                "merged_instance_count": 1 if damage_pixels else 0,
            },
        },
        "analysis": {
            "damage_detected": damage_pixels > 0,
            "damage_ratio": ratio,
            "damage_ratio_percent": ratio * 100,
            "estimated_severity": severity,
            "estimated_severity_label": severity,
            "repair_priority": "inspection_required",
            "repair_priority_label": "보수 확인 필요",
            "review_required": True,
            "review_reasons": ["severity_quality_below_target"],
            "advisory_only": True,
        },
        "quality": {
            "positive_damage_dice": 0.083,
            "damage_f2": 0.8261,
            "ratio_mae_pp": 6.085,
            "severity_macro_f1": 0.2187,
        },
    }
