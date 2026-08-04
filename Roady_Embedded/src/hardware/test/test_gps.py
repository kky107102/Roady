import pytest

from hardware.devices.gps import parse_nmea
from hardware.devices.location_estimator import LocationEstimator, offset_longitude
from hardware.devices.wheel_odometry import WheelOdometry


def with_checksum(payload):
    checksum = 0
    for character in payload:
        checksum ^= ord(character)
    return f"${payload}*{checksum:02X}"


def test_parse_valid_gga():
    reading = parse_nmea(with_checksum(
        "GNGGA,123519.00,3723.2475,N,12701.2345,E,1,08,0.9,42.3,M,0.0,M,,"
    ))
    assert reading is not None and reading.valid
    assert reading.fix_quality == 1 and reading.satellites == 8
    assert abs(reading.latitude - 37.3874583333) < 1e-8
    assert abs(reading.longitude - 127.020575) < 1e-8


def test_parse_no_fix_rmc():
    reading = parse_nmea(with_checksum("GNRMC,123519.00,V,,,,,,,300726,,,N"))
    assert reading is not None
    assert reading.sentence_type == "RMC" and not reading.valid
    assert reading.latitude is None and reading.longitude is None


def test_reject_bad_checksum():
    assert parse_nmea("$GNGGA,,,,,,0,00,25.5,,,,,,*00") is None


def test_location_uses_hall_distance_from_virtual_origin():
    estimator = LocationEstimator(37.5, 127.0)
    estimator.update_distance(100.0)

    location = estimator.location()

    assert location.source == "wheel"
    assert location.latitude == 37.5
    assert location.longitude > 127.0


def test_indoor_virtual_map_scales_physical_wheel_distance_only_for_display():
    estimator = LocationEstimator(
        37.5012748,
        127.039625,
        wheel_distance_scale=24.0368829327,
    )
    estimator.update_distance(0.367)

    location = estimator.location()
    expected = offset_longitude(37.5012748, 127.039625, 8.821536036299)

    assert location.latitude == expected[0]
    assert location.longitude == pytest.approx(expected[1])


def test_one_hall_pulse_becomes_one_demo_longitude_step():
    odometry = WheelOdometry(distance_per_pulse_m=0.367)
    estimator = LocationEstimator(
        37.5012748,
        127.039625,
        wheel_distance_scale=24.0368829327,
    )

    wheel = odometry.record_pulse()
    estimator.update_distance(wheel.distance_m)
    location = estimator.location()

    assert wheel.distance_m == pytest.approx(0.367)
    assert location.latitude == pytest.approx(37.5012748)
    assert location.longitude == pytest.approx(127.039725, abs=1e-10)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_indoor_mode_ignores_gps_updates():
    estimator = LocationEstimator(37.5, 127.0, use_gps=False)
    estimator.update_gps(37.6, 127.1)

    assert estimator.location().source == "wheel"
    assert estimator.location().latitude == 37.5
    assert estimator.location().longitude == 127.0


def test_outdoor_mode_uses_recent_gps_then_wheel_distance():
    clock = FakeClock()
    estimator = LocationEstimator(
        37.5, 127.0, use_gps=True, gps_timeout_sec=3.0, clock=clock
    )
    estimator.update_distance(10.0)
    estimator.update_gps(37.6, 127.1)

    assert estimator.location().source == "gps"
    clock.now = 3.1
    estimator.update_distance(110.0)
    fallback = estimator.location()

    assert fallback.source == "wheel"
    assert abs(fallback.latitude - 37.6) < 1e-6
    assert fallback.longitude > 127.1
