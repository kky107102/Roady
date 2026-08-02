from hardware.devices.max7219_matrix import Max7219Config
from hardware.tools.test_dot_matrix import run_test_sequence


class FakeDisplay:
    width, height = 16, 8

    def __init__(self):
        self.calls = []

    def clear(self): self.calls.append(("clear",))
    def fill(self): self.calls.append(("fill",))
    def vertical_line(self, x): self.calls.append(("column", x))
    def horizontal_line(self, y): self.calls.append(("row", y))
    def pixel(self, x, y): self.calls.append(("pixel", x, y))
    def block_boundaries(self, width=8): self.calls.append(("blocks", width))
    def close(self): self.calls.append(("close",))


def test_default_config_matches_tested_jetson_wiring():
    config = Max7219Config()
    assert (config.port, config.device, config.cascaded) == (0, 0, 4)
    assert config.bus_speed_hz == 500_000
    assert config.block_orientation == -90
    assert config.contrast == 5


def test_sequence_covers_entire_display():
    display = FakeDisplay()
    delays = []
    run_test_sequence(display, sleep=delays.append)
    assert sum(call[0] == "column" for call in display.calls) == 16
    assert sum(call[0] == "row" for call in display.calls) == 8
    assert sum(call[0] == "pixel" for call in display.calls) == 128
    assert ("blocks", 8) in display.calls
    assert display.calls[-1] == ("clear",)


def test_invalid_config_is_rejected():
    try:
        Max7219Config(cascaded=0)
    except ValueError:
        pass
    else:
        raise AssertionError("cascaded=0 must fail")
