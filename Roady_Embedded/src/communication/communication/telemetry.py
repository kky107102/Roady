from __future__ import annotations

import random
from datetime import datetime
from typing import Any


class MockTelemetry:
    """Produces test telemetry until real sensors are connected."""

    def __init__(
        self, latitude: float, longitude: float, longitude_step: float = 0.0001
    ) -> None:
        self._latitude = latitude
        self._longitude = longitude
        self._longitude_step = longitude_step
        self._sample_number = 0

    def next_payload(self) -> dict[str, Any]:
        longitude = self._longitude + self._longitude_step * self._sample_number
        battery_level = random.randint(20, 100)
        self._sample_number += 1

        return {
            "latitude": self._latitude,
            "longitude": round(longitude, 7),
            "batteryLevel": battery_level,
            "operationStatus": "MOVING",
            "connectionStatus": "CONNECTED",
            "errorCode": None,
            "errorMessage": None,
            "recordedAt": datetime.now().isoformat(timespec="seconds"),
        }
