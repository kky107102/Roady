from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, NavSatFix
from std_msgs.msg import String

from perception.algorithms.damage_event_pipeline import DamageEventPipeline, ReadyDamageEvent
from perception.algorithms.person_pipeline_test_adapter import (
    PersonAsTactileDetector,
)
from storage.damage_repository import DamageLocation, DamageRepository


class PersonDamagePipelineTestNode(Node):
    """End-to-end damage-pipeline smoke test using the lower-limb model."""

    def __init__(self) -> None:
        super().__init__("person_damage_pipeline_test_node")
        self.declare_parameter("image_topic", "/camera/tactile/image_raw")
        self.declare_parameter("annotated_topic", "/damage/test/annotated")
        self.declare_parameter("event_topic", "/damage/test/events")
        self.declare_parameter("location_topic", "/location/fix")
        self.declare_parameter("storage_dir", "data/person_damage_test_events")
        self.declare_parameter("model_path", "artifacts/obstacle_lower_limb/best.engine")
        self.declare_parameter("device", "0")
        self.declare_parameter("detect_confidence", 0.15)
        self.declare_parameter("confirm_count", 3)
        self.declare_parameter("confirm_window_sec", 2.0)
        self.declare_parameter("candidate_timeout_sec", 1.0)
        self.declare_parameter("base_latitude", 37.5012748)
        self.declare_parameter("base_longitude", 127.039625)

        self._repository = DamageRepository(
            Path(str(self.get_parameter("storage_dir").value))
        )
        self._detector = PersonAsTactileDetector(
            model_path=str(self.get_parameter("model_path").value),
            confidence=float(self.get_parameter("detect_confidence").value),
            device=str(self.get_parameter("device").value),
        )
        self._pipeline = DamageEventPipeline(
            detector=self._detector,
            detection_threshold=float(self.get_parameter("detect_confidence").value),
            confirm_count=int(self.get_parameter("confirm_count").value),
            confirm_window_sec=float(self.get_parameter("confirm_window_sec").value),
            candidate_timeout_sec=float(
                self.get_parameter("candidate_timeout_sec").value
            ),
        )
        self._latest_location: DamageLocation | None = None
        self._frame_count = 0

        self._image_subscription = self.create_subscription(
            Image,
            str(self.get_parameter("image_topic").value),
            self._on_image,
            qos_profile_sensor_data,
        )
        self._location_subscription = self.create_subscription(
            NavSatFix,
            str(self.get_parameter("location_topic").value),
            self._on_location,
            qos_profile_sensor_data,
        )
        self._annotated_publisher = self.create_publisher(
            Image,
            str(self.get_parameter("annotated_topic").value),
            qos_profile_sensor_data,
        )
        self._event_publisher = self.create_publisher(
            String,
            str(self.get_parameter("event_topic").value),
            10,
        )
        self.get_logger().warn(
            "TEST MODE: lower-limb detections are routed through the damage pipeline; "
            "events are isolated from the production upload directory"
        )

    def _on_image(self, msg: Image) -> None:
        frame = self._image_msg_to_bgr(msg)
        now = self.get_clock().now().nanoseconds / 1_000_000_000
        location = self._current_location()
        try:
            ready = self._pipeline.process(
                frame,
                timestamp=now,
                location=(location.latitude, location.longitude),
            )
        except Exception as exc:
            self.get_logger().error(f"Person pipeline test failed: {exc}")
            return

        self._frame_count += 1
        annotated = self._draw(frame)
        self._annotated_publisher.publish(self._bgr_to_image_msg(annotated, msg))
        for event in ready:
            self._save_event(event)

    def _draw(self, frame: np.ndarray) -> np.ndarray:
        annotated = frame.copy()
        for detection in self._detector.last_detections:
            x1, y1, x2, y2 = (int(value) for value in detection.xyxy)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 140, 0), 2)
            cv2.putText(
                annotated,
                f"FIRST DETECT {detection.confidence:.2f}",
                (x1, min(annotated.shape[0] - 8, y2 + 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 140, 0),
                2,
            )
        for candidate in self._pipeline.candidates:
            x1, y1, x2, y2 = (int(value) for value in candidate.last_bbox)
            if candidate.ready_emitted:
                status, color = "READY", (255, 0, 255)
            elif candidate.confirmed:
                status, color = "CONFIRMED", (0, 200, 0)
            else:
                status, color = "TRACKING", (0, 165, 255)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 4)
            cv2.putText(
                annotated,
                f"TEST ID={candidate.candidate_id} {status} "
                f"obs={len(candidate.observation_times)} score={candidate.best_score:.2f}",
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2,
            )
        cv2.putText(
            annotated,
            "PERSON -> DAMAGE PIPELINE TEST",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (0, 0, 255),
            2,
        )
        return annotated

    def _save_event(self, ready: ReadyDamageEvent) -> None:
        location = (
            DamageLocation(*ready.location)
            if ready.location is not None
            else self._current_location()
        )
        try:
            event = self._repository.save_event(
                images=[ready.original_image],
                location=location,
                robot_id=1,
                description="TEST: person through damage pipeline",
            )
        except Exception as exc:
            self._pipeline.retry(ready.candidate_id)
            self.get_logger().error(f"Failed to save test event: {exc}")
            return
        self._pipeline.acknowledge(ready.candidate_id)
        self._event_publisher.publish(String(data=self._repository.to_json(event)))
        self.get_logger().warn(
            f"TEST EVENT SAVED: {event.event_id}, observations={ready.observation_count}, "
            f"location=({location.latitude:.7f}, {location.longitude:.7f})"
        )

    def _on_location(self, msg: NavSatFix) -> None:
        if -90.0 <= msg.latitude <= 90.0 and -180.0 <= msg.longitude <= 180.0:
            self._latest_location = DamageLocation(msg.latitude, msg.longitude)

    def _current_location(self) -> DamageLocation:
        return self._latest_location or DamageLocation(
            latitude=float(self.get_parameter("base_latitude").value),
            longitude=float(self.get_parameter("base_longitude").value),
        )

    def destroy_node(self):
        self._detector.close()
        return super().destroy_node()

    @staticmethod
    def _image_msg_to_bgr(msg: Image) -> np.ndarray:
        if msg.encoding != "bgr8":
            raise ValueError(f"Unsupported image encoding: {msg.encoding}")
        image = np.frombuffer(msg.data, dtype=np.uint8)
        rows = image.reshape((msg.height, msg.step))
        return rows[:, : msg.width * 3].reshape((msg.height, msg.width, 3)).copy()

    @staticmethod
    def _bgr_to_image_msg(image: np.ndarray, source: Image) -> Image:
        message = Image()
        message.header = source.header
        message.height, message.width = image.shape[:2]
        message.encoding = "bgr8"
        message.is_bigendian = False
        message.step = message.width * 3
        message.data = image.tobytes()
        return message


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PersonDamagePipelineTestNode()
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
