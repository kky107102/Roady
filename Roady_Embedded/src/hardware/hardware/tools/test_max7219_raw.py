#!/usr/bin/env python3
"""Minimal MAX7219 SPI test without luma.led_matrix."""

import argparse
import time


def write_all(spi, cascaded: int, register: int, value: int) -> None:
    """Write the same register/value pair to every chained MAX7219."""
    spi.xfer2([register, value] * cascaded)


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal raw MAX7219 test")
    parser.add_argument("--bus", type=int, default=0)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--cascaded", type=int, default=4)
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()

    try:
        import spidev
    except ImportError as exc:
        raise SystemExit(
            "spidev가 없습니다: sudo apt install python3-spidev"
        ) from exc

    spi = spidev.SpiDev()
    spi.open(args.bus, args.device)
    spi.max_speed_hz = 500_000
    spi.mode = 0

    print(f"/dev/spidev{args.bus}.{args.device}, MAX7219 {args.cascaded}개")
    print(f"각 8x8 블록에 픽셀 1개를 {args.seconds:g}초 동안 켭니다.")

    try:
        # Low-current initialization: no decode, minimum intensity, 8 rows.
        write_all(spi, args.cascaded, 0x0F, 0x00)
        write_all(spi, args.cascaded, 0x09, 0x00)
        write_all(spi, args.cascaded, 0x0A, 0x00)
        write_all(spi, args.cascaded, 0x0B, 0x07)
        write_all(spi, args.cascaded, 0x0C, 0x01)
        for row in range(1, 9):
            write_all(spi, args.cascaded, row, 0x00)
        # One pixel in row 1 on every chained driver.
        write_all(spi, args.cascaded, 0x01, 0x01)
        time.sleep(args.seconds)
    finally:
        for row in range(1, 9):
            write_all(spi, args.cascaded, row, 0x00)
        write_all(spi, args.cascaded, 0x0C, 0x00)
        spi.close()
        print("테스트 종료")


if __name__ == "__main__":
    main()
