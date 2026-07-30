from __future__ import annotations

import array
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Header

from hardware.devices.camera import CameraConfig, CameraWorker


class ObstacleCameraNode(Node):
    """Publishes frames from the camera dedicated to obstacle detection."""

    def __init__(self):
        super().__init__("obstacle_camera_node")

        self.declare_parameter("device_index", 2)
        self.declare_parameter(
            "device_path",
            "/dev/v4l/by-id/usb-046d_Brio_100_2515ZBA0WRC8-video-index0",
        )
        self.declare_parameter("backend", "v4l2")
        self.declare_parameter("pixel_format", "MJPG")
        self.declare_parameter("width", 1280)
        self.declare_parameter("height", 720)
        self.declare_parameter("fps", 30)
        self.declare_parameter("auto_exposure", True)
        self.declare_parameter("publish_rate", 30.0)
        self.declare_parameter("stats_interval_sec", 2.0)
        self.declare_parameter("frame_id", "obstacle_camera")
        self.declare_parameter("topic", "/camera/obstacle/image_raw")

        width = self.get_parameter("width").value
        height = self.get_parameter("height").value
        fps = self.get_parameter("fps").value
        backend = self.get_parameter("backend").value
        pixel_format = self.get_parameter("pixel_format").value
        topic = str(self.get_parameter("topic").value)
        device_path = str(self.get_parameter("device_path").value)

        self._frame_id = str(self.get_parameter("frame_id").value)
        self._worker = CameraWorker(
            CameraConfig(
                name="obstacle_camera",
                device_index=int(self.get_parameter("device_index").value),
                device_path=device_path or None,
                backend=str(backend),
                pixel_format=str(pixel_format) if pixel_format else None,
                width=int(width) if width else None,
                height=int(height) if height else None,
                fps=int(fps) if fps else None,
                auto_exposure=bool(self.get_parameter("auto_exposure").value),
            )
        )
        image_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )
        self._publisher = self.create_publisher(Image, topic, image_qos)
        self._last_published_frame_id = -1
        self._published_frame_count = 0
        self._last_error_log_time = 0.0

        publish_rate = float(self.get_parameter("publish_rate").value)
        timer_period = 1.0 / publish_rate if publish_rate > 0 else 1.0 / 30.0

        self._worker.start()
        self._timer = self.create_timer(timer_period, self._publish_latest_frame)
        stats_interval = float(self.get_parameter("stats_interval_sec").value)
        self._stats_started_at = time.monotonic()
        self._stats_capture_count = 0
        self._stats_publish_count = 0
        self._stats_timer = self.create_timer(
            stats_interval if stats_interval > 0 else 2.0,
            self._log_fps_stats,
        )
        device = device_path or f"index {self.get_parameter('device_index').value}"
        self.get_logger().info(
            f"Obstacle camera ({device}) publishing on {topic}"
        )

    def destroy_node(self):
        self._worker.stop()
        super().destroy_node()

    def _publish_latest_frame(self) -> None:
        frame = self._worker.read_latest(copy=False)
        if frame is None:
            if self._worker.last_error:
                now = time.monotonic()
                if now - self._last_error_log_time > 2.0:
                    self.get_logger().warn(self._worker.last_error)
                    self._last_error_log_time = now
            return
        if frame.frame_id == self._last_published_frame_id:
            return

        self._publisher.publish(self._to_image_msg(frame.image))
        self._last_published_frame_id = frame.frame_id
        self._published_frame_count += 1

    def _log_fps_stats(self) -> None:
        now = time.monotonic()
        elapsed = now - self._stats_started_at
        if elapsed <= 0:
            return

        capture_count = self._worker.frame_count
        publish_count = self._published_frame_count
        capture_fps = (capture_count - self._stats_capture_count) / elapsed
        publish_fps = (publish_count - self._stats_publish_count) / elapsed
        self.get_logger().info(
            f"FPS capture={capture_fps:.2f}, publish={publish_fps:.2f}"
        )

        self._stats_started_at = now
        self._stats_capture_count = capture_count
        self._stats_publish_count = publish_count

    def _to_image_msg(self, image) -> Image:
        height, width, channels = image.shape
        msg = Image()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        msg.height = height
        msg.width = width
        msg.encoding = "bgr8"
        msg.is_bigendian = False
        msg.step = width * channels
        msg.data = array.array("B", image.tobytes())
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleCameraNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
