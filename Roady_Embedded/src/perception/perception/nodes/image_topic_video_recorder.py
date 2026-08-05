from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image


class ImageTopicVideoRecorder(Node):
    """Record a ROS BGR/RGB image topic to MP4 without a display server."""

    def __init__(self) -> None:
        super().__init__("image_topic_video_recorder")
        self.declare_parameter("image_topic", "/damage/annotated")
        self.declare_parameter("output_path", "reports/damage_annotated.mp4")
        self.declare_parameter("output_fps", 10.0)
        self.declare_parameter("codec", "mp4v")

        self._image_topic = str(self.get_parameter("image_topic").value)
        self._output_path = Path(
            str(self.get_parameter("output_path").value)
        ).expanduser()
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_fps = float(self.get_parameter("output_fps").value)
        if self._output_fps <= 0:
            raise ValueError("output_fps must be positive")
        codec = str(self.get_parameter("codec").value)
        if len(codec) != 4:
            raise ValueError("codec must contain exactly four characters")
        self._fourcc = cv2.VideoWriter_fourcc(*codec)
        self._writer: cv2.VideoWriter | None = None
        self._frame_size: tuple[int, int] | None = None
        self._frames_written = 0
        self._frames_received = 0
        self._first_stamp_sec: float | None = None
        self._last_stamp_sec: float | None = None

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self._subscription = self.create_subscription(
            Image, self._image_topic, self._on_image, qos
        )
        self.get_logger().info(
            f"Recording {self._image_topic} to {self._output_path} "
            f"at {self._output_fps:.2f} FPS"
        )

    def _on_image(self, msg: Image) -> None:
        frame = self._image_msg_to_bgr(msg)
        self._frames_received += 1
        stamp_sec = self._stamp_sec(msg)
        frame_size = (msg.width, msg.height)
        if self._writer is None:
            self._writer = cv2.VideoWriter(
                str(self._output_path), self._fourcc, self._output_fps, frame_size
            )
            if not self._writer.isOpened():
                self._writer.release()
                self._writer = None
                raise RuntimeError(f"Could not open video output: {self._output_path}")
            self._frame_size = frame_size
            self._first_stamp_sec = stamp_sec
        elif frame_size != self._frame_size:
            self.get_logger().error(
                f"Ignored frame size change: {self._frame_size} -> {frame_size}"
            )
            return

        assert self._first_stamp_sec is not None
        self._last_stamp_sec = stamp_sec
        elapsed_sec = max(0.0, stamp_sec - self._first_stamp_sec)
        target_frame_index = int(round(elapsed_sec * self._output_fps))
        # ROS sensor QoS may drop frames while software video encoding is busy.
        # Duplicate the newest received frame as needed so MP4 playback duration
        # follows the source timestamps instead of the number of callbacks.
        while self._frames_written <= target_frame_index:
            self._writer.write(frame)
            self._frames_written += 1

    def _stamp_sec(self, msg: Image) -> float:
        stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec / 1_000_000_000
        if stamp_sec > 0:
            return stamp_sec
        return self.get_clock().now().nanoseconds / 1_000_000_000

    @staticmethod
    def _image_msg_to_bgr(msg: Image) -> np.ndarray:
        if msg.encoding not in {"bgr8", "rgb8"}:
            raise ValueError(f"Unsupported image encoding: {msg.encoding}")
        rows = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.step))
        image = rows[:, : msg.width * 3].reshape((msg.height, msg.width, 3)).copy()
        return image if msg.encoding == "bgr8" else image[:, :, ::-1].copy()

    def destroy_node(self):
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        source_duration = (
            self._last_stamp_sec - self._first_stamp_sec
            if self._first_stamp_sec is not None and self._last_stamp_sec is not None
            else 0.0
        )
        self.get_logger().info(
            f"Saved {self._frames_written} frames ({self._frames_received} received, "
            f"source duration={source_duration:.2f}s) to {self._output_path}"
        )
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ImageTopicVideoRecorder()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
