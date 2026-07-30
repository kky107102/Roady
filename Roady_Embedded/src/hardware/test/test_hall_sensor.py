from hardware.devices.hall_sensor import HallSensor


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
