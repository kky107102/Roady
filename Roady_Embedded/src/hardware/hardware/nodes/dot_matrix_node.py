from __future__ import annotations

import rclpy
from rclpy.node import Node

from hardware.devices.max7219_matrix import Max7219Config, Max7219Matrix
from hardware.devices.running_eyes import show_running_eyes


class DotMatrixNode(Node):
    """Keep the robot's fixed running eyes lit for this node's lifetime."""

    def __init__(self) -> None:
        super().__init__("dot_matrix")
        self.declare_parameter("port", 0)
        self.declare_parameter("device", 0)
        self.declare_parameter("cascaded", 4)
        self.declare_parameter("bus_speed_hz", 500_000)
        self.declare_parameter("block_orientation", -90)
        self.declare_parameter("rotate", 0)
        self.declare_parameter("blocks_reversed", False)
        self.declare_parameter("contrast", 5)

        self._display = Max7219Matrix(
            Max7219Config(
                port=self.get_parameter("port").value,
                device=self.get_parameter("device").value,
                cascaded=self.get_parameter("cascaded").value,
                bus_speed_hz=self.get_parameter("bus_speed_hz").value,
                block_orientation=self.get_parameter("block_orientation").value,
                rotate=self.get_parameter("rotate").value,
                blocks_reversed=self.get_parameter("blocks_reversed").value,
                contrast=self.get_parameter("contrast").value,
            )
        )
        show_running_eyes(self._display)
        self.get_logger().info("Robot running eyes are on (blocks 1 and 4).")

    def destroy_node(self) -> bool:
        self._display.close()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DotMatrixNode()
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
