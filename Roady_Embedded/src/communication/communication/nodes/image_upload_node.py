from __future__ import annotations

import rclpy
from rclpy.node import Node

from communication.clients.http_client import DamageHttpClient
from storage.damage_repository import DamageRepository


class ImageUploadNode(Node):
    def __init__(self):
        super().__init__("image_upload_node")

        self.declare_parameter("base_url", "http://localhost:8080")
        self.declare_parameter("access_token", "")
        self.declare_parameter("storage_dir", "data/damage_events")
        self.declare_parameter("upload_interval_sec", 10.0)
        self.declare_parameter("upload_enabled", False)

        self._repository = DamageRepository(str(self.get_parameter("storage_dir").value))
        self._client = DamageHttpClient(
            base_url=str(self.get_parameter("base_url").value),
            access_token=str(self.get_parameter("access_token").value) or None,
        )

        interval = float(self.get_parameter("upload_interval_sec").value)
        self._timer = self.create_timer(max(interval, 1.0), self._upload_pending_events)
        self.get_logger().info("Image upload node ready. Set upload_enabled:=true to send events.")

    def _upload_pending_events(self) -> None:
        if not bool(self.get_parameter("upload_enabled").value):
            return

        for event_path in self._repository.list_pending_events():
            event = self._repository.load_event_file(event_path)

            image_paths = self._repository.resolve_image_paths(event)
            if not image_paths or not all(path.exists() for path in image_paths):
                self.get_logger().warn(f"Skipping event without image: {event_path}")
                continue

            try:
                self._client.upload_damage(
                    robot_id=int(event["robotId"]),
                    description=str(event["description"]),
                    latitude=float(event["latitude"]),
                    longitude=float(event["longitude"]),
                    captured_at=str(event["capturedAt"]),
                    image_paths=image_paths,
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
