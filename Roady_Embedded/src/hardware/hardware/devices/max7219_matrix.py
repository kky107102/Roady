from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from hardware.hal.display import DotMatrixDisplay


@dataclass(frozen=True)
class Max7219Config:
    port: int = 0
    device: int = 0
    cascaded: int = 4
    bus_speed_hz: int = 500_000
    block_orientation: int = -90
    rotate: int = 0
    blocks_reversed: bool = False
    contrast: int = 5

    def __post_init__(self) -> None:
        if self.cascaded <= 0:
            raise ValueError("cascaded must be positive")
        if self.bus_speed_hz <= 0:
            raise ValueError("bus_speed_hz must be positive")
        if self.rotate not in {0, 1, 2, 3}:
            raise ValueError("rotate must be 0, 1, 2, or 3")
        if not 0 <= self.contrast <= 255:
            raise ValueError("contrast must be between 0 and 255")


class Max7219Matrix(DotMatrixDisplay):
    """MAX7219 adapter backed by luma.led_matrix and Linux spidev."""

    def __init__(self, config: Max7219Config = Max7219Config()) -> None:
        try:
            from luma.core.interface.serial import noop, spi
            from luma.core.render import canvas
            from luma.led_matrix.device import max7219
        except ImportError as exc:
            raise RuntimeError(
                "MAX7219 requires luma.led_matrix: "
                "python3 -m pip install luma.led_matrix"
            ) from exc

        self.config = config
        self._canvas = canvas
        self._serial = spi(
            port=config.port,
            device=config.device,
            gpio=noop(),
            bus_speed_hz=config.bus_speed_hz,
        )
        self._device = max7219(
            self._serial,
            cascaded=config.cascaded,
            block_orientation=config.block_orientation,
            rotate=config.rotate,
            blocks_arranged_in_reverse_order=config.blocks_reversed,
        )
        self._device.contrast(config.contrast)
        self._closed = False

    @property
    def width(self) -> int:
        return self._device.width

    @property
    def height(self) -> int:
        return self._device.height

    def clear(self) -> None:
        self._device.clear()

    def fill(self) -> None:
        with self._canvas(self._device) as draw:
            draw.rectangle(self._device.bounding_box, outline="white", fill="white")

    def vertical_line(self, x: int) -> None:
        self._check_point(x, 0)
        with self._canvas(self._device) as draw:
            draw.line((x, 0, x, self.height - 1), fill="white")

    def horizontal_line(self, y: int) -> None:
        self._check_point(0, y)
        with self._canvas(self._device) as draw:
            draw.line((0, y, self.width - 1, y), fill="white")

    def pixel(self, x: int, y: int) -> None:
        self._check_point(x, y)
        with self._canvas(self._device) as draw:
            draw.point((x, y), fill="white")

    def pixels(self, points: Iterable[tuple[int, int]]) -> None:
        points = tuple(points)
        for x, y in points:
            self._check_point(x, y)
        with self._canvas(self._device) as draw:
            draw.point(points, fill="white")

    def block_boundaries(self, block_width: int = 8) -> None:
        if block_width <= 0 or self.width % block_width:
            raise ValueError("block_width must divide the display width")
        with self._canvas(self._device) as draw:
            for left in range(0, self.width, block_width):
                draw.rectangle(
                    (left, 0, left + block_width - 1, self.height - 1),
                    outline="white",
                    fill=None,
                )

    def close(self) -> None:
        if self._closed:
            return
        self.clear()
        cleanup = getattr(self._device, "cleanup", None)
        if cleanup is not None:
            cleanup()
        self._closed = True

    def _check_point(self, x: int, y: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"pixel ({x}, {y}) is outside {self.width}x{self.height}")
