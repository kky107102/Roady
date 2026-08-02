from __future__ import annotations

import json
from typing import Any

import paho.mqtt.client as mqtt


class MqttTelemetryClient:
    """Small MQTT client dedicated to publishing robot telemetry."""

    def __init__(
        self,
        host: str,
        port: int,
        client_id: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._connected = False
        self._client = mqtt.Client(client_id=client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

        if username:
            self._client.username_pw_set(username, password)

        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        self._client.connect_async(host, port, keepalive=60)
        self._client.loop_start()

    @property
    def connected(self) -> bool:
        return self._connected

    def publish(self, topic: str, payload: dict[str, Any]) -> bool:
        if not self._connected:
            return False

        message = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        result = self._client.publish(topic, message, qos=1, retain=False)
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def close(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()

    def _on_connect(self, _client, _userdata, _flags, reason_code, _properties=None):
        self._connected = reason_code == 0

    def _on_disconnect(
        self, _client, _userdata, _disconnect_flags, _reason_code=None, _properties=None
    ):
        self._connected = False
