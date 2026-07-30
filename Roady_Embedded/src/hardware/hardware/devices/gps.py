from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Optional

from hardware.hal.uart import UartPort


@dataclass(frozen=True)
class GpsReading:
    sentence_type: str
    valid: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    utc_time: Optional[time] = None
    satellites: Optional[int] = None
    fix_quality: Optional[int] = None
    altitude_m: Optional[float] = None
    speed_knots: Optional[float] = None


class GpsReceiver:
    """Reads NMEA 0183 sentences from a UART-connected GNSS receiver."""

    def __init__(self, uart: UartPort) -> None:
        self._uart = uart

    def read(self, timeout: float = 1.0) -> tuple[str, Optional[GpsReading]]:
        raw = self._uart.readline(timeout)
        if not raw:
            return "", None
        sentence = raw.decode("ascii", errors="replace").strip()
        return sentence, parse_nmea(sentence)

    def close(self) -> None:
        self._uart.close()


def parse_nmea(sentence: str) -> Optional[GpsReading]:
    if not sentence.startswith("$") or not _checksum_valid(sentence):
        return None
    payload = sentence[1:].split("*", 1)[0]
    fields = payload.split(",")
    if not fields or len(fields[0]) < 3:
        return None
    sentence_type = fields[0][-3:]
    try:
        if sentence_type == "GGA" and len(fields) >= 10:
            quality = _integer(fields[6]) or 0
            return GpsReading(
                sentence_type="GGA",
                valid=quality > 0,
                utc_time=_utc(fields[1]),
                latitude=_coordinate(fields[2], fields[3]),
                longitude=_coordinate(fields[4], fields[5]),
                fix_quality=quality,
                satellites=_integer(fields[7]),
                altitude_m=_number(fields[9]),
            )
        if sentence_type == "RMC" and len(fields) >= 8:
            return GpsReading(
                sentence_type="RMC",
                valid=fields[2] == "A",
                utc_time=_utc(fields[1]),
                latitude=_coordinate(fields[3], fields[4]),
                longitude=_coordinate(fields[5], fields[6]),
                speed_knots=_number(fields[7]),
            )
    except (ValueError, IndexError):
        return None
    return None


def _checksum_valid(sentence: str) -> bool:
    if "*" not in sentence:
        return False
    payload, expected = sentence[1:].split("*", 1)
    expected = expected[:2]
    if len(expected) != 2:
        return False
    checksum = 0
    for character in payload:
        checksum ^= ord(character)
    try:
        return checksum == int(expected, 16)
    except ValueError:
        return False


def _coordinate(value: str, hemisphere: str) -> Optional[float]:
    if not value or hemisphere not in {"N", "S", "E", "W"}:
        return None
    degree_digits = 2 if hemisphere in {"N", "S"} else 3
    degrees = float(value[:degree_digits])
    minutes = float(value[degree_digits:])
    result = degrees + minutes / 60.0
    return -result if hemisphere in {"S", "W"} else result


def _utc(value: str) -> Optional[time]:
    if len(value) < 6:
        return None
    seconds = float(value[4:])
    whole_seconds = int(seconds)
    microseconds = round((seconds - whole_seconds) * 1_000_000)
    return time(int(value[:2]), int(value[2:4]), whole_seconds, microseconds)


def _integer(value: str) -> Optional[int]:
    return int(value) if value else None


def _number(value: str) -> Optional[float]:
    return float(value) if value else None
