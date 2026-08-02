from __future__ import annotations

import rclpy
from rclpy.node import Node

from communication.clients.mqtt_client import MqttTelemetryClient
from communication.telemetry import MockTelemetry


class TelemetryNode(Node):
    def __init__(self) -> None:
        super().__init__("telemetry_node")

        self.declare_parameter("robot_id", 365)
        self.declare_parameter("broker_host", "localhost")
        self.declare_parameter("broker_port", 1883)
        self.declare_parameter("mqtt_username", "")
        self.declare_parameter("mqtt_password", "")
        self.declare_parameter("publish_interval_sec", 5.0)
        self.declare_parameter("mock_latitude", 37.5012748)
        self.declare_parameter("mock_longitude", 127.039625)
        self.declare_parameter("mock_longitude_step", 0.0001)

        robot_id = int(self.get_parameter("robot_id").value)
        if robot_id <= 0:
            raise ValueError("robot_id must be a positive integer")

        latitude = float(self.get_parameter("mock_latitude").value)
        longitude = float(self.get_parameter("mock_longitude").value)
        if not -90.0 <= latitude <= 90.0:
            raise ValueError("mock_latitude must be between -90 and 90")
        if not -180.0 <= longitude <= 180.0:
            raise ValueError("mock_longitude must be between -180 and 180")

        self._topic = f"roady/{robot_id}/telemetry"
        self._mock = MockTelemetry(
            latitude=latitude,
            longitude=longitude,
            longitude_step=float(self.get_parameter("mock_longitude_step").value),
        )
        username = str(self.get_parameter("mqtt_username").value)
        password = str(self.get_parameter("mqtt_password").value)
        self._mqtt = MqttTelemetryClient(
            host=str(self.get_parameter("broker_host").value),
            port=int(self.get_parameter("broker_port").value),
            client_id=f"roady-robot-{robot_id}-telemetry",
            username=username or None,
            password=password or None,
        )

        interval = max(float(self.get_parameter("publish_interval_sec").value), 1.0)
        self._timer = self.create_timer(interval, self._publish_telemetry)
        self.get_logger().info(
            f"Mock telemetry ready: topic={self._topic}, interval={interval:.1f}s"
        )

    def _publish_telemetry(self) -> None:
        if not self._mqtt.connected:
            self.get_logger().warn("MQTT is disconnected; telemetry was not published")
            return

        payload = self._mock.next_payload()
        if self._mqtt.publish(self._topic, payload):
            self.get_logger().info(
                "Published telemetry: "
                f"lat={payload['latitude']}, lon={payload['longitude']}, "
                f"battery={payload['batteryLevel']}%"
            )
        else:
            self.get_logger().warn("MQTT is disconnected; telemetry was not published")

    def destroy_node(self) -> bool:
        self._mqtt.close()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TelemetryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
