from __future__ import annotations

import argparse
import signal
import time
from dataclasses import dataclass

from hardware.devices.hall_sensor import HallSensor, HallState
from hardware.hal import create_gpio_backend


DEFAULT_PINS = {"raspberry_pi": 13, "jetson": 33}


@dataclass
class PulseMeasurement:
    """Count magnet entries after the initially attached magnet is released."""

    target_count: int = 5
    armed: bool = False
    pulse_count: int = 0

    def __post_init__(self) -> None:
        if self.target_count < 1:
            raise ValueError("target_count must be positive")

    def update(self, state: HallState) -> bool:
        if not state.changed:
            return False
        if not self.armed:
            # The test starts with the magnet attached. Do not count that
            # initial state; arm only after the magnet has left the sensor.
            if not state.detected:
                self.armed = True
            return False
        if state.detected:
            self.pulse_count += 1
        return self.pulse_count >= self.target_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count Hall pulses for distance-per-pulse calibration"
    )
    parser.add_argument("--platform", required=True, choices=sorted(DEFAULT_PINS))
    parser.add_argument("--pin", type=int)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--debounce", type=float, default=0.02)
    parser.add_argument("--poll-interval", type=float, default=0.005)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    if args.poll_interval <= 0.0:
        parser.error("--poll-interval must be positive")

    pin = args.pin if args.pin is not None else DEFAULT_PINS[args.platform]
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
    measurement = PulseMeasurement(target_count=args.count)
    numbering = "BCM" if args.platform == "raspberry_pi" else "BOARD"

    print(f"홀센서 거리 측정: {numbering} pin {pin}, 목표 {args.count}펄스")
    if args.platform == "jetson":
        print("VCC=3.3 V / SIGNAL-3.3 V 사이 외부 1 kOhm pull-up 필요")
    print("1) 자석이 센서에 붙어 있는 상태에서 프로그램을 시작하세요.")
    print("2) 차량을 끌면 최초 자석 이탈 후 카운팅을 시작합니다.")
    print(f"3) {args.count}번째 재감지 순간 프로그램이 종료됩니다.")

    try:
        while running:
            state = sensor.poll()
            was_armed = measurement.armed
            done = measurement.update(state)
            if not was_armed and measurement.armed:
                print("ARMED: 초기 자석이 이탈했습니다. 지금부터 펄스를 셉니다.")
            elif state.changed and state.detected and measurement.armed:
                print(f"PULSE {measurement.pulse_count}/{measurement.target_count}")
            if done:
                print(
                    f"STOP: 목표 {measurement.target_count}펄스에 도달했습니다. "
                    "차체 이동을 멈추세요."
                )
                break
            time.sleep(args.poll_interval)
    finally:
        sensor.close()
        gpio.close()
        print(f"측정 종료: 총 {measurement.pulse_count}펄스")


if __name__ == "__main__":
    main()
