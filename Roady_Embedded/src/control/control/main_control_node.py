#!/usr/bin/env python3
from collections import deque
import math
import time

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String


class MainControlNode(Node):

    def __init__(self):
        super().__init__('main_control_node')

        # Subscriptions
        self.sub_tactile = self.create_subscription(
            String, '/tactile/block_type', self.tactile_callback, 10
        )
        self.sub_offset = self.create_subscription(
            Float32, '/tactile/edge_offset', self.offset_callback, 10
        )
        self.sub_lidar = self.create_subscription(
            Bool, '/obstacle_warning', self.lidar_callback, 10
        )

        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)

        # Parameters
        self.declare_parameter('startup_delay', 5.0)
        self.declare_parameter('startup_crawl_duration', 1.0)
        self.declare_parameter('startup_crawl_speed', 0.5)
        self.declare_parameter('drive_speed', 0.65)
        self.declare_parameter('reverse_speed', 0.5)
        self.declare_parameter('steering_speed_boost', 0.05)
        self.declare_parameter('kp', 0.004)
        self.declare_parameter('max_steer', 0.75)
        self.declare_parameter('left_steering_gain', 1.30)
        self.declare_parameter('steering_deadband_px', 8.0)
        self.declare_parameter('steering_filter_alpha', 0.35)
        self.declare_parameter('offset_timeout', 1.0)
        self.declare_parameter('steering_sign', -1.0)
        self.declare_parameter('backup_duration', 1.5)
        self.declare_parameter('corner_turn_duration', 2.0)
        self.declare_parameter('corner_steer', 0.75)
        self.declare_parameter('corner_steering_sign', 1.0)
        self.declare_parameter('left_edge_stop_duration', 0.5)
        self.declare_parameter('left_edge_backup_duration', 1.0)
        self.declare_parameter('left_edge_extreme_backup_multiplier', 2.0)
        self.declare_parameter('left_edge_turn_duration', 1.0)
        self.declare_parameter('left_edge_recovery_steer', 0.75)

        self.startup_delay = max(
            0.0,
            float(self.get_parameter('startup_delay').value),
        )
        self.startup_crawl_duration = max(
            0.0,
            float(self.get_parameter('startup_crawl_duration').value),
        )
        self.startup_crawl_speed = abs(
            float(self.get_parameter('startup_crawl_speed').value)
        )
        self.drive_speed = min(
            1.0,
            abs(float(self.get_parameter('drive_speed').value)),
        )
        self.reverse_speed = min(
            1.0,
            abs(float(self.get_parameter('reverse_speed').value)),
        )
        self.steering_speed_boost = max(
            0.0,
            float(self.get_parameter('steering_speed_boost').value),
        )
        self.kp = float(self.get_parameter('kp').value)
        self.max_steer = abs(float(self.get_parameter('max_steer').value))
        self.left_steering_gain = max(
            0.0,
            float(self.get_parameter('left_steering_gain').value),
        )
        self.steering_deadband_px = float(
            self.get_parameter('steering_deadband_px').value
        )
        self.steering_filter_alpha = float(
            self.get_parameter('steering_filter_alpha').value
        )
        self.offset_timeout = float(self.get_parameter('offset_timeout').value)
        self.steering_sign = float(self.get_parameter('steering_sign').value)
        self.backup_duration = float(self.get_parameter('backup_duration').value)
        self.corner_turn_duration = float(
            self.get_parameter('corner_turn_duration').value
        )
        self.corner_steer = abs(float(self.get_parameter('corner_steer').value))
        self.corner_steering_sign = float(
            self.get_parameter('corner_steering_sign').value
        )
        self.left_edge_stop_duration = max(
            0.0,
            float(self.get_parameter('left_edge_stop_duration').value),
        )
        self.left_edge_backup_duration = max(
            0.0,
            float(self.get_parameter('left_edge_backup_duration').value),
        )
        self.left_edge_extreme_backup_multiplier = max(
            1.0,
            float(
                self.get_parameter('left_edge_extreme_backup_multiplier').value
            ),
        )
        self.left_edge_turn_duration = max(
            0.0,
            float(self.get_parameter('left_edge_turn_duration').value),
        )
        self.left_edge_recovery_steer = min(
            1.0,
            abs(float(self.get_parameter('left_edge_recovery_steer').value)),
        )

        # FSM States
        self.current_state = 'LINE_TRACE'
        self.current_block_type = 'UNKNOWN'
        self.current_offset = 999.0
        self.offset_history = deque(maxlen=5)
        self.last_offset_time = 0.0
        self.filtered_steering = 0.0
        self.is_obstacle_detected = False
        self.backup_start_time = 0.0
        self.corner_turn_start_time = 0.0
        self.corner_direction = 0.0
        self.corner_latched = False
        self.left_edge_recovery_start_time = 0.0
        self.left_edge_recovery_latched = False
        self.left_edge_active_steer = self.left_edge_recovery_steer
        self.left_edge_active_backup_duration = self.left_edge_backup_duration
        self.startup_start_time = time.monotonic()
        self.startup_complete = False
        self.drive_start_time = 0.0

        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info(
            f'⏳ 카메라 준비를 위해 {self.startup_delay:.1f}초간 정지합니다.'
        )

    def lidar_callback(self, msg: Bool):
        self.is_obstacle_detected = msg.data

    def maneuver_is_active(self):
        return self.current_state in (
            'LEFT_EDGE_STOP',
            'LEFT_EDGE_BACKUP',
            'LEFT_EDGE_TURN',
            'CORNER_BACKUP',
            'CORNER_TURN',
        )

    def tactile_callback(self, msg: String):
        # 후진·조향 기동 중에는 새 비전 판단으로 현재 동작을 덮어쓰지 않는다.
        if self.maneuver_is_active():
            return

        self.current_block_type = msg.data

        startup_valid_block_types = (
            'STRAIGHT',
            'LEFT_EDGE_LIMIT',
            'LEFT_EDGE_CRITICAL',
            'LEFT_EDGE_EXTREME',
        )
        if (
            not self.startup_complete
            and self.current_block_type not in startup_valid_block_types
        ):
            self.offset_history.clear()
            self.current_offset = 999.0

        if self.current_block_type == 'STRAIGHT' and self.current_state == 'LINE_TRACE':
            self.corner_latched = False
            self.left_edge_recovery_latched = False

        self.try_start_left_edge_recovery()
        self.try_start_corner_maneuver()

    def try_start_left_edge_recovery(self):
        if (
            self.startup_complete
            and self.current_block_type in (
                'LEFT_EDGE_LIMIT',
                'LEFT_EDGE_CRITICAL',
                'LEFT_EDGE_EXTREME',
            )
            and self.current_state == 'LINE_TRACE'
            and not self.is_obstacle_detected
            and not self.left_edge_recovery_latched
        ):
            self.left_edge_recovery_latched = True
            critical_recovery = self.current_block_type in (
                'LEFT_EDGE_CRITICAL',
                'LEFT_EDGE_EXTREME',
            )
            extreme_recovery = self.current_block_type == 'LEFT_EDGE_EXTREME'
            self.left_edge_active_steer = (
                1.0 if critical_recovery else self.left_edge_recovery_steer
            )
            self.left_edge_active_backup_duration = self.left_edge_backup_duration
            if extreme_recovery:
                self.left_edge_active_backup_duration *= (
                    self.left_edge_extreme_backup_multiplier
                )
            self.current_state = 'LEFT_EDGE_STOP'
            self.left_edge_recovery_start_time = time.monotonic()
            self.get_logger().warn(
                '⚠️ Left Edge 한계 진입: 후진 후 좌측 복구 동작을 시작합니다. '
                f'(backup={self.left_edge_active_backup_duration:.1f}s, '
                f'steer={self.left_edge_active_steer:.2f})'
            )

    def try_start_corner_maneuver(self):
        if (
            self.startup_complete
            and self.current_block_type.startswith('CORNER_')
            and self.current_state == 'LINE_TRACE'
            and not self.is_obstacle_detected
            and not self.corner_latched
        ):
            self.corner_direction = (
                1.0 if self.current_block_type.endswith('_LEFT') else -1.0
            )
            self.corner_latched = True
            direction_label = '좌측' if self.corner_direction > 0 else '우측'
            self.get_logger().warn(
                f'⚠️ ㄱ자 코너 감지! 후진 후 {direction_label}으로 조향합니다.'
            )
            self.current_state = 'CORNER_BACKUP'
            self.backup_start_time = time.monotonic()

    def offset_callback(self, msg: Float32):
        # 기동이 끝날 때까지 라인트레이싱 오프셋 갱신을 잠근다.
        if self.maneuver_is_active():
            return

        offset_is_valid = math.isfinite(msg.data) and msg.data != 999.0
        if (
            offset_is_valid
            and (
                self.startup_complete
                or self.current_block_type in (
                    'STRAIGHT',
                    'LEFT_EDGE_LIMIT',
                    'LEFT_EDGE_CRITICAL',
                    'LEFT_EDGE_EXTREME',
                )
            )
        ):
            self.offset_history.append(float(msg.data))
            self.current_offset = sum(self.offset_history) / len(self.offset_history)
            self.last_offset_time = time.monotonic()
        elif not self.startup_complete:
            self.offset_history.clear()
            self.current_offset = 999.0

    def calculate_requested_steering(self, offset):
        if abs(offset) <= self.steering_deadband_px:
            offset = 0.0

        requested_steering = self.steering_sign * offset * self.kp
        if requested_steering > 0.0:
            requested_steering *= self.left_steering_gain

        left_steering_limit = min(
            1.0,
            self.max_steer * self.left_steering_gain,
        )
        return max(
            -self.max_steer,
            min(requested_steering, left_steering_limit),
        )

    def control_loop(self):
        twist = Twist()
        now = time.monotonic()

        # State 1: 장애물 정지
        if self.is_obstacle_detected:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.cmd_pub.publish(twist)
            return

        # State 0: 실행 직후 카메라 프레임과 오프셋 버퍼 준비
        if not self.startup_complete:
            minimum_delay_complete = (
                now - self.startup_start_time >= self.startup_delay
            )
            offset_is_fresh = (
                now - self.last_offset_time <= self.offset_timeout
            )
            startup_data_ready = (
                self.current_block_type in (
                    'STRAIGHT',
                    'LEFT_EDGE_LIMIT',
                    'LEFT_EDGE_CRITICAL',
                    'LEFT_EDGE_EXTREME',
                )
                and len(self.offset_history) == self.offset_history.maxlen
                and offset_is_fresh
            )

            if not (minimum_delay_complete and startup_data_ready):
                self.get_logger().info(
                    'Waiting for 5 consecutive valid offsets...',
                    throttle_duration_sec=1.0,
                )
                block_is_detected = self.current_block_type in (
                    'STRAIGHT',
                    'LEFT_EDGE_LIMIT',
                    'LEFT_EDGE_CRITICAL',
                    'LEFT_EDGE_EXTREME',
                )
                twist.linear.x = (
                    self.startup_crawl_speed
                    if minimum_delay_complete and block_is_detected
                    else 0.0
                )
                twist.angular.z = 0.0
                self.cmd_pub.publish(twist)
                return

            self.startup_complete = True
            self.drive_start_time = now
            self.filtered_steering = self.calculate_requested_steering(
                self.current_offset
            )
            self.get_logger().info(
                '🚀 유효 오프셋 5개 준비 완료, 저속 주행을 시작합니다.'
            )
            self.try_start_left_edge_recovery()

        # State 1: Left Edge 한계 진입 시 정지
        if self.current_state == 'LEFT_EDGE_STOP':
            elapsed = now - self.left_edge_recovery_start_time
            if elapsed < self.left_edge_stop_duration:
                twist.linear.x = 0.0
                twist.angular.z = 0.0
            else:
                self.current_state = 'LEFT_EDGE_BACKUP'
                self.left_edge_recovery_start_time = now
                twist.linear.x = -self.reverse_speed
                twist.angular.z = 0.0

        # State 2: 직선 후진으로 좌측 조향 공간 확보
        elif self.current_state == 'LEFT_EDGE_BACKUP':
            elapsed = now - self.left_edge_recovery_start_time
            if elapsed < self.left_edge_active_backup_duration:
                twist.linear.x = -self.reverse_speed
                twist.angular.z = 0.0
            else:
                self.current_state = 'LEFT_EDGE_TURN'
                self.left_edge_recovery_start_time = now
                twist.linear.x = self.drive_speed
                twist.angular.z = self.left_edge_active_steer

        # State 3: 전진하며 좌측으로 고정 조향
        elif self.current_state == 'LEFT_EDGE_TURN':
            elapsed = now - self.left_edge_recovery_start_time
            if elapsed < self.left_edge_turn_duration:
                twist.linear.x = self.drive_speed
                twist.angular.z = self.left_edge_active_steer
            else:
                self.current_state = 'LINE_TRACE'
                self.filtered_steering = 0.0
                self.left_edge_recovery_latched = False
                twist.linear.x = 0.0
                twist.angular.z = 0.0

        # State 4: ㄱ자 후진
        elif self.current_state == 'CORNER_BACKUP':
            elapsed = time.monotonic() - self.backup_start_time
            if elapsed < self.backup_duration:
                twist.linear.x = -self.reverse_speed
                twist.angular.z = 0.0
            else:
                self.current_state = 'CORNER_TURN'
                self.corner_turn_start_time = now
                twist.linear.x = self.drive_speed
                twist.angular.z = (
                    self.corner_direction
                    * self.corner_steering_sign
                    * self.corner_steer
                )

        # State 5: 후진을 마친 뒤 검출한 ㄱ자 방향으로 전진 조향
        elif self.current_state == 'CORNER_TURN':
            elapsed = now - self.corner_turn_start_time
            if elapsed < self.corner_turn_duration:
                twist.linear.x = self.drive_speed
                twist.angular.z = (
                    self.corner_direction
                    * self.corner_steering_sign
                    * self.corner_steer
                )
            else:
                self.current_state = 'LINE_TRACE'
                self.filtered_steering = 0.0
                twist.linear.x = self.drive_speed
                twist.angular.z = 0.0

        # State 6: 라인트레이싱 (P-Control)
        elif self.current_state == 'LINE_TRACE':
            steering_required = False
            line_tracking_available = False
            offset_is_fresh = (
                math.isfinite(self.current_offset)
                and self.current_offset != 999.0
                and now - self.last_offset_time <= self.offset_timeout
            )

            if (
                self.current_block_type == 'STRAIGHT'
                and offset_is_fresh
            ):
                line_tracking_available = True
                offset = self.current_offset
                steering_required = abs(offset) > self.steering_deadband_px
                requested_steering = self.calculate_requested_steering(offset)

                # 프레임별 검출 흔들림이 서보에 그대로 전달되지 않도록 저역 통과 필터 적용
                alpha = max(0.0, min(self.steering_filter_alpha, 1.0))
                self.filtered_steering += alpha * (
                    requested_steering - self.filtered_steering
                )
                twist.angular.z = self.filtered_steering

            # Case B: 라인을 잠시 놓쳤거나 탐색 중일 때
            else:
                self.get_logger().info(
                    'Tactile block lost or offset invalid; stopping.',
                    throttle_duration_sec=2.0,
                )
                self.filtered_steering = 0.0
                twist.angular.z = 0.0

            if not line_tracking_available:
                twist.linear.x = 0.0
            else:
                # 유효 라인과 오프셋이 있을 때만 전진한다.
                startup_crawl_active = (
                    now - self.drive_start_time < self.startup_crawl_duration
                )
                if startup_crawl_active:
                    twist.linear.x = min(1.0, self.startup_crawl_speed)
                else:
                    speed_boost = (
                        self.steering_speed_boost if steering_required else 0.0
                    )
                    twist.linear.x = min(1.0, self.drive_speed + speed_boost)

        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = MainControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
