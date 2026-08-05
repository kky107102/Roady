from datetime import datetime

from communication.telemetry import MockTelemetry


def test_mock_telemetry_matches_server_contract():
    payload = MockTelemetry().next_payload()

    assert set(payload) == {
        "latitude",
        "longitude",
        "batteryLevel",
        "operationStatus",
        "connectionStatus",
        "errorCode",
        "errorMessage",
        "recordedAt",
    }
    assert -90 <= payload["latitude"] <= 90
    assert -180 <= payload["longitude"] <= 180
    assert 0 <= payload["batteryLevel"] <= 100
    assert payload["operationStatus"] in {
        "STANDBY",
        "MOVING",
        "INSPECTING",
        "CHARGING",
        "STOPPED",
        "ERROR",
    }
    assert payload["connectionStatus"] == "CONNECTED"
    assert payload["errorCode"] is None
    assert payload["errorMessage"] is None
    datetime.fromisoformat(payload["recordedAt"])


def test_each_payload_changes_both_coordinates_and_keeps_battery_at_90():
    mock = MockTelemetry()

    first = mock.next_payload()
    second = mock.next_payload()

    assert first["latitude"] == 37.5013961
    assert first["longitude"] == 127.0394712
    assert second["latitude"] == 37.5013661
    assert second["longitude"] == 127.0393712
    assert first["batteryLevel"] == second["batteryLevel"] == 90


def test_live_location_replaces_mock_movement():
    telemetry = MockTelemetry(37.5, 127.0)
    telemetry.next_payload()
    telemetry.set_location(35.1, 129.1)

    first = telemetry.next_payload()
    second = telemetry.next_payload()

    assert first["latitude"] == second["latitude"] == 35.1
    assert first["longitude"] == second["longitude"] == 129.1
