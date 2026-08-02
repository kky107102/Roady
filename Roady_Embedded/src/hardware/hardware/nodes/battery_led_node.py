from __future__ import annotations

import rclpy
from rclpy.node import Node

from hardware.devices.battery_indicator import BatteryIndicator
from hardware.devices.led_bank import LedBank
from hardware.hal import create_gpio_backend


DEFAULT_PINS = {
    "raspberry_pi": (22, 6),
    "jetson": (7, 29),
}


class BatteryLedNode(Node):
    """Keep the LED matching the configured battery level lit."""

    def __init__(self) -> None:
        super().__init__("battery_led")
        self.declare_parameter("platform", "jetson")
        self.declare_parameter("green_pin", -1)
        self.declare_parameter("red_pin", -1)
        self.declare_parameter("battery_percent", 100.0)
        self.declare_parameter("low_threshold", 20.0)

        platform = str(self.get_parameter("platform").value)
        if platform not in DEFAULT_PINS:
            raise ValueError(f"unsupported platform: {platform}")
        default_green, default_red = DEFAULT_PINS[platform]
        green_pin = int(self.get_parameter("green_pin").value)
        red_pin = int(self.get_parameter("red_pin").value)
        if green_pin < 0:
            green_pin = default_green
        if red_pin < 0:
            red_pin = default_red

        battery_percent = float(self.get_parameter("battery_percent").value)
        low_threshold = float(self.get_parameter("low_threshold").value)
        if not 0.0 <= battery_percent <= 100.0:
            raise ValueError("battery_percent must be between 0 and 100")
        if not 0.0 <= low_threshold <= 100.0:
            raise ValueError("low_threshold must be between 0 and 100")

        self._gpio = create_gpio_backend(platform)
        self._leds = LedBank(
            (
                self._gpio.output(green_pin, initial=False),
                self._gpio.output(red_pin, initial=False),
            )
        )
        self._indicator = BatteryIndicator(
            self._leds,
            low_threshold=low_threshold,
        )
        is_low = self._indicator.show(battery_percent)
        self._closed = False

        colour = "RED" if is_low else "GREEN"
        self.get_logger().info(
            f"Battery {battery_percent:.1f}%: {colour} LED on "
            f"(low threshold {low_threshold:.1f}%)"
        )

    def destroy_node(self) -> bool:
        if not self._closed:
            self._leds.close()
            self._gpio.close()
            self._closed = True
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = BatteryLedNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
