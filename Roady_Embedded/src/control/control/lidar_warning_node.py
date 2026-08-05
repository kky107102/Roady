import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool


class LidarWarningNode(Node):

    def __init__(self):
        super().__init__('lidar_warning_node')

        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('warning_topic', '/obstacle/lidar_detected')
        self.declare_parameter('stop_threshold', 0.50)
        self.declare_parameter('min_valid_distance', 0.08)

        # 라이다 구독 (QoS 호환성 적용)
        self.scan_sub = self.create_subscription(
            LaserScan,
            str(self.get_parameter('scan_topic').value),
            self.scan_callback,
            qos_profile_sensor_data,
        )

        # 비상 정지 명령 발행자 (Bool)
        self.stop_pub = self.create_publisher(
            Bool, str(self.get_parameter('warning_topic').value), 10
        )

        self.STOP_THRESHOLD = float(self.get_parameter('stop_threshold').value)
        self.MIN_VALID_DIST = float(
            self.get_parameter('min_valid_distance').value
        )

        self.get_logger().info(
            '✅ LiDAR 장애물 감지 노드가 시작되었습니다. '
            f'(기준: {self.STOP_THRESHOLD:.2f}m)'
        )

    def scan_callback(self, msg: LaserScan):
        # inf, nan, 노이즈 제외한 거리 계산
        valid_ranges = [
            r
            for r in msg.ranges
            if not math.isinf(r) and not math.isnan(r) and r >= self.MIN_VALID_DIST
        ]

        stop_msg = Bool()

        if not valid_ranges:
            # 안전을 위해 데이터가 불분명할 때는 비상정지 미발행
            stop_msg.data = False
            self.stop_pub.publish(stop_msg)
            return

        min_dist = min(valid_ranges)

        # 0.5m 이내 접근 확인
        if min_dist <= self.STOP_THRESHOLD:
            stop_msg.data = True
            self.get_logger().warn(
                '🚨 [LiDAR] 장애물 감지! '
                f'(현재: {min_dist*100:.1f}cm)',
                throttle_duration_sec=0.2,
            )
        else:
            stop_msg.data = False

        # 비상 정지 상태 토픽 발행
        self.stop_pub.publish(stop_msg)


def main(args=None):
    rclpy.init(args=args)
    node = LidarWarningNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
