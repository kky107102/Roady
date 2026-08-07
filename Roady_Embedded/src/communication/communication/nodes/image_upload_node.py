from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool

from communication.clients.http_client import DamageHttpClient
from storage.damage_repository import DamageRepository


class ImageUploadNode(Node):
    def __init__(self):
        super().__init__("image_upload_node")

        self.declare_parameter("base_url", "https://i15a404.p.ssafy.io")
        self.declare_parameter("access_token", "")
        self.declare_parameter("storage_dir", "data/damage_events")
        self.declare_parameter("upload_interval_sec", 10.0)
        self.declare_parameter("upload_enabled", False)
        self.declare_parameter("arrival_topic", "/driving/finished")

        self._repository = DamageRepository(str(self.get_parameter("storage_dir").value))
        self._client = DamageHttpClient(
            base_url=str(self.get_parameter("base_url").value),
            access_token=str(self.get_parameter("access_token").value) or None,
        )

        self._arrival_active = False
        arrival_qos = QoSProfile(depth=1)
        arrival_qos.reliability = ReliabilityPolicy.RELIABLE
        arrival_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self._arrival_subscription = self.create_subscription(
            Bool,
            str(self.get_parameter("arrival_topic").value),
            self._on_arrival,
            arrival_qos,
        )

        interval = float(self.get_parameter("upload_interval_sec").value)
        self._timer = self.create_timer(max(interval, 1.0), self._upload_pending_events)
        self.get_logger().info(
            "Image upload node ready. Pending events will be uploaded after "
            f"arrival on {self.get_parameter('arrival_topic').value}."
        )

    def _on_arrival(self, msg: Bool) -> None:
        if not msg.data:
            self._arrival_active = False
            return
        if self._arrival_active:
            return

        self._arrival_active = True
        self.get_logger().info("Station arrival received; uploading pending events.")
        self._upload_pending_events()

    def _upload_pending_events(self) -> None:
        if (
            not self._arrival_active
            or not bool(self.get_parameter("upload_enabled").value)
        ):
            return

        for event_path in self._repository.list_pending_events():
            event = self._repository.load_event_file(event_path)

            local_image_paths = self._repository.resolve_image_paths(event)
            upload_image_paths = self._repository.resolve_upload_image_paths(event)
            if (
                not local_image_paths
                or not all(path.exists() for path in local_image_paths)
                or not upload_image_paths
                or not all(path.exists() for path in upload_image_paths)
            ):
                self.get_logger().warn(f"Skipping event without image: {event_path}")
                continue

            try:
                self._client.upload_damage(
                    robot_id=int(event["robotId"]),
                    description=str(event["description"]),
                    latitude=float(event["latitude"]),
                    longitude=float(event["longitude"]),
                    captured_at=str(event["capturedAt"]),
                    image_paths=upload_image_paths,
                )
            except Exception as exc:
                self.get_logger().warn(f"Failed to upload {event_path.name}: {exc}")
                continue

            self._repository.delete_event(event_path)
            self.get_logger().info(f"Uploaded damage event: {event['eventId']}")


def main(args=None):
    rclpy.init(args=args)
    node = ImageUploadNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
