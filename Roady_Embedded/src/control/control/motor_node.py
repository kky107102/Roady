import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
from control.motor_driver import MotorDriver


class MotorNode(Node):

    def __init__(self):
        super().__init__('motor_node')

        # 하드웨어 모터 드라이버 객체 생성 (I2C 0x60, 0x40)
        self.driver = MotorDriver()

        # 1. 키보드/라인트레이서 제어 명령 구독 (/cmd_vel)
        self.cmd_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_callback, 10
        )

        # 2. 비상 정지 토픽 구독
        self.emergency_sub = self.create_subscription(
            Bool, '/emergency_stop', self.emergency_callback, 10
        )

        self.is_emergency_stop = False
        self.is_motor_stopped = True

        # 안전을 위한 워치독 타이머 (0.5s 동안 명령 없으면 정지)
        self.watchdog_timer = self.create_timer(0.5, self.watchdog_callback)
        self.last_cmd_time = self.get_clock().now()

        self.get_logger().info('✅ Motor Node가 시작되었습니다.')

    def emergency_callback(self, msg: Bool):
        was_emergency_stop = self.is_emergency_stop
        self.is_emergency_stop = msg.data

        # 비상 정지 신호 수신 즉시 모터 정지
        if self.is_emergency_stop:
            if not was_emergency_stop:
                self._log_stop_request(
                    '/emergency_stop', '비상 정지 요청'
                )
            self.driver.stop()
            self.is_motor_stopped = True

    def cmd_callback(self, msg: Twist):
        self.last_cmd_time = self.get_clock().now()

        # 조향(Steering) 제어 (angular.z 값 전달)
        steering_angle = msg.angular.z
        self.driver.set_steering_angle(steering_angle)

        # 🚨 비상 정지 상태일 때: 전/후진 명령 무시하고 정지
        if self.is_emergency_stop:
            self.get_logger().warn(
                '⛔ 장애물 근접! 모터 제어가 차단되었습니다.',
                throttle_duration_sec=0.5,
            )
            self.driver.move(0.0)
            self.is_motor_stopped = True
        else:
            # 정상 상태: linear.x 값을 move() 메서드로 전달
            throttle_value = msg.linear.x
            if throttle_value == 0.0 and not self.is_motor_stopped:
                self._log_stop_request('/cmd_vel', '속도 0 명령')
            self.driver.move(throttle_value)
            self.is_motor_stopped = throttle_value == 0.0

    def watchdog_callback(self):
        # 0.5초 이상 제어 명령이 안 들어오면 안전 정지
        dt = (self.get_clock().now() - self.last_cmd_time).nanoseconds / 1e9
        if dt > 0.5:
            if not self.is_motor_stopped:
                self.get_logger().warn(
                    '🛑 정지 요청: /motor_node 워치독 '
                    '(0.5초 동안 /cmd_vel 미수신)'
                )
            self.driver.move(0.0)
            self.is_motor_stopped = True

    def _log_stop_request(self, topic_name, reason):
        """Log the nodes currently publishing the stop command topic."""
        publisher_names = []
        for info in self.get_publishers_info_by_topic(topic_name):
            namespace = info.node_namespace.rstrip('/')
            full_name = f'{namespace}/{info.node_name}'
            publisher_names.append(full_name or f'/{info.node_name}')

        publishers = ', '.join(sorted(set(publisher_names)))
        if not publishers:
            publishers = '발행 노드 확인 불가'
        self.get_logger().warn(
            f'🛑 정지 요청: {publishers} '
            f'(토픽: {topic_name}, 사유: {reason})'
        )


def main(args=None):
    rclpy.init(args=args)
    node = MotorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # 종료 시 모든 모터 및 서보 완전 정지
        node.driver.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
