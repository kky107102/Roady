from __future__ import annotations

import argparse
import signal
import time

from hardware.devices.push_lock import PushLock
from hardware.hal import create_gpio_backend

DEFAULT_PINS = {"raspberry_pi": (17, 18), "jetson": (31, 15)}


def main() -> None:
    parser = argparse.ArgumentParser(description="R16-503 push-lock and LED test")
    parser.add_argument("--platform", required=True, choices=sorted(DEFAULT_PINS))
    parser.add_argument("--button-pin", type=int)
    parser.add_argument("--led-pin", type=int)
    parser.add_argument("--debounce", type=float, default=0.05)
    args = parser.parse_args()
    default_button, default_led = DEFAULT_PINS[args.platform]
    button_pin = args.button_pin if args.button_pin is not None else default_button
    led_pin = args.led_pin if args.led_pin is not None else default_led
    # The verified Jetson wiring uses a pull-down: LOW=pressed/locked.
    pull_up = True if args.platform == "raspberry_pi" else False
    running = True

    def stop(_signal, _frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    gpio = create_gpio_backend(args.platform)
    lock = PushLock(
        gpio.input(button_pin, pull_up=pull_up),
        gpio.output(led_pin, initial=False),
        indicator_active_low=False,
        debounce_sec=args.debounce,
    )
    print("===== LOCK 버튼 테스트 =====")
    print(f"platform={args.platform}, button={button_pin}, led={led_pin}")
    print("LOCK ON이면 LED ON, LOCK OFF이면 LED OFF / 종료는 Ctrl+C")
    try:
        while running:
            state = lock.poll()
            if state.changed:
                print("LOCK ON" if state.locked else "LOCK OFF")
            time.sleep(0.02)
    finally:
        lock.close()
        gpio.close()
        print("종료")


if __name__ == "__main__":
    main()
