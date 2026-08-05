from __future__ import annotations

import array
import hashlib
import time
from pathlib import Path

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, NavSatFix
from std_msgs.msg import String

from perception.algorithms.damage_detector import DamageDetector
from perception.algorithms.damage_event_pipeline import DamageEventPipeline, ReadyDamageEvent
from perception.benchmark import BenchmarkRecorder, jetson_temperature_c, percentile
from storage.damage_repository import DamageLocation, DamageRepository


class DamageDetectionNode(Node):
    def __init__(self):
        super().__init__("damage_detection_node")

        self.declare_parameter("image_topic", "/camera/wide/image_raw")
        self.declare_parameter("event_topic", "/damage/events")
        self.declare_parameter("annotated_topic", "/damage/annotated")
        self.declare_parameter("publish_annotated", True)
        self.declare_parameter("detection_only_mode", False)
        self.declare_parameter("location_topic", "/location/fix")
        self.declare_parameter("storage_dir", "data/damage_events")
        self.declare_parameter(
            "detect_model_path",
            "../ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt",
        )
        self.declare_parameter("inference_device", "0")
        self.declare_parameter("inference_image_size", 768)
        self.declare_parameter("detection_threshold", 0.15)
        self.declare_parameter("confirm_count", 3)
        self.declare_parameter("confirm_window_sec", 2.0)
        self.declare_parameter("min_confirm_duration_sec", 0.4)
        self.declare_parameter("min_observation_interval_sec", 0.1)
        self.declare_parameter("candidate_timeout_sec", 1.0)
        self.declare_parameter("reported_track_cooldown_sec", 5.0)
        self.declare_parameter("process_every_n_frames", 1)
        self.declare_parameter("benchmark_duration_sec", 0.0)
        self.declare_parameter(
            "benchmark_report", "reports/tactile_damage_pipeline_benchmark.json"
        )
        self.declare_parameter("benchmark_label", "yolo26n_camera_pipeline")
        self.declare_parameter(
            "benchmark_history", "reports/tactile_damage_pipeline_history.csv"
        )
        self.declare_parameter("benchmark_log_interval_sec", 5.0)
        self.declare_parameter("base_latitude", 37.5665)
        self.declare_parameter("base_longitude", 126.9780)
        self.declare_parameter("robot_id", 1)
        self.declare_parameter(
            "description", "로디 {robot_id}호 점자블록 파손 감지"
        )

        storage_dir = Path(str(self.get_parameter("storage_dir").value))
        self._repository = DamageRepository(storage_dir)
        device = str(self.get_parameter("inference_device").value)
        self._detector = DamageDetector(
            model_path=str(self.get_parameter("detect_model_path").value),
            confidence=float(self.get_parameter("detection_threshold").value),
            image_size=int(self.get_parameter("inference_image_size").value),
            device=device,
        )
        self._pipeline = DamageEventPipeline(
            detector=self._detector,
            detection_threshold=float(self.get_parameter("detection_threshold").value),
            confirm_count=int(self.get_parameter("confirm_count").value),
            confirm_window_sec=float(self.get_parameter("confirm_window_sec").value),
            min_confirm_duration_sec=float(
                self.get_parameter("min_confirm_duration_sec").value
            ),
            min_observation_interval_sec=float(
                self.get_parameter("min_observation_interval_sec").value
            ),
            candidate_timeout_sec=float(
                self.get_parameter("candidate_timeout_sec").value
            ),
            reported_track_cooldown_sec=float(
                self.get_parameter("reported_track_cooldown_sec").value
            ),
        )
        self._frame_count = 0
        self._event_count = 0
        self._latest_location: DamageLocation | None = None
        self._model_path = str(self.get_parameter("detect_model_path").value)
        self._image_topic = str(self.get_parameter("image_topic").value)
        self._publish_annotated = bool(
            self.get_parameter("publish_annotated").value
        )
        self._detection_only_mode = bool(
            self.get_parameter("detection_only_mode").value
        )
        self._recorder = BenchmarkRecorder(
            duration_sec=float(self.get_parameter("benchmark_duration_sec").value),
            report_path=str(self.get_parameter("benchmark_report").value),
            label=str(self.get_parameter("benchmark_label").value),
            history_path=str(self.get_parameter("benchmark_history").value),
        )
        self._stage_timings_ms: dict[str, list[float]] = {
            "image_conversion": [],
            "detection_tracking": [],
            "annotation_publish": [],
            "event_persistence": [],
            "callback_total": [],
        }
        self._last_benchmark_log = time.monotonic()
        self._benchmark_metadata: dict[str, object] = {
            "engine_sha256": self._sha256(self._model_path),
            "confidence": float(self.get_parameter("detection_threshold").value),
            "inference_image_size": int(
                self.get_parameter("inference_image_size").value
            ),
            "process_every_n_frames": int(
                self.get_parameter("process_every_n_frames").value
            ),
            "publish_annotated": self._publish_annotated,
            "detection_only_mode": self._detection_only_mode,
            "confirm_count": int(self.get_parameter("confirm_count").value),
            "confirm_window_sec": float(
                self.get_parameter("confirm_window_sec").value
            ),
            "candidate_timeout_sec": float(
                self.get_parameter("candidate_timeout_sec").value
            ),
            "min_confirm_duration_sec": float(
                self.get_parameter("min_confirm_duration_sec").value
            ),
            "min_observation_interval_sec": float(
                self.get_parameter("min_observation_interval_sec").value
            ),
            "reported_track_cooldown_sec": float(
                self.get_parameter("reported_track_cooldown_sec").value
            ),
            "latency_scope": "camera ROS stamp to callback completion",
        }

        image_topic = self._image_topic
        event_topic = str(self.get_parameter("event_topic").value)
        self._subscription = self.create_subscription(
            Image,
            image_topic,
            self._on_image,
            qos_profile_sensor_data,
        )
        self._location_subscription = self.create_subscription(
            NavSatFix,
            str(self.get_parameter("location_topic").value),
            self._on_location,
            qos_profile_sensor_data,
        )
        self._event_publisher = self.create_publisher(String, event_topic, 10)
        self._annotated_publisher = self.create_publisher(
            Image,
            str(self.get_parameter("annotated_topic").value),
            qos_profile_sensor_data,
        )
        self.get_logger().info(
            f"Damage detection subscribed to {image_topic}; events stored in {storage_dir}"
        )

    def _on_image(self, msg: Image) -> None:
        self._frame_count += 1
        interval = max(1, int(self.get_parameter("process_every_n_frames").value))
        if (self._frame_count - 1) % interval:
            return

        callback_started = time.perf_counter()
        stage_started = callback_started
        image = self._image_msg_to_bgr(msg)
        self._stage_timings_ms["image_conversion"].append(
            (time.perf_counter() - stage_started) * 1000.0
        )
        now = self.get_clock().now().nanoseconds / 1_000_000_000
        try:
            location = self._current_location()
            stage_started = time.perf_counter()
            if self._detection_only_mode:
                detections, _ = self._detector.detect(image)
                ready_events = []
            else:
                ready_events = self._pipeline.process(
                    image,
                    now,
                    location=(location.latitude, location.longitude),
                )
                detections = list(self._pipeline.last_detections)
            self._stage_timings_ms["detection_tracking"].append(
                (time.perf_counter() - stage_started) * 1000.0
            )
            stage_started = time.perf_counter()
            if self._publish_annotated:
                annotated = self._draw_annotated(image, detections)
                self._annotated_publisher.publish(
                    self._bgr_to_image_msg(annotated, msg)
                )
            self._stage_timings_ms["annotation_publish"].append(
                (time.perf_counter() - stage_started) * 1000.0
            )
        except Exception as exc:
            self.get_logger().error(f"Damage inference failed: {exc}")
            return

        stage_started = time.perf_counter()
        for ready in ready_events:
            self._save_ready_event(ready)
        self._stage_timings_ms["event_persistence"].append(
            (time.perf_counter() - stage_started) * 1000.0
        )
        callback_total_ms = (time.perf_counter() - callback_started) * 1000.0
        self._stage_timings_ms["callback_total"].append(callback_total_ms)
        completed_ros_ns = self.get_clock().now().nanoseconds
        stamp_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
        camera_to_complete_ms = (
            (completed_ros_ns - stamp_ns) / 1_000_000.0
            if stamp_ns > 0 and completed_ros_ns >= stamp_ns
            else callback_total_ms
        )
        damage_count = sum(
            detection.label == "damage_candidate"
            for detection in detections
        )
        self._benchmark_metadata.update(
            {
                "camera_width": msg.width,
                "camera_height": msg.height,
                "camera_encoding": msg.encoding,
                "stage_timings_ms": self._stage_summary(),
            }
        )
        temperature = jetson_temperature_c()
        self._recorder.add(camera_to_complete_ms, temperature, damage_count)
        self._log_or_finish_benchmark(callback_total_ms, temperature)

    def _log_or_finish_benchmark(
        self, callback_total_ms: float, temperature: float | None
    ) -> None:
        now = time.monotonic()
        interval = float(self.get_parameter("benchmark_log_interval_sec").value)
        if interval > 0 and now - self._last_benchmark_log >= interval:
            summary = self._recorder.summary(self._model_path, self._image_topic)
            temperature_text = "n/a" if temperature is None else f"{temperature:.1f}C"
            self.get_logger().info(
                f"pipeline fps={summary['end_to_end_fps']:.2f}, "
                f"callback={callback_total_ms:.1f}ms, "
                f"camera-to-complete={summary['latency_ms']['mean']:.1f}ms, "
                f"temperature={temperature_text}"
            )
            self._last_benchmark_log = now

        if self._recorder.due and not self._recorder.completed:
            self._benchmark_metadata["stage_timings_ms"] = self._stage_summary()
            report = self._recorder.write(
                self._model_path, self._image_topic, self._benchmark_metadata
            )
            self.get_logger().info(
                f"Benchmark complete: {self._recorder.report_path} "
                f"({report['end_to_end_fps']:.2f} FPS)"
            )

    def _stage_summary(self) -> dict[str, dict[str, float]]:
        return {
            name: {
                "mean": sum(values) / len(values) if values else 0.0,
                "p50": percentile(values, 50),
                "p95": percentile(values, 95),
                "max": max(values, default=0.0),
            }
            for name, values in self._stage_timings_ms.items()
        }

    def _save_ready_event(self, ready: ReadyDamageEvent) -> None:
        location = (
            DamageLocation(*ready.location)
            if ready.location is not None
            else self._current_location()
        )
        robot_id = int(self.get_parameter("robot_id").value)
        description = str(self.get_parameter("description").value).replace(
            "{robot_id}", str(robot_id)
        )
        try:
            event = self._repository.save_event(
                images=[ready.original_image, ready.tactile_roi],
                location=location,
                robot_id=robot_id,
                description=description,
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
        if self._recorder.latencies_ms and not self._recorder.completed:
            self._benchmark_metadata["stage_timings_ms"] = self._stage_summary()
            self._recorder.write(
                self._model_path, self._image_topic, self._benchmark_metadata
            )
        self._detector.close()
        return super().destroy_node()

    def _draw_annotated(self, frame: np.ndarray, detections) -> np.ndarray:
        annotated = frame.copy()
        for detection in detections:
            if self._detection_only_mode and detection.label != "damage_candidate":
                continue
            x1, y1, x2, y2 = (int(round(value)) for value in detection.xyxy)
            if detection.label == "damage_candidate":
                color = (255, 0, 0)
            else:
                color = (0, 255, 255)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated,
                f"{detection.label} {detection.confidence:.2f}",
                (x1, max(24, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        if self._detection_only_mode:
            return annotated

        for candidate in self._pipeline.candidates:
            x1, y1, x2, y2 = (int(round(value)) for value in candidate.last_bbox)
            if candidate.reported:
                status, color = "REPORTED", (128, 128, 128)
            elif candidate.ready_emitted:
                status, color = "READY", (255, 0, 255)
            elif candidate.confirmed:
                status, color = "CONFIRMED", (0, 200, 0)
            else:
                status, color = "TRACKING", (0, 165, 255)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 4)
            cv2.putText(
                annotated,
                f"ID={candidate.candidate_id} {status} "
                f"obs={len(candidate.observation_times)}",
                (x1, min(annotated.shape[0] - 8, y2 + 22)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )
        return annotated

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
        message.data = array.array("B", image.tobytes())
        return message

    @staticmethod
    def _sha256(path: str) -> str:
        digest = hashlib.sha256()
        with Path(path).open("rb") as model_file:
            for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


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
