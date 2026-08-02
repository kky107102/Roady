from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import Bool, Float64

from hardware.devices.gps import GpsReceiver
from hardware.devices.location_estimator import LocationEstimator
from hardware.hal.uart import LinuxUart


class GpsLocationNode(Node):
    """Publish GPS coordinates with a wheel-distance fallback."""

    def __init__(self) -> None:
        super().__init__("gps_location")
        self.declare_parameter("port", "/dev/ttyTHS1")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("virtual_latitude", 37.5012748)
        self.declare_parameter("virtual_longitude", 127.039625)
        self.declare_parameter("heading_deg", 90.0)
        self.declare_parameter("gps_timeout_sec", 3.0)
        self.declare_parameter("publish_hz", 5.0)

        publish_hz = float(self.get_parameter("publish_hz").value)
        if publish_hz <= 0.0:
            raise ValueError("publish_hz must be positive")

        self._estimator = LocationEstimator(
            float(self.get_parameter("virtual_latitude").value),
            float(self.get_parameter("virtual_longitude").value),
            heading_deg=float(self.get_parameter("heading_deg").value),
            gps_timeout_sec=float(self.get_parameter("gps_timeout_sec").value),
        )
        self._receiver = GpsReceiver(
            LinuxUart(
                str(self.get_parameter("port").value),
                int(self.get_parameter("baudrate").value),
            )
        )
        self._fix_publisher = self.create_publisher(
            NavSatFix, "/location/fix", qos_profile_sensor_data
        )
        self._fallback_publisher = self.create_publisher(
            Bool, "/location/using_fallback", 10
        )
        self._distance_subscription = self.create_subscription(
            Float64,
            "/wheel/distance_m",
            self._on_distance,
            qos_profile_sensor_data,
        )
        self._read_timer = self.create_timer(0.01, self._read_gps)
        self._publish_timer = self.create_timer(1.0 / publish_hz, self._publish_location)
        self._closed = False
        self._last_source = None
        self.get_logger().info(
            "GPS location ready; wheel-distance fallback is enabled"
        )

    def _read_gps(self) -> None:
        _, reading = self._receiver.read(timeout=0.0)
        if (
            reading is not None
            and reading.valid
            and reading.latitude is not None
            and reading.longitude is not None
        ):
            self._estimator.update_gps(reading.latitude, reading.longitude)

    def _on_distance(self, message: Float64) -> None:
        try:
            self._estimator.update_distance(message.data)
        except ValueError as exc:
            self.get_logger().warn(f"Ignored invalid wheel distance: {exc}")

    def _publish_location(self) -> None:
        location = self._estimator.location()
        using_fallback = location.source != "gps"

        message = NavSatFix()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "gps"
        message.status.status = (
            NavSatStatus.STATUS_NO_FIX if using_fallback else NavSatStatus.STATUS_FIX
        )
        message.status.service = NavSatStatus.SERVICE_GPS
        message.latitude = location.latitude
        message.longitude = location.longitude
        message.altitude = float("nan")
        message.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
        self._fix_publisher.publish(message)
        self._fallback_publisher.publish(Bool(data=using_fallback))

        if location.source != self._last_source:
            log = self.get_logger().warn if using_fallback else self.get_logger().info
            log(f"Location source changed to {location.source.upper()}")
            self._last_source = location.source

    def destroy_node(self) -> bool:
        if not self._closed:
            self._receiver.close()
            self._closed = True
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = GpsLocationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
