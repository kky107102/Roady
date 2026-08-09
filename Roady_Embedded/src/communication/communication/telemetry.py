from __future__ import annotations

import math
from datetime import datetime
from typing import Any


class MockTelemetry:
    """Produces test telemetry until real sensors are connected."""

    def __init__(
        self,
        latitude: float = 37.501361,
        longitude: float = 127.039500,
        latitude_step: float = -0.00003,
        longitude_step: float = -0.0001,
    ) -> None:
        self._latitude = latitude
        self._longitude = longitude
        self._latitude_step = latitude_step
        self._longitude_step = longitude_step
        self._sample_number = 0

    def next_payload(self) -> dict[str, Any]:
        latitude = self._latitude + self._latitude_step * self._sample_number
        longitude = self._longitude + self._longitude_step * self._sample_number
        self._sample_number += 1

        return {
            "latitude": round(latitude, 7),
            "longitude": round(longitude, 7),
            "batteryLevel": 90,
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
        self._latitude_step = 0.0
        self._longitude_step = 0.0
        self._sample_number = 0
