from __future__ import annotations

import json
import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, String

from perception.algorithms.lower_limb_detector import LowerLimbDetector
from perception.benchmark import BenchmarkRecorder, jetson_temperature_c


class ObstacleDetectionNode(Node):
    def __init__(self) -> None:
        super().__init__("obstacle_detection_node")
        self.declare_parameter("model_path", "")
        self.declare_parameter("image_topic", "/camera/obstacle/image_raw")
        self.declare_parameter("detected_topic", "/obstacle/human_lower_limb_detected")
        self.declare_parameter("detections_topic", "/obstacle/lower_limb_detections")
        self.declare_parameter("confidence", 0.25)
        self.declare_parameter("image_size", 640)
        self.declare_parameter("device", "0")
        self.declare_parameter("benchmark_duration_sec", 0.0)
        self.declare_parameter("benchmark_report", "reports/obstacle_benchmark.json")
        self.declare_parameter("log_interval_sec", 5.0)

        model_path = str(self.get_parameter("model_path").value)
        if not model_path:
            raise ValueError("ROS parameter 'model_path' is required")
        self._image_topic = str(self.get_parameter("image_topic").value)
        self._detector = LowerLimbDetector(
            model_path=model_path,
            confidence=float(self.get_parameter("confidence").value),
            image_size=int(self.get_parameter("image_size").value),
            device=str(self.get_parameter("device").value),
        )
        self._model_path = model_path
        self._last_log = time.monotonic()
        self._recorder = BenchmarkRecorder(
            duration_sec=float(self.get_parameter("benchmark_duration_sec").value),
            report_path=str(self.get_parameter("benchmark_report").value),
        )

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self._subscription = self.create_subscription(Image, self._image_topic, self._on_image, qos)
        self._detected_publisher = self.create_publisher(
            Bool, str(self.get_parameter("detected_topic").value), 10
        )
        self._detections_publisher = self.create_publisher(
            String, str(self.get_parameter("detections_topic").value), 10
        )
        self.get_logger().info(f"Lower-limb model={model_path}, input={self._image_topic}")

    def _on_image(self, msg: Image) -> None:
        started = time.perf_counter()
        try:
            detections, _ = self._detector.detect(self._image_msg_to_bgr(msg))
        except Exception as exc:
            self.get_logger().error(f"Inference failed: {exc}")
            return
        latency_ms = (time.perf_counter() - started) * 1000.0
        temperature = jetson_temperature_c()
        self._recorder.add(latency_ms, temperature)

        self._detected_publisher.publish(Bool(data=bool(detections)))
        payload = {
            "stamp": {"sec": msg.header.stamp.sec, "nanosec": msg.header.stamp.nanosec},
            "detected": bool(detections),
            "latency_ms": latency_ms,
            "detections": [d.__dict__ for d in detections],
        }
        self._detections_publisher.publish(String(data=json.dumps(payload, ensure_ascii=False)))

        now = time.monotonic()
        if now - self._last_log >= float(self.get_parameter("log_interval_sec").value):
            summary = self._recorder.summary(self._model_path, self._image_topic)
            temp_text = "n/a" if temperature is None else f"{temperature:.1f}C"
            self.get_logger().info(
                f"fps={summary['end_to_end_fps']:.2f}, latency={latency_ms:.1f}ms, "
                f"detections={len(detections)}, temperature={temp_text}"
            )
            self._last_log = now

        if self._recorder.due and not self._recorder.completed:
            report = self._recorder.write(self._model_path, self._image_topic)
            self.get_logger().info(
                f"Benchmark complete: {self._recorder.report_path} "
                f"({report['end_to_end_fps']:.2f} FPS)"
            )

    @staticmethod
    def _image_msg_to_bgr(msg: Image) -> np.ndarray:
        if msg.encoding not in {"bgr8", "rgb8"}:
            raise ValueError(f"Unsupported image encoding: {msg.encoding}")
        row = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.step))
        image = row[:, : msg.width * 3].reshape((msg.height, msg.width, 3)).copy()
        return image if msg.encoding == "bgr8" else image[:, :, ::-1].copy()

    def destroy_node(self) -> bool:
        if self._recorder.latencies_ms and not self._recorder.completed:
            self._recorder.write(self._model_path, self._image_topic)
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ObstacleDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
