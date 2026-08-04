from __future__ import annotations

import csv
import json
import math
import time
from datetime import datetime
from pathlib import Path


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(percent / 100.0 * len(ordered)) - 1)
    return ordered[max(index, 0)]


def jetson_temperature_c() -> float | None:
    temperatures: list[float] = []
    for path in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            value = float(path.read_text(encoding="utf-8").strip())
            temperatures.append(value / 1000.0 if value > 200.0 else value)
        # Some Jetson thermal drivers can return an empty/transient read while
        # the sysfs value is being refreshed. Temperature telemetry must never
        # terminate the safety-critical detection callback.
        except (OSError, TypeError, ValueError):
            continue
    return max(temperatures) if temperatures else None


class BenchmarkRecorder:
    def __init__(
        self,
        duration_sec: float,
        report_path: str | Path,
        label: str = "unnamed",
        history_path: str | Path | None = None,
    ) -> None:
        self.duration_sec = duration_sec
        self.report_path = Path(report_path).expanduser()
        self.label = label
        self.history_path = Path(history_path).expanduser() if history_path else None
        self.started_monotonic: float | None = None
        self.started_wall: float | None = None
        self.latencies_ms: list[float] = []
        self.temperatures_c: list[float] = []
        self.detection_counts: list[int] = []
        self.completed = False

    def add(
        self,
        latency_ms: float,
        temperature_c: float | None,
        detection_count: int = 0,
    ) -> None:
        if self.started_monotonic is None:
            self.started_monotonic = time.monotonic()
            self.started_wall = time.time()
        self.latencies_ms.append(latency_ms)
        self.detection_counts.append(detection_count)
        if temperature_c is not None:
            self.temperatures_c.append(temperature_c)

    @property
    def elapsed_sec(self) -> float:
        if self.started_monotonic is None:
            return 0.0
        return time.monotonic() - self.started_monotonic

    @property
    def due(self) -> bool:
        return self.duration_sec > 0 and self.elapsed_sec >= self.duration_sec

    def summary(
        self,
        model_path: str,
        camera_topic: str,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        elapsed = self.elapsed_sec
        latency = self.latencies_ms
        temperatures = self.temperatures_c
        detection_counts = self.detection_counts
        detected_frames = sum(count > 0 for count in detection_counts)
        return {
            "schema_version": 1,
            "label": self.label,
            "model": model_path,
            "camera_topic": camera_topic,
            "started_unix_sec": self.started_wall,
            "started_at": (
                datetime.fromtimestamp(self.started_wall).astimezone().isoformat()
                if self.started_wall is not None
                else None
            ),
            "duration_sec": elapsed,
            "frames": len(latency),
            "end_to_end_fps": len(latency) / elapsed if elapsed > 0 else 0.0,
            "detections": {
                "detected_frames": detected_frames,
                "detection_rate": (
                    detected_frames / len(detection_counts) if detection_counts else 0.0
                ),
                "mean_per_frame": (
                    sum(detection_counts) / len(detection_counts)
                    if detection_counts
                    else 0.0
                ),
                "max_per_frame": max(detection_counts, default=0),
            },
            "latency_ms": {
                "mean": sum(latency) / len(latency) if latency else 0.0,
                "p50": percentile(latency, 50),
                "p95": percentile(latency, 95),
                "max": max(latency, default=0.0),
            },
            "temperature_c": {
                "samples": len(temperatures),
                "mean": sum(temperatures) / len(temperatures) if temperatures else None,
                "max": max(temperatures, default=None),
            },
            "configuration": metadata or {},
        }

    def write(
        self,
        model_path: str,
        camera_topic: str,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        report = self.summary(model_path, camera_topic, metadata)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if self.history_path is not None:
            self._append_history(report)
        self.completed = True
        return report

    def _append_history(self, report: dict[str, object]) -> None:
        assert self.history_path is not None
        latency = report["latency_ms"]
        temperature = report["temperature_c"]
        detections = report["detections"]
        configuration = report["configuration"]
        assert isinstance(latency, dict)
        assert isinstance(temperature, dict)
        assert isinstance(detections, dict)
        assert isinstance(configuration, dict)
        row = {
            "started_at": report["started_at"],
            "label": report["label"],
            "duration_sec": report["duration_sec"],
            "frames": report["frames"],
            "fps": report["end_to_end_fps"],
            "detection_rate": detections["detection_rate"],
            "detections_mean_per_frame": detections["mean_per_frame"],
            "detections_max_per_frame": detections["max_per_frame"],
            "latency_mean_ms": latency["mean"],
            "latency_p50_ms": latency["p50"],
            "latency_p95_ms": latency["p95"],
            "latency_max_ms": latency["max"],
            "temperature_mean_c": temperature["mean"],
            "temperature_max_c": temperature["max"],
            "camera_width": configuration.get("camera_width"),
            "camera_height": configuration.get("camera_height"),
            "confidence": configuration.get("confidence"),
            "publish_annotated": configuration.get("publish_annotated"),
            "engine_sha256": configuration.get("engine_sha256"),
            "report_path": str(self.report_path),
        }
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.history_path.exists() and self.history_path.stat().st_size > 0
        with self.history_path.open("a", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(row))
            if not exists:
                writer.writeheader()
            writer.writerow(row)
