from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from hardware.hal.gpio import DigitalInput


@dataclass(frozen=True)
class HallState:
    detected: bool
    changed: bool
    electrical_high: bool


class HallSensor:
    """Debounced digital Hall switch, active-low by default."""

    def __init__(
        self,
        signal: DigitalInput,
        *,
        active_low: bool = True,
        debounce_sec: float = 0.02,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if debounce_sec < 0:
            raise ValueError("debounce_sec must be non-negative")
        self._signal = signal
        self._active_low = active_low
        self._debounce_sec = debounce_sec
        self._clock = clock
        self._candidate: Optional[bool] = None
        self._candidate_since = 0.0
        self._detected: Optional[bool] = None
        self._closed = False

    def poll(self) -> HallState:
        if self._closed:
            raise RuntimeError("HallSensor is closed")
        electrical_high = self._signal.read()
        observed = not electrical_high if self._active_low else electrical_high
        now = self._clock()
        if observed != self._candidate:
            self._candidate = observed
            self._candidate_since = now
        changed = False
        if observed != self._detected and now - self._candidate_since >= self._debounce_sec:
            self._detected = observed
            changed = True
        current = observed if self._detected is None else self._detected
        return HallState(current, changed, electrical_high)

    def close(self) -> None:
        if not self._closed:
            self._signal.close()
            self._closed = True
