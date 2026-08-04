from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import Bool, Float64

from hardware.devices.gps import GpsReceiver
from hardware.devices.location_estimator import LocationEstimator
from hardware.hal.uart import LinuxUart


WHEEL_DISTANCE_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class GpsLocationNode(Node):
    """Publish a Hall-only indoor or GPS-assisted outdoor location."""

    def __init__(self) -> None:
        super().__init__("gps_location")
        self.declare_parameter("location_mode", "indoor")
        self.declare_parameter("port", "/dev/ttyTHS1")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("virtual_latitude", 37.5012748)
        self.declare_parameter("virtual_longitude", 127.039625)
        # 0.367 physical m/pulse * 24.03688 = 8.821536 virtual m/pulse,
        # which keeps consecutive demo markers visible on the server map.
        self.declare_parameter("virtual_map_scale", 24.0368829327)
        self.declare_parameter("gps_timeout_sec", 3.0)
        self.declare_parameter("publish_hz", 5.0)

        self._location_mode = str(self.get_parameter("location_mode").value).lower()
        if self._location_mode not in {"indoor", "outdoor"}:
            raise ValueError("location_mode must be 'indoor' or 'outdoor'")
        use_gps = self._location_mode == "outdoor"
        virtual_map_scale = float(self.get_parameter("virtual_map_scale").value)
        publish_hz = float(self.get_parameter("publish_hz").value)
        if publish_hz <= 0.0:
            raise ValueError("publish_hz must be positive")

        self._estimator = LocationEstimator(
            float(self.get_parameter("virtual_latitude").value),
            float(self.get_parameter("virtual_longitude").value),
            use_gps=use_gps,
            gps_timeout_sec=float(self.get_parameter("gps_timeout_sec").value),
            wheel_distance_scale=virtual_map_scale if not use_gps else 1.0,
        )
        self._receiver = None
        if use_gps:
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
            WHEEL_DISTANCE_QOS,
        )
        self._read_timer = (
            self.create_timer(0.01, self._read_gps) if use_gps else None
        )
        self._publish_timer = self.create_timer(1.0 / publish_hz, self._publish_location)
        self._last_source = None
        self.get_logger().info(
            f"Location ready: mode={self._location_mode}, "
            f"GPS={'enabled' if use_gps else 'disabled'}, "
            f"map_scale={virtual_map_scale if not use_gps else 1.0:.3f}"
        )

    def _read_gps(self) -> None:
        if self._receiver is None:
            return
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
        using_wheel = location.source == "wheel"

        message = NavSatFix()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = location.source
        message.status.status = (
            NavSatStatus.STATUS_NO_FIX if using_wheel else NavSatStatus.STATUS_FIX
        )
        message.status.service = (
            0 if using_wheel else NavSatStatus.SERVICE_GPS
        )
        message.latitude = location.latitude
        message.longitude = location.longitude
        message.altitude = float("nan")
        message.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
        self._fix_publisher.publish(message)
        self._fallback_publisher.publish(Bool(data=using_wheel))

        if location.source != self._last_source:
            self.get_logger().info(f"Location source: {location.source.upper()}")
            self._last_source = location.source

    def destroy_node(self) -> bool:
        if self._receiver is not None:
            self._receiver.close()
            self._receiver = None
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
