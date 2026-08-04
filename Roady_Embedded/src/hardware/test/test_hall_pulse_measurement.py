from hardware.devices.hall_sensor import HallState
from hardware.tools.measure_hall_pulses import PulseMeasurement


def state(detected: bool, changed: bool = True) -> HallState:
    return HallState(
        detected=detected,
        changed=changed,
        electrical_high=not detected,
    )


def test_initially_attached_magnet_is_not_counted():
    measurement = PulseMeasurement(target_count=5)

    assert not measurement.update(state(True))
    assert not measurement.armed
    assert measurement.pulse_count == 0


def test_counts_five_entries_only_after_initial_release():
    measurement = PulseMeasurement(target_count=5)
    measurement.update(state(True))
    measurement.update(state(False))
    assert measurement.armed

    for expected in range(1, 5):
        assert not measurement.update(state(True))
        assert measurement.pulse_count == expected
        assert not measurement.update(state(False))

    assert measurement.update(state(True))
    assert measurement.pulse_count == 5


def test_unchanged_detected_state_is_not_counted_repeatedly():
    measurement = PulseMeasurement(target_count=1)
    measurement.update(state(False))

    assert not measurement.update(state(True, changed=False))
    assert measurement.pulse_count == 0
    assert measurement.update(state(True, changed=True))
