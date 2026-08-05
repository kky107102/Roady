from __future__ import annotations

from collections.abc import Iterable

from hardware.hal.display import DotMatrixDisplay


# A 7-row by 8-column outline for matrices whose final row is obscured after
# assembly.  Keeping an odd number of rows makes the circle vertically
# symmetric within the seven visible rows.
EYE_ROWS = (
    "00111100",
    "01000010",
    "10000001",
    "10000001",
    "10000001",
    "01000010",
    "00111100",
)


def eye_pixels(
    block_numbers: Iterable[int] = (1, 4),
    *,
    block_width: int = 8,
) -> tuple[tuple[int, int], ...]:
    """Return eye pixels for one-based dot-matrix block numbers."""
    if block_width != len(EYE_ROWS[0]):
        raise ValueError("the eye pattern requires 8-pixel-wide blocks")

    points: list[tuple[int, int]] = []
    for block_number in block_numbers:
        if block_number <= 0:
            raise ValueError("block numbers must be positive")
        x_offset = (block_number - 1) * block_width
        points.extend(
            (x_offset + x, y)
            for y, row in enumerate(EYE_ROWS)
            for x, value in enumerate(row)
            if value == "1"
        )
    return tuple(points)


def show_running_eyes(display: DotMatrixDisplay) -> None:
    """Show fixed eyes in the first and fourth 8x8 blocks."""
    if display.width < 32 or display.height < 8:
        raise ValueError("running eyes require a display of at least 32x8 pixels")
    display.pixels(eye_pixels())
