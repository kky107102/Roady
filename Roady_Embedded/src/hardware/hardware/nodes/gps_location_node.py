from __future__ import annotations

import math
import time

from geometry_msgs.msg import Twist
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
        self.declare_parameter("virtual_latitude", 37.501361)
        self.declare_parameter("virtual_longitude", 127.039500)
        # Demo-map calibration: one 0.36 m wheel revolution moves the marker by
        # (-0.00003, -0.0001). This can be driven by Hall distance or by the
        # time-based /cmd_vel fallback used when the Hall sensor is unavailable.
        self.declare_parameter("latitude_offset_per_meter", -0.00003 / 0.36)
        self.declare_parameter("longitude_offset_per_meter", -0.0001 / 0.36)
        self.declare_parameter("use_time_based_distance", False)
        self.declare_parameter("estimated_speed_mps", 0.10)
        self.declare_parameter("nominal_drive_command", 0.40)
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("gps_timeout_sec", 3.0)
        self.declare_parameter("publish_hz", 5.0)

        self._location_mode = str(self.get_parameter("location_mode").value).lower()
        if self._location_mode not in {"indoor", "outdoor"}:
            raise ValueError("location_mode must be 'indoor' or 'outdoor'")
        use_gps = self._location_mode == "outdoor"
        publish_hz = float(self.get_parameter("publish_hz").value)
        if publish_hz <= 0.0:
            raise ValueError("publish_hz must be positive")

        self._estimator = LocationEstimator(
            float(self.get_parameter("virtual_latitude").value),
            float(self.get_parameter("virtual_longitude").value),
            use_gps=use_gps,
            gps_timeout_sec=float(self.get_parameter("gps_timeout_sec").value),
            latitude_offset_per_meter=(
                float(self.get_parameter("latitude_offset_per_meter").value)
                if not use_gps else 0.0
            ),
            longitude_offset_per_meter=(
                float(self.get_parameter("longitude_offset_per_meter").value)
                if not use_gps else None
            ),
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
        self._use_time_based_distance = bool(
            self.get_parameter("use_time_based_distance").value
        )
        self._estimated_speed_mps = float(
            self.get_parameter("estimated_speed_mps").value
        )
        self._nominal_drive_command = abs(
            float(self.get_parameter("nominal_drive_command").value)
        )
        if (
            not math.isfinite(self._estimated_speed_mps)
            or self._estimated_speed_mps < 0.0
        ):
            raise ValueError("estimated_speed_mps must be finite and non-negative")
        if (
            not math.isfinite(self._nominal_drive_command)
            or self._nominal_drive_command <= 0.0
        ):
            raise ValueError("nominal_drive_command must be finite and positive")
        self._command_linear_x = 0.0
        self._time_distance_m = 0.0
        self._last_distance_update = time.monotonic()
        self._distance_subscription = None
        self._cmd_vel_subscription = None
        self._distance_timer = None
        if self._use_time_based_distance:
            self._cmd_vel_subscription = self.create_subscription(
                Twist,
                str(self.get_parameter("cmd_vel_topic").value),
                self._on_cmd_vel,
                10,
            )
            self._distance_timer = self.create_timer(0.05, self._update_time_distance)
        else:
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
            f"distance_source={'time/cmd_vel' if self._use_time_based_distance else 'hall'}, "
            f"estimated_speed={self._estimated_speed_mps:.2f}m/s"
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

    def _on_cmd_vel(self, message: Twist) -> None:
        self._command_linear_x = (
            float(message.linear.x) if math.isfinite(message.linear.x) else 0.0
        )

    def _update_time_distance(self) -> None:
        now = time.monotonic()
        elapsed = min(max(0.0, now - self._last_distance_update), 0.5)
        self._last_distance_update = now
        command_ratio = min(
            1.0, abs(self._command_linear_x) / self._nominal_drive_command
        )
        self._time_distance_m += elapsed * self._estimated_speed_mps * command_ratio
        self._estimator.update_distance(self._time_distance_m)

    def _publish_location(self) -> None:
        location = self._estimator.location()
        using_wheel = location.source == "wheel"

        message = NavSatFix()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = (
            "time" if self._use_time_based_distance and location.source == "wheel"
            else location.source
        )
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
