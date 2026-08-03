from __future__ import annotations

import json
import math
import time
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
        except (OSError, ValueError):
            continue
    return max(temperatures) if temperatures else None


class BenchmarkRecorder:
    def __init__(self, duration_sec: float, report_path: str | Path) -> None:
        self.duration_sec = duration_sec
        self.report_path = Path(report_path).expanduser()
        self.started_monotonic = time.monotonic()
        self.started_wall = time.time()
        self.latencies_ms: list[float] = []
        self.temperatures_c: list[float] = []
        self.completed = False

    def add(self, latency_ms: float, temperature_c: float | None) -> None:
        self.latencies_ms.append(latency_ms)
        if temperature_c is not None:
            self.temperatures_c.append(temperature_c)

    @property
    def elapsed_sec(self) -> float:
        return time.monotonic() - self.started_monotonic

    @property
    def due(self) -> bool:
        return self.duration_sec > 0 and self.elapsed_sec >= self.duration_sec

    def summary(self, model_path: str, camera_topic: str) -> dict[str, object]:
        elapsed = self.elapsed_sec
        latency = self.latencies_ms
        temperatures = self.temperatures_c
        return {
            "model": model_path,
            "camera_topic": camera_topic,
            "started_unix_sec": self.started_wall,
            "duration_sec": elapsed,
            "frames": len(latency),
            "end_to_end_fps": len(latency) / elapsed if elapsed > 0 else 0.0,
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
        }

    def write(self, model_path: str, camera_topic: str) -> dict[str, object]:
        report = self.summary(model_path, camera_topic)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.completed = True
        return report
