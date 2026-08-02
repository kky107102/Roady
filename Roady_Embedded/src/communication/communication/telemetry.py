from __future__ import annotations

import math
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

    def set_location(self, latitude: float, longitude: float) -> None:
        """Use a live location and stop advancing the mock coordinate."""
        if not math.isfinite(latitude) or not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if not math.isfinite(longitude) or not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        self._latitude = latitude
        self._longitude = longitude
        self._longitude_step = 0.0
        self._sample_number = 0
