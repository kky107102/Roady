from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class WheelDistance:
    pulse_count: int
    distance_m: float


class WheelOdometry:
    """Convert Hall-sensor pulses into cumulative wheel travel distance."""

    def __init__(
        self,
        *,
        wheel_diameter_m: float = 0.10,
        pulses_per_revolution: int = 1,
    ) -> None:
        if not math.isfinite(wheel_diameter_m) or wheel_diameter_m <= 0.0:
            raise ValueError("wheel_diameter_m must be a finite positive value")
        if pulses_per_revolution <= 0:
            raise ValueError("pulses_per_revolution must be positive")
        self._meters_per_pulse = (
            math.pi * wheel_diameter_m / pulses_per_revolution
        )
        self._pulse_count = 0

    @property
    def state(self) -> WheelDistance:
        return WheelDistance(
            pulse_count=self._pulse_count,
            distance_m=self._pulse_count * self._meters_per_pulse,
        )

    def record_pulse(self) -> WheelDistance:
        self._pulse_count += 1
        return self.state
