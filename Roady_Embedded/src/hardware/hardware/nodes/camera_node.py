from __future__ import annotations

import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Header

from hardware.devices.camera import CameraConfig, CameraWorker


class WideCameraNode(Node):
    def __init__(self):
        super().__init__("wide_camera_node")

        self.declare_parameter("device_index", 0)
        self.declare_parameter("backend", "v4l2")
        self.declare_parameter("pixel_format", "MJPG")
        self.declare_parameter("width", 1280)
        self.declare_parameter("height", 720)
        self.declare_parameter("fps", 30)
        self.declare_parameter("publish_rate", 30.0)
        self.declare_parameter("frame_id", "wide_camera")
        self.declare_parameter("topic", "/camera/wide/image_raw")

        width = self.get_parameter("width").value
        height = self.get_parameter("height").value
        fps = self.get_parameter("fps").value
        backend = self.get_parameter("backend").value
        pixel_format = self.get_parameter("pixel_format").value
        topic = self.get_parameter("topic").value

        self._frame_id = self.get_parameter("frame_id").value
        self._worker = CameraWorker(
            CameraConfig(
                name="wide_camera",
                device_index=int(self.get_parameter("device_index").value),
                backend=str(backend),
                pixel_format=str(pixel_format) if pixel_format else None,
                width=int(width) if width else None,
                height=int(height) if height else None,
                fps=int(fps) if fps else None,
            )
        )
        self._publisher = self.create_publisher(Image, topic, 10)
        self._last_published_frame_id = -1
        self._last_error_log_time = 0.0

        publish_rate = float(self.get_parameter("publish_rate").value)
        timer_period = 1.0 / publish_rate if publish_rate > 0 else 1.0 / 30.0

        self._worker.start()
        self._timer = self.create_timer(timer_period, self._publish_latest_frame)
        self.get_logger().info(f"Wide camera publishing on {topic}")

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
        msg.data = image.tobytes()
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = WideCameraNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
