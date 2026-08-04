from __future__ import annotations

import json
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, String

from perception.algorithms.camera_safety_filter import CameraSafetyFilter


STOP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class SafetyFusionNode(Node):
    """Publish a latched camera safety decision; LiDAR fusion is added later."""

    def __init__(self) -> None:
        super().__init__("safety_fusion_node")
        self.declare_parameter(
            "camera_detection_topic", "/obstacle/human_lower_limb_detected"
        )
        self.declare_parameter("stop_topic", "/safety/stop_required")
        self.declare_parameter("status_topic", "/safety/status")
        self.declare_parameter("vote_window", 3)
        self.declare_parameter("vote_required", 2)
        self.declare_parameter("clear_frames", 10)
        self.declare_parameter("minimum_hold_sec", 1.0)
        self.declare_parameter("camera_timeout_sec", 0.5)
        self.declare_parameter("stop_on_camera_timeout", False)
        self.declare_parameter("publish_rate_hz", 20.0)

        self._camera_timeout_sec = float(
            self.get_parameter("camera_timeout_sec").value
        )
        self._stop_on_camera_timeout = bool(
            self.get_parameter("stop_on_camera_timeout").value
        )
        vote_window = int(self.get_parameter("vote_window").value)
        vote_required = int(self.get_parameter("vote_required").value)
        clear_frames = int(self.get_parameter("clear_frames").value)
        minimum_hold_sec = float(self.get_parameter("minimum_hold_sec").value)
        self._filter = CameraSafetyFilter(
            vote_window=vote_window,
            vote_required=vote_required,
            clear_frames=clear_frames,
            minimum_hold_sec=minimum_hold_sec,
        )
        self._stop_publisher = self.create_publisher(
            Bool, str(self.get_parameter("stop_topic").value), STOP_QOS
        )
        self._status_publisher = self.create_publisher(
            String, str(self.get_parameter("status_topic").value), 10
        )
        self.create_subscription(
            Bool,
            str(self.get_parameter("camera_detection_topic").value),
            self._on_camera_detection,
            10,
        )

        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        if publish_rate_hz <= 0:
            raise ValueError("publish_rate_hz must be positive")
        self._timer = self.create_timer(1.0 / publish_rate_hz, self._publish_state)
        self._previous_stop: bool | None = None
        self._previous_camera_alive: bool | None = None
        self.get_logger().info(
            f"Camera safety filter ready: vote={vote_required}/{vote_window}, "
            f"clear={clear_frames} frames, hold={minimum_hold_sec:.2f}s, "
            f"timeout={self._camera_timeout_sec:.2f}s, "
            f"stop_on_timeout={self._stop_on_camera_timeout}"
        )

    def _on_camera_detection(self, msg: Bool) -> None:
        self._filter.update(bool(msg.data), time.monotonic())

    def _publish_state(self) -> None:
        state = self._filter.check_timeout(
            time.monotonic(),
            self._camera_timeout_sec,
            self._stop_on_camera_timeout,
        )
        self._stop_publisher.publish(Bool(data=state.stop_required))
        status = {
            "stop_required": state.stop_required,
            "reason": state.reason,
            "recent_detections": list(state.recent_detections),
            "clear_count": state.clear_count,
            "camera_alive": state.camera_alive,
        }
        self._status_publisher.publish(
            String(data=json.dumps(status, ensure_ascii=False))
        )

        if state.stop_required != self._previous_stop:
            if state.stop_required:
                self.get_logger().warn(f"Safety stop engaged: {state.reason}")
            elif self._previous_stop is not None:
                self.get_logger().info("Safety stop released")
            self._previous_stop = state.stop_required

        if state.camera_alive != self._previous_camera_alive:
            if state.camera_alive:
                self.get_logger().info("Camera detection stream active")
            elif self._previous_camera_alive is not None:
                self.get_logger().warn("Camera detection stream timed out")
            self._previous_camera_alive = state.camera_alive


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SafetyFusionNode()
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
