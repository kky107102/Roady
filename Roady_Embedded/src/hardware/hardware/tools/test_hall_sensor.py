from __future__ import annotations

import argparse
import signal
import time

from hardware.devices.hall_sensor import HallSensor
from hardware.hal import create_gpio_backend

DEFAULT_PINS = {"raspberry_pi": 13, "jetson": 33}


def main() -> None:
    parser = argparse.ArgumentParser(description="KY-003 digital Hall sensor test")
    parser.add_argument("--platform", required=True, choices=sorted(DEFAULT_PINS))
    parser.add_argument("--pin", type=int)
    parser.add_argument("--debounce", type=float, default=0.02)
    parser.add_argument("--raw", action="store_true")
    args = parser.parse_args()

    pin = args.pin if args.pin is not None else DEFAULT_PINS[args.platform]
    # Pi uses its 3.3 V internal pull-up. For Jetson use an external 10 kOhm
    # pull-up from signal to 3.3 V, matching the existing input wiring policy.
    pull_up = True if args.platform == "raspberry_pi" else None
    running = True

    def stop(_signal, _frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    gpio = create_gpio_backend(args.platform)
    sensor = HallSensor(
        gpio.input(pin, pull_up=pull_up),
        active_low=True,
        debounce_sec=args.debounce,
    )
    numbering = "BCM" if args.platform == "raspberry_pi" else "BOARD"
    print(f"KY-003 테스트: {numbering} pin {pin}")
    print("자석의 한쪽 극을 센서에 가까이 대세요. 종료는 Ctrl+C")
    previous_raw = None
    try:
        while running:
            state = sensor.poll()
            if state.changed:
                print("MAGNET DETECTED" if state.detected else "MAGNET RELEASED")
            if args.raw and state.electrical_high != previous_raw:
                print(f"RAW={'HIGH' if state.electrical_high else 'LOW'}")
                previous_raw = state.electrical_high
            time.sleep(0.01)
    finally:
        sensor.close()
        gpio.close()
        print("종료")


if __name__ == "__main__":
    main()
