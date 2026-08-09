import pytest

from hardware.devices.battery_indicator import BatteryIndicator
from hardware.devices.led_bank import LedBank


class FakeOutput:
    def __init__(self):
        self.values = []
        self.closed = False
    def write(self, value): self.values.append(value)
    def close(self): self.closed = True


def test_individual_and_all_led_control():
    first, second = FakeOutput(), FakeOutput()
    leds = LedBank((first, second))
    leds.set(0, True)
    leds.set(1, False)
    leds.set_all(True)
    assert first.values == [True, True]
    assert second.values == [False, True]


def test_close_turns_every_led_off_and_is_idempotent():
    first, second = FakeOutput(), FakeOutput()
    leds = LedBank((first, second))
    leds.close()
    leds.close()
    assert first.values == [False] and second.values == [False]
    assert first.closed and second.closed


def test_battery_at_or_above_threshold_turns_green_on():
    green, red = FakeOutput(), FakeOutput()
    indicator = BatteryIndicator(LedBank((green, red)), low_threshold=20.0)

    assert indicator.show(100.0) is False
    assert indicator.show(20.0) is False
    assert green.values == [False, True, False, True]
    assert red.values == [False, False]


def test_battery_below_threshold_turns_red_on():
    green, red = FakeOutput(), FakeOutput()
    indicator = BatteryIndicator(LedBank((green, red)), low_threshold=20.0)

    assert indicator.show(19.9) is True
    assert green.values == [False]
    assert red.values == [False, True]


@pytest.mark.parametrize("battery_percent", [-0.1, 100.1])
def test_invalid_battery_percent_is_rejected(battery_percent):
    indicator = BatteryIndicator(LedBank((FakeOutput(), FakeOutput())))

    with pytest.raises(ValueError):
        indicator.show(battery_percent)
