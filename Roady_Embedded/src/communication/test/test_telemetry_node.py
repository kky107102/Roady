from datetime import datetime

from communication.telemetry import MockTelemetry


def test_mock_telemetry_matches_server_contract():
    payload = MockTelemetry(37.5012748, 127.039625).next_payload()

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


def test_longitude_increases_and_latitude_stays_fixed():
    mock = MockTelemetry(37.5012748, 127.039625)

    first = mock.next_payload()
    second = mock.next_payload()

    assert first["latitude"] == second["latitude"] == 37.5012748
    assert first["longitude"] == 127.039625
    assert second["longitude"] == 127.039725
    assert 20 <= first["batteryLevel"] <= 100
    assert 20 <= second["batteryLevel"] <= 100
