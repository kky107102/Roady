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
