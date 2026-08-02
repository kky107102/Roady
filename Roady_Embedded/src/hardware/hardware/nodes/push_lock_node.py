from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool

from hardware.devices.push_lock import PushLock
from hardware.hal import create_gpio_backend


DEFAULT_PINS = {
    "raspberry_pi": (17, 18),
    "jetson": (31, 15),
}

EMERGENCY_STOP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class PushLockNode(Node):
    """Publish the debounced push-lock state for the motor safety system."""

    def __init__(self) -> None:
        super().__init__("push_lock")
        self.declare_parameter("platform", "jetson")
        self.declare_parameter("button_pin", -1)
        self.declare_parameter("indicator_pin", -1)
        self.declare_parameter("active_low", True)
        self.declare_parameter("indicator_active_low", False)
        self.declare_parameter("debounce_sec", 0.05)
        self.declare_parameter("poll_hz", 50.0)

        platform = str(self.get_parameter("platform").value)
        if platform not in DEFAULT_PINS:
            raise ValueError(f"unsupported platform: {platform}")
        default_button, default_indicator = DEFAULT_PINS[platform]
        button_pin = int(self.get_parameter("button_pin").value)
        indicator_pin = int(self.get_parameter("indicator_pin").value)
        if button_pin < 0:
            button_pin = default_button
        if indicator_pin < 0:
            indicator_pin = default_indicator

        debounce_sec = float(self.get_parameter("debounce_sec").value)
        poll_hz = float(self.get_parameter("poll_hz").value)
        if poll_hz <= 0:
            raise ValueError("poll_hz must be positive")

        # The verified Jetson wiring uses LOW as the locked signal.
        pull_up = True if platform == "raspberry_pi" else False
        self._gpio = create_gpio_backend(platform)
        self._lock = PushLock(
            self._gpio.input(button_pin, pull_up=pull_up),
            self._gpio.output(indicator_pin, initial=False),
            active_low=bool(self.get_parameter("active_low").value),
            indicator_active_low=bool(
                self.get_parameter("indicator_active_low").value
            ),
            debounce_sec=debounce_sec,
        )
        self._publisher = self.create_publisher(
            Bool,
            "/emergency_stop",
            EMERGENCY_STOP_QOS,
        )
        self._timer = self.create_timer(1.0 / poll_hz, self._poll)
        self._closed = False
        self.get_logger().info(
            "Push-lock ready: "
            f"platform={platform}, button={button_pin}, indicator={indicator_pin}"
        )

    def _poll(self) -> None:
        state = self._lock.poll()
        if not state.changed:
            return

        self._publisher.publish(Bool(data=state.locked))
        if state.locked:
            self.get_logger().warn("EMERGENCY STOP engaged")
        else:
            self.get_logger().info("Emergency stop released")

    def destroy_node(self) -> bool:
        if not self._closed:
            self._lock.close()
            self._gpio.close()
            self._closed = True
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PushLockNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
