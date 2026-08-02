from hardware.devices.gps import parse_nmea
from hardware.devices.location_estimator import LocationEstimator


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


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_location_uses_gps_until_it_becomes_stale():
    clock = FakeClock()
    estimator = LocationEstimator(
        37.5, 127.0, gps_timeout_sec=3.0, clock=clock
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


def test_location_uses_virtual_origin_before_first_gps_fix():
    estimator = LocationEstimator(37.5, 127.0, heading_deg=0.0)
    estimator.update_distance(100.0)

    location = estimator.location()

    assert location.source == "wheel"
    assert location.latitude > 37.5
    assert abs(location.longitude - 127.0) < 1e-9
