from hardware.devices.gps import parse_nmea


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
