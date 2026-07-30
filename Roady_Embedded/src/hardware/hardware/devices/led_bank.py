from __future__ import annotations

from collections.abc import Sequence

from hardware.hal.gpio import DigitalOutput


class LedBank:
    """Platform-independent collection of active-high LEDs."""

    def __init__(self, outputs: Sequence[DigitalOutput]) -> None:
        if not outputs:
            raise ValueError("at least one LED output is required")
        self._outputs = list(outputs)
        self._closed = False

    def set(self, index: int, on: bool) -> None:
        if self._closed:
            raise RuntimeError("LedBank is closed")
        self._outputs[index].write(on)

    def set_all(self, on: bool) -> None:
        if self._closed:
            raise RuntimeError("LedBank is closed")
        for output in self._outputs:
            output.write(on)

    def close(self) -> None:
        if self._closed:
            return
        for output in self._outputs:
            output.write(False)
        for output in self._outputs:
            output.close()
        self._closed = True
