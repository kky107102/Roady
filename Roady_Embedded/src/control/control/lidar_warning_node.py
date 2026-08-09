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
        self.declare_parameter('min_detection_distance', 0.20)
        self.declare_parameter('max_detection_distance', 0.50)
        self.declare_parameter('front_exclusion_angle_deg', 90.0)

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

        self.MIN_DETECTION_DISTANCE = float(
            self.get_parameter('min_detection_distance').value
        )
        self.MAX_DETECTION_DISTANCE = float(
            self.get_parameter('max_detection_distance').value
        )
        front_exclusion_angle_deg = min(
            360.0,
            max(
                0.0,
                float(self.get_parameter('front_exclusion_angle_deg').value),
            ),
        )
        self.FRONT_EXCLUSION_HALF_ANGLE_RAD = math.radians(
            front_exclusion_angle_deg / 2.0
        )
        self.get_logger().info(
            '✅ LiDAR 장애물 감지 노드가 시작되었습니다. '
            f'(범위: {self.MIN_DETECTION_DISTANCE:.2f}~'
            f'{self.MAX_DETECTION_DISTANCE:.2f}m, '
            f'전방 제외 각도: '
            f'±{front_exclusion_angle_deg / 2.0:.1f}°)'
        )

    def scan_callback(self, msg: LaserScan):
        # 전방 90도(-45~+45도)를 제외한 좌·우측면과 후방의
        # 20~50cm 측정값만 검사한다.
        obstacle_ranges = []
        for index, distance in enumerate(msg.ranges):
            angle = msg.angle_min + index * msg.angle_increment
            normalized_angle = math.atan2(math.sin(angle), math.cos(angle))
            if (
                abs(normalized_angle)
                > self.FRONT_EXCLUSION_HALF_ANGLE_RAD + 1e-9
                and math.isfinite(distance)
                and self.MIN_DETECTION_DISTANCE
                <= distance
                <= self.MAX_DETECTION_DISTANCE
            ):
                obstacle_ranges.append(distance)

        stop_msg = Bool()

        stop_msg.data = bool(obstacle_ranges)
        if obstacle_ranges:
            min_dist = min(obstacle_ranges)
            self.get_logger().warn(
                '🚨 [LiDAR] 장애물 감지! '
                f'(현재: {min_dist*100:.1f}cm)',
                throttle_duration_sec=0.2,
            )
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
