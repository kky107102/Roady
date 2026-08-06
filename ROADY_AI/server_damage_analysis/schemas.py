from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal["normal", "minor", "moderate", "severe"]
RepairPriority = Literal["LOW", "NORMAL", "HIGH", "URGENT"]


class ModelDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    weights: str
    weights_sha256: str
    classes: dict[str, str]


class AggregationDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_count: int = Field(ge=1)
    selected_image_index: int = Field(ge=0)
    strategy: Literal["max_damage_score"] = "max_damage_score"


class ImageAnalysisSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    filename: str
    damaged: bool
    damage_score: int = Field(ge=0, le=100)
    damage_ratio: float = Field(ge=0.0, le=1.0)
    damage_ratio_percent: float = Field(ge=0.0, le=100.0)
    estimated_severity: Severity
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    review_required: bool


class AnalysisDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    model: ModelDetail
    aggregation: AggregationDetail
    damage_ratio: float = Field(ge=0.0, le=1.0)
    damage_ratio_percent: float = Field(ge=0.0, le=100.0)
    estimated_severity: Severity
    estimated_severity_label: str
    review_required: bool
    review_reasons: list[str]
    advisory_only: bool
    regions: dict[str, Any]
    quality: dict[str, float]
    images: list[ImageAnalysisSummary]
    inference_ms: float = Field(ge=0.0)


class DamageAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    damaged: bool
    damage_score: int = Field(ge=0, le=100)
    damage_type: None = None
    repair_required: bool
    repair_priority: RepairPriority | None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    analysis_detail: AnalysisDetail


class HealthResponse(BaseModel):
    status: Literal["ok", "ready"]


class ModelInfoResponse(BaseModel):
    name: str
    weights: str
    weights_sha256: str
    classes: dict[str, str]
    device: str
    imgsz: int
