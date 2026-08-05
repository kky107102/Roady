from __future__ import annotations

from hardware.devices.led_bank import LedBank


class BatteryIndicator:
    """Display a battery level using green and red LEDs."""

    GREEN_INDEX = 0
    RED_INDEX = 1

    def __init__(self, leds: LedBank, *, low_threshold: float = 20.0) -> None:
        if not 0.0 <= low_threshold <= 100.0:
            raise ValueError("low_threshold must be between 0 and 100")
        self._leds = leds
        self._low_threshold = low_threshold

    def show(self, battery_percent: float) -> bool:
        """Show the level and return True when the battery is low."""
        if not 0.0 <= battery_percent <= 100.0:
            raise ValueError("battery_percent must be between 0 and 100")

        is_low = battery_percent < self._low_threshold
        # Turn the previous colour off before enabling the selected colour.
        self._leds.set(self.GREEN_INDEX, False)
        self._leds.set(self.RED_INDEX, False)
        self._leds.set(self.RED_INDEX if is_low else self.GREEN_INDEX, True)
        return is_low
