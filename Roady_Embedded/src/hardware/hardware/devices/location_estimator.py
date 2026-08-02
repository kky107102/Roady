from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Optional


EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class EstimatedLocation:
    latitude: float
    longitude: float
    source: str


class LocationEstimator:
    """Select recent GPS or estimate a location from cumulative wheel distance."""

    def __init__(
        self,
        virtual_latitude: float,
        virtual_longitude: float,
        *,
        heading_deg: float = 90.0,
        gps_timeout_sec: float = 3.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not -90.0 < virtual_latitude < 90.0:
            raise ValueError("virtual_latitude must be between -90 and 90")
        if not -180.0 <= virtual_longitude <= 180.0:
            raise ValueError("virtual_longitude must be between -180 and 180")
        if gps_timeout_sec < 0.0:
            raise ValueError("gps_timeout_sec must be non-negative")

        self._virtual_origin = (virtual_latitude, virtual_longitude)
        self._heading_deg = heading_deg
        self._gps_timeout_sec = gps_timeout_sec
        self._clock = clock
        self._distance_m = 0.0
        self._gps_location: Optional[tuple[float, float]] = None
        self._gps_time: Optional[float] = None
        self._gps_distance_m = 0.0

    def update_distance(self, distance_m: float) -> None:
        if not math.isfinite(distance_m) or distance_m < 0.0:
            raise ValueError("distance_m must be a finite non-negative value")
        self._distance_m = distance_m

    def update_gps(self, latitude: float, longitude: float) -> None:
        if not math.isfinite(latitude) or not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if not math.isfinite(longitude) or not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        self._gps_location = (latitude, longitude)
        self._gps_time = self._clock()
        self._gps_distance_m = self._distance_m

    def location(self) -> EstimatedLocation:
        now = self._clock()
        if (
            self._gps_location is not None
            and self._gps_time is not None
            and now - self._gps_time <= self._gps_timeout_sec
        ):
            return EstimatedLocation(*self._gps_location, source="gps")

        origin = self._gps_location or self._virtual_origin
        distance_offset = self._distance_m - (
            self._gps_distance_m if self._gps_location is not None else 0.0
        )
        latitude, longitude = offset_coordinate(
            origin[0],
            origin[1],
            distance_offset,
            self._heading_deg,
        )
        return EstimatedLocation(latitude, longitude, source="wheel")


def offset_coordinate(
    latitude: float,
    longitude: float,
    distance_m: float,
    heading_deg: float,
) -> tuple[float, float]:
    """Move a WGS84 coordinate along a great-circle bearing."""
    angular_distance = distance_m / EARTH_RADIUS_M
    bearing = math.radians(heading_deg)
    latitude_1 = math.radians(latitude)
    longitude_1 = math.radians(longitude)

    latitude_2 = math.asin(
        math.sin(latitude_1) * math.cos(angular_distance)
        + math.cos(latitude_1) * math.sin(angular_distance) * math.cos(bearing)
    )
    longitude_2 = longitude_1 + math.atan2(
        math.sin(bearing) * math.sin(angular_distance) * math.cos(latitude_1),
        math.cos(angular_distance) - math.sin(latitude_1) * math.sin(latitude_2),
    )
    normalized_longitude = (math.degrees(longitude_2) + 540.0) % 360.0 - 180.0
    return math.degrees(latitude_2), normalized_longitude
