from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from ROADY_AI.server_damage_analysis.api import create_app
from ROADY_AI.server_damage_analysis.config import AppSettings
from ROADY_AI.tests.test_server_damage_service import FakeAnalyzer, payload


def test_analyze_accepts_spring_multipart_contract(tmp_path: Path):
    app = build_test_app(tmp_path, [payload(0.0859, 0.84321)])

    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            data={
                "damageId": "42",
                "latitude": "",
                "longitude": "",
                "capturedAt": "",
            },
            files=[("images", ("damage.jpg", jpeg_bytes(), "application/octet-stream"))],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["damaged"] is True
    assert body["damage_score"] == 45
    assert body["damage_type"] is None
    assert body["repair_required"] is True
    assert body["repair_priority"] == "NORMAL"
    assert body["confidence_score"] == 0.8432
    assert body["analysis_detail"]["aggregation"]["image_count"] == 1


def test_health_and_model_info_are_ready(tmp_path: Path):
    app = build_test_app(tmp_path, [payload(0.0, None)])

    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready"}
        model_info = client.get("/model-info").json()

    assert model_info["name"] == "yolo26s-seg-server-v1"
    assert model_info["weights"] == "model.pt"
    assert model_info["weights_sha256"] == "a" * 64


def test_analyze_rejects_non_image_payload(tmp_path: Path):
    app = build_test_app(tmp_path, [payload(0.0, None)])

    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            data={"damageId": "42"},
            files=[("images", ("not-image.txt", b"hello", "text/plain"))],
        )

    assert response.status_code == 415
    assert response.json()["detail"] == "Image index 0 cannot be decoded."


def test_analyze_rejects_invalid_damage_id(tmp_path: Path):
    app = build_test_app(tmp_path, [payload(0.0, None)])

    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            data={"damageId": "invalid"},
            files=[("images", ("damage.jpg", jpeg_bytes(), "image/jpeg"))],
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "damageId must be a positive integer."


def build_test_app(tmp_path: Path, payloads: list[dict]):
    model_path = tmp_path / "model.pt"
    sha_path = tmp_path / "model.sha256"
    model_path.write_bytes(b"fake-model")
    sha_path.write_text(("a" * 64) + "  model.pt\n", encoding="utf-8")
    settings = AppSettings(
        model_path=model_path,
        model_sha256_path=sha_path,
        verify_model_hash=False,
        warmup_enabled=False,
    )
    return create_app(settings, analyzer_factory=lambda _: FakeAnalyzer(payloads))


def jpeg_bytes() -> bytes:
    ok, encoded = cv2.imencode(".jpg", np.zeros((10, 10, 3), dtype=np.uint8))
    assert ok
    return encoded.tobytes()
