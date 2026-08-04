from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Float64, UInt64

from hardware.devices.hall_sensor import HallSensor
from hardware.devices.wheel_odometry import WheelDistance, WheelOdometry
from hardware.hal import create_gpio_backend


DEFAULT_PINS = {
    "raspberry_pi": 13,
    "jetson": 33,
}

DISTANCE_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class HallDistanceNode(Node):
    """Publish cumulative travel distance measured by one wheel magnet."""

    def __init__(self) -> None:
        super().__init__("hall_distance")
        self.declare_parameter("platform", "jetson")
        self.declare_parameter("pin", -1)
        self.declare_parameter("active_low", True)
        self.declare_parameter("debounce_sec", 0.02)
        self.declare_parameter("poll_hz", 100.0)
        # Physical calibration values. Set distance_per_pulse_m to 0 to use
        # wheel diameter and pulses per revolution instead.
        self.declare_parameter("wheel_diameter_m", 0.10)
        self.declare_parameter("pulses_per_revolution", 1)
        # Measured with the vehicle on the floor: 3 pulses=1.09 m and
        # 5 pulses=1.85 m, giving approximately 0.367 m per pulse.
        self.declare_parameter("distance_per_pulse_m", 0.367)

        platform = str(self.get_parameter("platform").value)
        if platform not in DEFAULT_PINS:
            raise ValueError(f"unsupported platform: {platform}")
        pin = int(self.get_parameter("pin").value)
        if pin < 0:
            pin = DEFAULT_PINS[platform]
        poll_hz = float(self.get_parameter("poll_hz").value)
        if poll_hz <= 0.0:
            raise ValueError("poll_hz must be positive")

        distance_per_pulse_m = float(
            self.get_parameter("distance_per_pulse_m").value
        )
        self._odometry = WheelOdometry(
            wheel_diameter_m=float(
                self.get_parameter("wheel_diameter_m").value
            ),
            pulses_per_revolution=int(
                self.get_parameter("pulses_per_revolution").value
            ),
            distance_per_pulse_m=(
                distance_per_pulse_m if distance_per_pulse_m > 0.0 else None
            ),
        )
        # Pi has an internal pull-up. Jetson BOARD 33 uses the verified external
        # 1 kOhm pull-up between SIGNAL and 3.3 V.
        pull_up = True if platform == "raspberry_pi" else None
        self._gpio = create_gpio_backend(platform)
        self._sensor = HallSensor(
            self._gpio.input(pin, pull_up=pull_up),
            active_low=bool(self.get_parameter("active_low").value),
            debounce_sec=float(self.get_parameter("debounce_sec").value),
        )
        self._distance_publisher = self.create_publisher(
            Float64, "/wheel/distance_m", DISTANCE_QOS
        )
        self._pulse_publisher = self.create_publisher(
            UInt64, "/wheel/pulse_count", DISTANCE_QOS
        )
        self._timer = self.create_timer(1.0 / poll_hz, self._poll)
        self._closed = False
        self._pulse_armed = False
        self._publish(self._odometry.state)
        self.get_logger().info(
            "Hall distance ready: "
            f"platform={platform}, pin={pin}, "
            f"distance_per_pulse={self._odometry.meters_per_pulse:.3f}m"
        )

    def _poll(self) -> None:
        hall_state = self._sensor.poll()
        if hall_state.changed and not hall_state.detected:
            # Establish a known released state first. This prevents a magnet
            # already attached at process startup from becoming a false pulse.
            self._pulse_armed = True
        # Count only the transition into magnet detection, not every poll while
        # the magnet remains in front of the sensor.
        if hall_state.changed and hall_state.detected and self._pulse_armed:
            state = self._odometry.record_pulse()
            self._publish(state)
            self.get_logger().info(
                f"Wheel pulse {state.pulse_count}: {state.distance_m:.3f}m"
            )

    def _publish(self, state: WheelDistance) -> None:
        self._distance_publisher.publish(Float64(data=state.distance_m))
        self._pulse_publisher.publish(UInt64(data=state.pulse_count))

    def destroy_node(self) -> bool:
        if not self._closed:
            self._sensor.close()
            self._gpio.close()
            self._closed = True
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = HallDistanceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
