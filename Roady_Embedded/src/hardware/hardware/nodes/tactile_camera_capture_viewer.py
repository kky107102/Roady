from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from hardware.devices.image_capture import image_message_to_bgr, save_frame


class CameraCaptureViewer(Node):
    def __init__(
        self,
        *,
        node_name: str,
        default_topic: str,
        default_output_dir: str,
        filename_prefix: str,
        window_name: str,
    ) -> None:
        super().__init__(node_name)
        self.declare_parameter("topic", default_topic)
        self.declare_parameter("output_dir", default_output_dir)
        self.declare_parameter("jpeg_quality", 95)

        topic = str(self.get_parameter("topic").value)
        output_value = str(self.get_parameter("output_dir").value)
        self._output_dir = Path(output_value).expanduser().resolve()
        self._jpeg_quality = max(
            0, min(100, int(self.get_parameter("jpeg_quality").value))
        )
        self._filename_prefix = filename_prefix
        self._window_name = window_name
        self._latest_frame: Optional[np.ndarray] = None
        self._button_rect = (0, 0, 0, 0)
        self._saved_count = 0
        self._status = "S / Space / SAVE button = capture"
        self._should_close = False

        self._output_dir.mkdir(parents=True, exist_ok=True)
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self._window_name, self._handle_mouse)
        self._subscription = self.create_subscription(
            Image, topic, self._handle_image, qos_profile_sensor_data
        )
        self.get_logger().info(
            f"Viewing {topic}; captures will be saved to {self._output_dir}"
        )

    @property
    def should_close(self) -> bool:
        return self._should_close

    def destroy_node(self):
        cv2.destroyWindow(self._window_name)
        super().destroy_node()

    def _handle_image(self, message: Image) -> None:
        try:
            self._latest_frame = image_message_to_bgr(message)
        except ValueError as error:
            self.get_logger().error(str(error))
            return

        preview = self._latest_frame.copy()
        self._draw_controls(preview)
        cv2.imshow(self._window_name, preview)
        key = cv2.waitKey(1) & 0xFF
        if key in {ord("s"), ord("S"), ord(" ")}:
            self._capture_latest()
        elif key in {27, ord("q"), ord("Q")}:
            self._should_close = True

    def _draw_controls(self, preview: np.ndarray) -> None:
        height, width = preview.shape[:2]
        button_width = min(150, max(90, width // 5))
        left = max(0, width - button_width - 16)
        right = max(0, width - 16)
        top, bottom = 16, min(68, height - 1)
        self._button_rect = (left, top, right, bottom)

        cv2.rectangle(preview, (left, top), (right, bottom), (20, 150, 20), -1)
        cv2.putText(
            preview,
            "SAVE",
            (left + 18, min(bottom - 13, top + 37)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            preview,
            f"saved={self._saved_count}  {self._status}",
            (16, max(30, height - 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2,
        )

    def _handle_mouse(self, event, x, y, _flags, _param) -> None:
        if event != cv2.EVENT_LBUTTONUP:
            return
        left, top, right, bottom = self._button_rect
        if left <= x <= right and top <= y <= bottom:
            self._capture_latest()

    def _capture_latest(self) -> None:
        if self._latest_frame is None:
            self._status = "No frame received yet"
            return
        try:
            output_path = save_frame(
                self._latest_frame,
                self._output_dir,
                jpeg_quality=self._jpeg_quality,
                filename_prefix=self._filename_prefix,
            )
        except OSError as error:
            self._status = "Save failed - check terminal"
            self.get_logger().error(str(error))
            return

        self._saved_count += 1
        self._status = f"Saved: {output_path.name}"
        self.get_logger().info(f"Saved capture: {output_path}")


class TactileCameraCaptureViewer(CameraCaptureViewer):
    def __init__(self) -> None:
        super().__init__(
            node_name="tactile_camera_capture_viewer",
            default_topic="/camera/tactile/image_raw",
            default_output_dir="~/roady_dataset/wide_camera",
            filename_prefix="tactile",
            window_name="ROADY tactile-camera data capture",
        )


def run_viewer(node_factory, args=None) -> None:
    rclpy.init(args=args)
    node = node_factory()
    try:
        while rclpy.ok() and not node.should_close:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def main(args=None) -> None:
    run_viewer(TactileCameraCaptureViewer, args=args)


if __name__ == "__main__":
    main()
