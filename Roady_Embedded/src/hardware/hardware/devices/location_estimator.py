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
    """Estimate a location from wheel distance, optionally preferring recent GPS."""

    def __init__(
        self,
        virtual_latitude: float,
        virtual_longitude: float,
        *,
        use_gps: bool = False,
        gps_timeout_sec: float = 3.0,
        wheel_distance_scale: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not -90.0 < virtual_latitude < 90.0:
            raise ValueError("virtual_latitude must be between -90 and 90")
        if not -180.0 <= virtual_longitude <= 180.0:
            raise ValueError("virtual_longitude must be between -180 and 180")
        if gps_timeout_sec < 0.0:
            raise ValueError("gps_timeout_sec must be non-negative")
        if not math.isfinite(wheel_distance_scale) or wheel_distance_scale <= 0.0:
            raise ValueError("wheel_distance_scale must be a finite positive value")
        self._virtual_origin = (virtual_latitude, virtual_longitude)
        self._use_gps = use_gps
        self._gps_timeout_sec = gps_timeout_sec
        self._wheel_distance_scale = wheel_distance_scale
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
        if not self._use_gps:
            return
        if not math.isfinite(latitude) or not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if not math.isfinite(longitude) or not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        self._gps_location = (latitude, longitude)
        self._gps_time = self._clock()
        self._gps_distance_m = self._distance_m

    def location(self) -> EstimatedLocation:
        if (
            self._use_gps
            and self._gps_location is not None
            and self._gps_time is not None
            and self._clock() - self._gps_time <= self._gps_timeout_sec
        ):
            return EstimatedLocation(*self._gps_location, source="gps")

        origin = self._gps_location or self._virtual_origin
        physical_distance_offset = self._distance_m - (
            self._gps_distance_m if self._gps_location is not None else 0.0
        )
        distance_offset = physical_distance_offset * self._wheel_distance_scale
        latitude, longitude = offset_longitude(
            origin[0],
            origin[1],
            distance_offset,
        )
        return EstimatedLocation(latitude, longitude, source="wheel")


def offset_longitude(
    latitude: float,
    longitude: float,
    distance_m: float,
) -> tuple[float, float]:
    """Add wheel travel to longitude while keeping latitude unchanged."""
    parallel_radius = EARTH_RADIUS_M * math.cos(math.radians(latitude))
    if math.isclose(parallel_radius, 0.0, abs_tol=1e-9):
        raise ValueError("longitude offset is undefined at the poles")
    longitude_offset_deg = math.degrees(distance_m / parallel_radius)
    normalized_longitude = (longitude + longitude_offset_deg + 540.0) % 360.0 - 180.0
    return latitude, normalized_longitude
