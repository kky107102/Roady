from hardware.devices.push_lock import PushLock


class FakeInput:
    def __init__(self, level=True):
        self.level, self.closed = level, False
    def read(self): return self.level
    def close(self): self.closed = True


class FakeOutput:
    def __init__(self):
        self.values, self.closed = [], False
    def write(self, value): self.values.append(value)
    def close(self): self.closed = True


class FakeClock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now
    def advance(self, seconds): self.now += seconds


def test_active_low_switch_is_debounced_and_drives_led():
    switch, led, clock = FakeInput(True), FakeOutput(), FakeClock()
    lock = PushLock(switch, led, debounce_sec=0.05, clock=clock)
    assert lock.poll().changed is False
    clock.advance(0.05)
    assert lock.poll().locked is False
    assert led.values == [False]
    switch.level = False
    assert lock.poll().changed is False
    clock.advance(0.05)
    state = lock.poll()
    assert state.changed is True and state.locked is True
    assert led.values == [False, True]


def test_close_is_idempotent_and_safe():
    switch, led = FakeInput(), FakeOutput()
    lock = PushLock(switch, led, debounce_sec=0)
    lock.poll()
    lock.close()
    lock.close()
    assert led.values[-1] is False
    assert switch.closed and led.closed


def test_active_low_indicator_inverts_electrical_output():
    switch, led, clock = FakeInput(True), FakeOutput(), FakeClock()
    lock = PushLock(
        switch,
        led,
        indicator_active_low=True,
        debounce_sec=0,
        clock=clock,
    )
    assert lock.poll().locked is False
    assert led.values == [True]
    switch.level = False
    assert lock.poll().locked is True
    assert led.values == [True, False]
    lock.close()
    assert led.values[-1] is True
