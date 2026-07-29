from __future__ import annotations

from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from perception.algorithms.damage_detector import MockDamageDetector
from storage.damage_repository import DamageLocation, DamageRepository


class MockDamageDetectionNode(Node):
    def __init__(self):
        super().__init__("mock_damage_detection_node")

        self.declare_parameter("image_topic", "/camera/wide/image_raw")
        self.declare_parameter("event_topic", "/damage/events")
        self.declare_parameter("storage_dir", "data/damage_events")
        self.declare_parameter("capture_interval_sec", 5.0)
        self.declare_parameter("base_latitude", 37.5665)
        self.declare_parameter("base_longitude", 126.9780)
        self.declare_parameter("sensor_latitude_offset", 0.0001)
        self.declare_parameter("sensor_longitude_offset", 0.0001)
        self.declare_parameter("gps_latitude_step", 0.00001)
        self.declare_parameter("gps_longitude_step", 0.00001)
        self.declare_parameter("robot_id", 1)
        self.declare_parameter("description", "도로 균열 감지")

        storage_dir = Path(str(self.get_parameter("storage_dir").value))
        self._repository = DamageRepository(storage_dir)
        self._detector = MockDamageDetector()
        self._last_saved_time = 0.0
        self._capture_count = 0

        image_topic = str(self.get_parameter("image_topic").value)
        event_topic = str(self.get_parameter("event_topic").value)
        self._subscription = self.create_subscription(
            Image,
            image_topic,
            self._on_image,
            10,
        )
        self._event_publisher = self.create_publisher(String, event_topic, 10)

        self.get_logger().info(
            f"Mock damage detection subscribed to {image_topic}, saving to {storage_dir}"
        )

    def _on_image(self, msg: Image) -> None:
        now = self.get_clock().now().nanoseconds / 1_000_000_000
        interval = float(self.get_parameter("capture_interval_sec").value)
        if now - self._last_saved_time < interval:
            return

        image = self._image_msg_to_bgr(msg)
        self._detector.detect(image)
        location = self._dummy_location()
        event = self._repository.save_event(
            images=[image],
            location=location,
            robot_id=int(self.get_parameter("robot_id").value),
            description=str(self.get_parameter("description").value),
        )

        self._last_saved_time = now
        self._capture_count += 1
        self._event_publisher.publish(String(data=self._repository.to_json(event)))
        self.get_logger().info(
            "Saved mock damage event at "
            f"{location.latitude:.6f}, {location.longitude:.6f}"
        )

    def _dummy_location(self) -> DamageLocation:
        latitude = float(self.get_parameter("base_latitude").value)
        longitude = float(self.get_parameter("base_longitude").value)
        latitude += float(self.get_parameter("sensor_latitude_offset").value)
        longitude += float(self.get_parameter("sensor_longitude_offset").value)
        latitude += self._capture_count * float(
            self.get_parameter("gps_latitude_step").value
        )
        longitude += self._capture_count * float(
            self.get_parameter("gps_longitude_step").value
        )
        return DamageLocation(
            latitude=latitude,
            longitude=longitude,
        )

    @staticmethod
    def _image_msg_to_bgr(msg: Image) -> np.ndarray:
        if msg.encoding != "bgr8":
            raise ValueError(f"Unsupported image encoding: {msg.encoding}")
        channels = 3
        image = np.frombuffer(msg.data, dtype=np.uint8)
        return image.reshape((msg.height, msg.width, channels)).copy()


def main(args=None):
    rclpy.init(args=args)
    node = MockDamageDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
