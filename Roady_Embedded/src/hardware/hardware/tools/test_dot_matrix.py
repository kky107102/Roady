from __future__ import annotations

import argparse
import signal
import time
from typing import Callable

from hardware.devices.max7219_matrix import Max7219Config, Max7219Matrix
from hardware.hal.display import DotMatrixDisplay


def run_test_sequence(
    display: DotMatrixDisplay,
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    print("1. 전체 LED 테스트")
    display.fill()
    sleep(1.0)
    display.clear()

    print("2. 세로줄 테스트")
    for x in range(display.width):
        display.vertical_line(x)
        sleep(0.05)

    print("3. 가로줄 테스트")
    for y in range(display.height):
        display.horizontal_line(y)
        sleep(0.15)

    print("4. 픽셀 테스트")
    for y in range(display.height):
        for x in range(display.width):
            display.pixel(x, y)
            sleep(0.01)

    print("5. 8x8 블록 경계 테스트")
    display.block_boundaries(8)
    sleep(2.0)
    display.clear()


def main() -> None:
    parser = argparse.ArgumentParser(description="MAX7219 8x32 test")
    parser.add_argument("--port", type=int, default=0, help="SPI bus number")
    parser.add_argument("--device", type=int, default=0, help="SPI CE number")
    parser.add_argument("--cascaded", type=int, default=4)
    parser.add_argument("--speed", type=int, default=500_000)
    parser.add_argument("--contrast", type=int, default=5)
    parser.add_argument("--orientation", type=int, default=-90)
    parser.add_argument("--rotate", type=int, choices=range(4), default=0)
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    running = True

    def stop(_signal, _frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    display = Max7219Matrix(
        Max7219Config(
            port=args.port,
            device=args.device,
            cascaded=args.cascaded,
            bus_speed_hz=args.speed,
            block_orientation=args.orientation,
            rotate=args.rotate,
            blocks_reversed=args.reverse,
            contrast=args.contrast,
        )
    )
    print(f"디스플레이 크기: {display.width} x {display.height}")
    print("Ctrl+C를 누르면 종료됩니다.")
    try:
        while running:
            run_test_sequence(display)
            if args.once:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n테스트를 종료합니다.")
    finally:
        display.close()


if __name__ == "__main__":
    main()
