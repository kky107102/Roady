from __future__ import annotations

import argparse
import signal
import time

from hardware.devices.gps import GpsReceiver
from hardware.hal.uart import LinuxUart


def main() -> None:
    parser = argparse.ArgumentParser(description="UART NMEA GPS test")
    parser.add_argument("--port", default="/dev/ttyTHS1")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--raw", action="store_true", help="print every NMEA sentence")
    args = parser.parse_args()

    running = True

    def stop(_signal, _frame) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    receiver = GpsReceiver(LinuxUart(args.port, args.baud))
    print(f"GPS 테스트: {args.port} @ {args.baud} baud")
    print("위성 고정 전에도 NMEA 수신 여부를 확인합니다. 종료는 Ctrl+C")
    received = 0
    last_status = 0.0
    try:
        while running:
            sentence, reading = receiver.read(args.timeout)
            if not sentence:
                now = time.monotonic()
                if now - last_status >= 5.0:
                    print("NMEA 대기 중...")
                    last_status = now
                continue
            received += 1
            if args.raw:
                print(sentence)
            if reading is None:
                continue
            if reading.valid:
                print(
                    f"FIX {reading.sentence_type}: "
                    f"lat={reading.latitude:.7f}, lon={reading.longitude:.7f}, "
                    f"sat={reading.satellites}, alt={reading.altitude_m}m"
                )
            elif reading.sentence_type in {"GGA", "RMC"}:
                print(
                    f"NO FIX ({reading.sentence_type}) / "
                    f"NMEA {received}문장 수신"
                )
    finally:
        receiver.close()
        print(f"종료: NMEA {received}문장 수신")


if __name__ == "__main__":
    main()
