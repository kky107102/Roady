from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraSafetyState:
    stop_required: bool
    reason: str
    recent_detections: tuple[bool, ...]
    clear_count: int
    camera_alive: bool


class CameraSafetyFilter:
    """Latch a camera stop using vote-to-stop and conservative release rules."""

    def __init__(
        self,
        vote_window: int = 3,
        vote_required: int = 2,
        clear_frames: int = 10,
        minimum_hold_sec: float = 1.0,
    ) -> None:
        if vote_window <= 0:
            raise ValueError("vote_window must be positive")
        if not 1 <= vote_required <= vote_window:
            raise ValueError("vote_required must be between 1 and vote_window")
        if clear_frames <= 0:
            raise ValueError("clear_frames must be positive")
        if minimum_hold_sec < 0:
            raise ValueError("minimum_hold_sec must not be negative")

        self._vote_window = vote_window
        self._vote_required = vote_required
        self._clear_frames = clear_frames
        self._minimum_hold_sec = minimum_hold_sec
        self._recent: deque[bool] = deque(maxlen=vote_window)
        self._stop_required = False
        self._reason = "clear"
        self._clear_count = 0
        self._stopped_at: float | None = None
        self._last_camera_update: float | None = None
        self._camera_alive = False

    def update(self, detected: bool, now: float) -> CameraSafetyState:
        self._last_camera_update = now
        self._camera_alive = True
        self._recent.append(bool(detected))

        if not self._stop_required:
            if (
                len(self._recent) == self._vote_window
                and sum(self._recent) >= self._vote_required
            ):
                self._engage("camera_lower_limb", now)
        elif detected:
            self._clear_count = 0
        else:
            self._clear_count += 1
            self._release_if_ready(now)

        return self.state

    def check_timeout(
        self,
        now: float,
        timeout_sec: float,
        stop_on_timeout: bool,
    ) -> CameraSafetyState:
        if timeout_sec <= 0:
            self._camera_alive = True
            return self.state

        self._camera_alive = (
            self._last_camera_update is not None
            and now - self._last_camera_update <= timeout_sec
        )
        if not self._camera_alive and stop_on_timeout and not self._stop_required:
            self._engage("camera_timeout", now)
        return self.state

    def _engage(self, reason: str, now: float) -> None:
        self._stop_required = True
        self._reason = reason
        self._clear_count = 0
        self._stopped_at = now

    def _release_if_ready(self, now: float) -> None:
        hold_elapsed = (
            self._stopped_at is not None
            and now - self._stopped_at >= self._minimum_hold_sec
        )
        if self._clear_count >= self._clear_frames and hold_elapsed:
            self._stop_required = False
            self._reason = "clear"
            self._clear_count = 0
            self._stopped_at = None
            self._recent.clear()

    @property
    def state(self) -> CameraSafetyState:
        return CameraSafetyState(
            stop_required=self._stop_required,
            reason=self._reason,
            recent_detections=tuple(self._recent),
            clear_count=self._clear_count,
            camera_alive=self._camera_alive,
        )
