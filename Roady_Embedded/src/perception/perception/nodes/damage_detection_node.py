from __future__ import annotations

from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, NavSatFix
from std_msgs.msg import String

from perception.algorithms.damage_classifier import DamageClassifier
from perception.algorithms.damage_detector import DamageDetector
from perception.algorithms.damage_event_pipeline import DamageEventPipeline, ReadyDamageEvent
from storage.damage_repository import DamageLocation, DamageRepository


class DamageDetectionNode(Node):
    def __init__(self):
        super().__init__("damage_detection_node")

        self.declare_parameter("image_topic", "/camera/wide/image_raw")
        self.declare_parameter("event_topic", "/damage/events")
        self.declare_parameter("location_topic", "/location/fix")
        self.declare_parameter("storage_dir", "data/damage_events")
        self.declare_parameter(
            "detect_model_path",
            "../ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt",
        )
        self.declare_parameter(
            "classify_model_path",
            "../ROADY_AI/models/edge/damage_presence_yolo11n_cls_best.pt",
        )
        self.declare_parameter("inference_device", "0")
        self.declare_parameter("image_size", 768)
        self.declare_parameter("use_damage_classifier", False)
        self.declare_parameter("detection_threshold", 0.15)
        self.declare_parameter("classification_threshold", 0.275)
        self.declare_parameter("confirm_count", 3)
        self.declare_parameter("confirm_window_sec", 2.0)
        self.declare_parameter("candidate_timeout_sec", 1.0)
        self.declare_parameter("tile_size", 320)
        self.declare_parameter("tile_overlap", 0.30)
        self.declare_parameter("process_every_n_frames", 1)
        self.declare_parameter("base_latitude", 37.5665)
        self.declare_parameter("base_longitude", 126.9780)
        self.declare_parameter("robot_id", 1)
        self.declare_parameter("description", "점자블록 파손 감지")

        storage_dir = Path(str(self.get_parameter("storage_dir").value))
        self._repository = DamageRepository(storage_dir)
        device = str(self.get_parameter("inference_device").value)
        self._detector = DamageDetector(
            model_path=str(self.get_parameter("detect_model_path").value),
            confidence=float(self.get_parameter("detection_threshold").value),
            image_size=int(self.get_parameter("image_size").value),
            device=device,
        )
        use_classifier = bool(self.get_parameter("use_damage_classifier").value)
        self._classifier = (
            DamageClassifier(
                model_path=str(self.get_parameter("classify_model_path").value),
                device=device,
            )
            if use_classifier
            else None
        )
        self._pipeline = DamageEventPipeline(
            detector=self._detector,
            classifier=self._classifier,
            detection_threshold=float(self.get_parameter("detection_threshold").value),
            classification_threshold=float(
                self.get_parameter("classification_threshold").value
            ),
            confirm_count=int(self.get_parameter("confirm_count").value),
            confirm_window_sec=float(self.get_parameter("confirm_window_sec").value),
            candidate_timeout_sec=float(
                self.get_parameter("candidate_timeout_sec").value
            ),
            tile_size=int(self.get_parameter("tile_size").value),
            tile_overlap=float(self.get_parameter("tile_overlap").value),
        )
        self._frame_count = 0
        self._event_count = 0
        self._latest_location: DamageLocation | None = None

        image_topic = str(self.get_parameter("image_topic").value)
        event_topic = str(self.get_parameter("event_topic").value)
        self._subscription = self.create_subscription(Image, image_topic, self._on_image, 10)
        self._location_subscription = self.create_subscription(
            NavSatFix,
            str(self.get_parameter("location_topic").value),
            self._on_location,
            qos_profile_sensor_data,
        )
        self._event_publisher = self.create_publisher(String, event_topic, 10)
        self.get_logger().info(
            f"Damage detection subscribed to {image_topic}; events stored in {storage_dir}; "
            f"mode={'detect+classifier' if use_classifier else 'YOLO26n detect only'}; "
            f"image_size={int(self.get_parameter('image_size').value)}"
        )

    def _on_image(self, msg: Image) -> None:
        self._frame_count += 1
        interval = max(1, int(self.get_parameter("process_every_n_frames").value))
        if (self._frame_count - 1) % interval:
            return

        image = self._image_msg_to_bgr(msg)
        now = self.get_clock().now().nanoseconds / 1_000_000_000
        try:
            location = self._current_location()
            ready_events = self._pipeline.process(
                image,
                now,
                location=(location.latitude, location.longitude),
            )
        except Exception as exc:
            self.get_logger().error(f"Damage inference failed: {exc}")
            return

        for ready in ready_events:
            self._save_ready_event(ready)

    def _save_ready_event(self, ready: ReadyDamageEvent) -> None:
        location = (
            DamageLocation(*ready.location)
            if ready.location is not None
            else self._current_location()
        )
        try:
            event = self._repository.save_event(
                images=[ready.original_image, ready.tactile_roi],
                location=location,
                robot_id=int(self.get_parameter("robot_id").value),
                description=str(self.get_parameter("description").value),
            )
        except Exception as exc:
            self._pipeline.retry(ready.candidate_id)
            self.get_logger().error(
                f"Failed to persist damage candidate {ready.candidate_id}: {exc}"
            )
            return

        self._pipeline.acknowledge(ready.candidate_id)
        self._event_count += 1
        self._event_publisher.publish(String(data=self._repository.to_json(event)))
        self.get_logger().info(
            f"Saved damage event {event.event_id}: observations={ready.observation_count}, "
            f"score={ready.best_score:.3f}"
        )

    def _on_location(self, msg: NavSatFix) -> None:
        if not (-90.0 <= msg.latitude <= 90.0 and -180.0 <= msg.longitude <= 180.0):
            self.get_logger().warn("Ignored invalid location fix")
            return
        self._latest_location = DamageLocation(msg.latitude, msg.longitude)

    def _current_location(self) -> DamageLocation:
        if self._latest_location is not None:
            return self._latest_location
        return DamageLocation(
            latitude=float(self.get_parameter("base_latitude").value),
            longitude=float(self.get_parameter("base_longitude").value),
        )

    def destroy_node(self):
        if self._classifier is not None:
            self._classifier.close()
        self._detector.close()
        return super().destroy_node()

    @staticmethod
    def _image_msg_to_bgr(msg: Image) -> np.ndarray:
        if msg.encoding != "bgr8":
            raise ValueError(f"Unsupported image encoding: {msg.encoding}")
        image = np.frombuffer(msg.data, dtype=np.uint8)
        rows = image.reshape((msg.height, msg.step))
        return rows[:, : msg.width * 3].reshape((msg.height, msg.width, 3)).copy()


def main(args=None):
    rclpy.init(args=args)
    node = DamageDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
