from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from hardware.hal.gpio import DigitalInput, DigitalOutput


@dataclass(frozen=True)
class PushLockState:
    locked: bool
    changed: bool


class PushLock:
    """Debounced active-low push-lock switch with an indicator LED."""

    def __init__(
        self,
        switch: DigitalInput,
        indicator: DigitalOutput,
        *,
        active_low: bool = True,
        indicator_active_low: bool = False,
        debounce_sec: float = 0.05,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if debounce_sec < 0:
            raise ValueError("debounce_sec must be non-negative")
        self._switch, self._indicator = switch, indicator
        self._active_low, self._debounce_sec, self._clock = active_low, debounce_sec, clock
        self._indicator_active_low = indicator_active_low
        self._candidate: Optional[bool] = None
        self._candidate_since = 0.0
        self._locked: Optional[bool] = None
        self._closed = False

    @property
    def locked(self) -> Optional[bool]:
        return self._locked

    def poll(self) -> PushLockState:
        if self._closed:
            raise RuntimeError("PushLock is closed")
        level = self._switch.read()
        observed = not level if self._active_low else level
        now = self._clock()
        if observed != self._candidate:
            self._candidate, self._candidate_since = observed, now
        changed = False
        if observed != self._locked and now - self._candidate_since >= self._debounce_sec:
            self._locked = observed
            self._write_indicator(observed)
            changed = True
        return PushLockState(self._locked if self._locked is not None else observed, changed)

    def close(self) -> None:
        if self._closed:
            return
        self._write_indicator(False)
        self._switch.close()
        self._indicator.close()
        self._closed = True

    def _write_indicator(self, on: bool) -> None:
        self._indicator.write(not on if self._indicator_active_low else on)
