from __future__ import annotations

import argparse
import signal
import time

from hardware.devices.led_bank import LedBank
from hardware.hal import create_gpio_backend

# Same physical header positions on both boards:
# Raspberry Pi uses BCM numbering; Jetson uses BOARD numbering.
DEFAULT_PINS = {
    "raspberry_pi": (22, 6),
    "jetson": (7, 29),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Two active-high LED test")
    parser.add_argument("--platform", required=True, choices=sorted(DEFAULT_PINS))
    parser.add_argument("--led1-pin", type=int)
    parser.add_argument("--led2-pin", type=int)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--cycles", type=int, default=0, help="0 means repeat forever")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    if args.cycles < 0:
        parser.error("--cycles must be non-negative")

    default_led1, default_led2 = DEFAULT_PINS[args.platform]
    led1_pin = args.led1_pin if args.led1_pin is not None else default_led1
    led2_pin = args.led2_pin if args.led2_pin is not None else default_led2
    running = True

    def stop(_signal, _frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    gpio = create_gpio_backend(args.platform)
    leds = LedBank((gpio.output(led1_pin), gpio.output(led2_pin)))
    numbering = "BCM" if args.platform == "raspberry_pi" else "BOARD"
    print(f"LED1={numbering} {led1_pin}, LED2={numbering} {led2_pin}")
    print("LED1과 LED2가 번갈아 켜집니다. 종료는 Ctrl+C")
    completed = 0
    try:
        while running and (args.cycles == 0 or completed < args.cycles):
            leds.set(0, True)
            leds.set(1, False)
            print("LED1 ON / LED2 OFF")
            time.sleep(args.interval)
            if not running:
                break
            leds.set(0, False)
            leds.set(1, True)
            print("LED1 OFF / LED2 ON")
            time.sleep(args.interval)
            completed += 1
    finally:
        leds.close()
        gpio.close()
        print("두 LED OFF / 종료")


if __name__ == "__main__":
    main()
