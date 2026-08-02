import math

import pytest

from hardware.devices.hall_sensor import HallSensor
from hardware.devices.wheel_odometry import WheelOdometry


class FakeInput:
    def __init__(self, level=True):
        self.level = level
        self.closed = False
    def read(self): return self.level
    def close(self): self.closed = True


class FakeClock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now
    def advance(self, seconds): self.now += seconds


def test_active_low_magnet_detection_is_debounced():
    signal, clock = FakeInput(True), FakeClock()
    sensor = HallSensor(signal, debounce_sec=0.02, clock=clock)
    assert not sensor.poll().changed
    clock.advance(0.02)
    state = sensor.poll()
    assert state.changed and not state.detected and state.electrical_high
    signal.level = False
    assert not sensor.poll().changed
    clock.advance(0.02)
    state = sensor.poll()
    assert state.changed and state.detected and not state.electrical_high


def test_close_is_idempotent():
    signal = FakeInput()
    sensor = HallSensor(signal)
    sensor.close()
    sensor.close()
    assert signal.closed


def test_one_magnet_pulse_adds_one_wheel_circumference():
    odometry = WheelOdometry(wheel_diameter_m=0.10)

    first = odometry.record_pulse()
    second = odometry.record_pulse()

    assert first.pulse_count == 1
    assert first.distance_m == pytest.approx(math.pi * 0.10)
    assert second.pulse_count == 2
    assert second.distance_m == pytest.approx(2 * math.pi * 0.10)


def test_multiple_magnets_reduce_distance_per_pulse():
    odometry = WheelOdometry(
        wheel_diameter_m=0.10,
        pulses_per_revolution=2,
    )

    assert odometry.record_pulse().distance_m == pytest.approx(math.pi * 0.05)


@pytest.mark.parametrize("diameter", [0.0, -0.1, float("nan")])
def test_invalid_wheel_diameter_is_rejected(diameter):
    with pytest.raises(ValueError):
        WheelOdometry(wheel_diameter_m=diameter)
