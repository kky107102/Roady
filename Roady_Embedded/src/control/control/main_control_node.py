#!/usr/bin/env python3
from collections import Counter, deque
import math
import time

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, Float32, String

TRACKING_STATES = ('UNKNOWN', 'STRAIGHT', 'CORNER_LEFT', 'CORNER_RIGHT')
CORNER_STATES = ('CORNER_LEFT', 'CORNER_RIGHT')
STARTUP_STATE = 'STARTUP'


class MainControlNode(Node):
    """Turns frame-level tactile detections into a small driving FSM."""

    def __init__(self):
        super().__init__('main_control_node')

        self.create_subscription(
            String, '/tactile/block_type', self.detection_callback, 10
        )
        self.create_subscription(
            Float32, '/tactile/edge_offset', self.offset_callback, 10
        )
        self.create_subscription(
            Float32, '/tactile/leftmost_x', self.leftmost_callback, 10
        )
        self.create_subscription(
            Float32,
            '/tactile/full_frame_yellow_ratio',
            self.roi_ratio_callback,
            10,
        )
        self.create_subscription(Bool, '/obstacle_warning', self.lidar_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.state_pub = self.create_publisher(String, '/tactile/tracking_state', 10)
        finished_qos = QoSProfile(depth=1)
        finished_qos.reliability = ReliabilityPolicy.RELIABLE
        finished_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.finished_pub = self.create_publisher(
            Bool, '/driving/finished', finished_qos
        )

        self.declare_parameter('drive_speed', 0.4)
        self.declare_parameter('reverse_speed', 0.4)
        self.declare_parameter('kp', 0.004)
        self.declare_parameter('max_steer', 0.75)
        self.declare_parameter('left_steering_gain', 1.30)
        self.declare_parameter('steering_deadband_px', 15.0)
        self.declare_parameter('steering_filter_alpha', 0.35)
        self.declare_parameter('offset_timeout', 1.0)
        self.declare_parameter('steering_sign', -1.0)
        self.declare_parameter('target_edge_x_px', 750.0)
        self.declare_parameter('corner_align_tolerance_px', 8.0)
        self.declare_parameter('corner_candidate_frames', 5)
        self.declare_parameter('corner_vote_window', 15)
        self.declare_parameter('corner_backup_duration', 1.5)
        self.declare_parameter('corner_forward_duration', 1.0)
        self.declare_parameter('offset_backup_duration', 1.5)
        self.declare_parameter('offset_forward_duration', 1.0)
        self.declare_parameter('corner_steer', 0.75)
        self.declare_parameter('unknown_duration', 7.0)
        self.declare_parameter('unknown_vote_required', 15)
        self.declare_parameter('reacquire_yellow_ratio', 0.20)
        self.declare_parameter('reacquire_confirm_frames', 5)

        self.drive_speed = min(1.0, abs(float(self.get_parameter('drive_speed').value)))
        self.reverse_speed = min(1.0, abs(float(self.get_parameter('reverse_speed').value)))
        self.kp = float(self.get_parameter('kp').value)
        self.max_steer = min(1.0, abs(float(self.get_parameter('max_steer').value)))
        self.left_steering_gain = max(
            0.0, float(self.get_parameter('left_steering_gain').value)
        )
        self.steering_deadband_px = abs(
            float(self.get_parameter('steering_deadband_px').value)
        )
        self.steering_filter_alpha = float(
            self.get_parameter('steering_filter_alpha').value
        )
        self.offset_timeout = max(0.0, float(self.get_parameter('offset_timeout').value))
        self.steering_sign = float(self.get_parameter('steering_sign').value)
        self.target_edge_x_px = float(self.get_parameter('target_edge_x_px').value)
        self.corner_align_tolerance_px = abs(
            float(self.get_parameter('corner_align_tolerance_px').value)
        )
        self.corner_candidate_frames = max(
            1, int(self.get_parameter('corner_candidate_frames').value)
        )
        self.corner_vote_window = max(
            1, int(self.get_parameter('corner_vote_window').value)
        )
        self.corner_backup_duration = max(
            0.0, float(self.get_parameter('corner_backup_duration').value)
        )
        self.corner_forward_duration = max(
            0.0, float(self.get_parameter('corner_forward_duration').value)
        )
        self.offset_backup_duration = max(
            0.0, float(self.get_parameter('offset_backup_duration').value)
        )
        self.offset_forward_duration = max(
            0.0, float(self.get_parameter('offset_forward_duration').value)
        )
        self.corner_steer = min(
            1.0, abs(float(self.get_parameter('corner_steer').value))
        )
        self.unknown_duration = max(
            0.0, float(self.get_parameter('unknown_duration').value)
        )
        self.unknown_vote_required = max(
            1, int(self.get_parameter('unknown_vote_required').value)
        )
        self.reacquire_yellow_ratio = max(
            0.0, min(1.0, float(self.get_parameter('reacquire_yellow_ratio').value))
        )
        self.reacquire_confirm_frames = max(
            1, int(self.get_parameter('reacquire_confirm_frames').value)
        )

        self.tracking_state = STARTUP_STATE
        self.maneuver_phase = 'NONE'
        self.phase_started_at = time.monotonic()
        self.startup_candidate_state = None
        self.startup_candidate_count = 0
        self.unknown_started_at = time.monotonic()
        self.unknown_search_complete = False
        self.unknown_candidate_state = None
        self.unknown_candidate_count = 0
        self.corner_candidate_direction = None
        self.corner_candidate_count = 0
        self.corner_confirmation_history = deque(maxlen=self.corner_vote_window)
        self.corner_recovery_active = False
        self.reacquire_count = 0
        self.current_offset = 999.0
        self.offset_history = deque(maxlen=5)
        self.last_offset_time = 0.0
        self.filtered_steering = 0.0
        self.offset_recovery_steer = 0.0
        self.is_obstacle_detected = False
        self.shutdown_requested = False
        self.shutdown_timer = None

        self.timer = self.create_timer(0.05, self.control_loop)
        self._publish_tracking_state()
        self.get_logger().info(
            '주행 FSM 시작: STARTUP 전체 화면 무제한 탐색'
        )

    def _publish_tracking_state(self):
        msg = String()
        msg.data = self.tracking_state
        self.state_pub.publish(msg)

    def _set_tracking_state(self, state):
        if state not in TRACKING_STATES:
            state = 'UNKNOWN'
        previous_state = self.tracking_state
        self.tracking_state = state
        self.filtered_steering = 0.0
        self.offset_history.clear()
        self.current_offset = 999.0
        self.corner_candidate_direction = None
        self.corner_candidate_count = 0
        self.corner_confirmation_history.clear()
        if state == 'UNKNOWN':
            self.corner_recovery_active = False
            self.maneuver_phase = 'NONE'
            if previous_state != 'UNKNOWN':
                self.unknown_candidate_state = None
                self.unknown_candidate_count = 0
                self.unknown_started_at = time.monotonic()
                self.unknown_search_complete = False
        elif state in CORNER_STATES:
            # 코너 확정 이후에는 일반 상태 판정을 잠그고 복구 입력만 처리한다.
            self.corner_recovery_active = True
            self.maneuver_phase = 'CORNER_BACKUP'
            self.phase_started_at = time.monotonic()
        else:
            self.corner_recovery_active = False
            self.maneuver_phase = 'NONE'
            # STRAIGHT 전환 직후 첫 오프셋이 도착할 수 있도록 timeout만큼 기다린다.
            self.last_offset_time = time.monotonic()
        self._publish_tracking_state()
        self.get_logger().info(f'주행 상태 전환: {state}')

    def lidar_callback(self, msg):
        self.is_obstacle_detected = bool(msg.data)

    def detection_callback(self, msg):
        # 확정된 코너 복구 중에는 프레임별 상태 판정 결과를 완전히 무시한다.
        # leftmost_callback과 roi_ratio_callback만 복구 단계를 전환할 수 있다.
        if self.corner_recovery_active:
            return

        detected = msg.data if msg.data in TRACKING_STATES else 'UNKNOWN'

        if self.tracking_state == STARTUP_STATE:
            self._update_startup_candidate(detected)
            return

        if self.maneuver_phase == 'CORNER_CONFIRM':
            # 정지 상태에서 15프레임을 모두 모은 뒤 최빈 상태를 한 번만 확정한다.
            # 수집 중에는 tracking_state를 갱신하지 않는다.
            self.corner_confirmation_history.append(detected)
            if len(self.corner_confirmation_history) >= self.corner_vote_window:
                confirmed_state = Counter(
                    self.corner_confirmation_history
                ).most_common(1)[0][0]
                self.get_logger().info(
                    f'코너 확인 {self.corner_vote_window}프레임 최빈 상태: '
                    f'{confirmed_state}'
                )
                self._set_tracking_state(confirmed_state)
            return

        if self.tracking_state == 'UNKNOWN':
            self._update_unknown_candidate(detected)
            return

        if self.tracking_state == 'STRAIGHT':
            if detected in CORNER_STATES:
                if detected == self.corner_candidate_direction:
                    self.corner_candidate_count += 1
                else:
                    self.corner_candidate_direction = detected
                    self.corner_candidate_count = 1
                if self.corner_candidate_count >= self.corner_candidate_frames:
                    self.maneuver_phase = 'CORNER_CONFIRM'
                    self.corner_confirmation_history.clear()
                    self.filtered_steering = 0.0
                    self.get_logger().warn(
                        '코너 후보 5프레임 연속 감지: 정지 후 최근 15프레임의 '
                        '최빈 상태를 확인합니다.'
                    )
            else:
                self.corner_candidate_direction = None
                self.corner_candidate_count = 0

    def _update_startup_candidate(self, detected):
        """Confirm the initial state without applying an exploration timeout."""
        if detected == 'UNKNOWN':
            self.startup_candidate_state = None
            self.startup_candidate_count = 0
            return

        if detected == self.startup_candidate_state:
            self.startup_candidate_count += 1
        else:
            self.startup_candidate_state = detected
            self.startup_candidate_count = 1

        if self.startup_candidate_count >= self.unknown_vote_required:
            self._set_tracking_state(self.startup_candidate_state)

    def _update_unknown_candidate(self, detected):
        if self.unknown_search_complete:
            return

        # 마감 시각 이후 들어온 프레임으로 상태가 확정되지 않게 먼저 검사한다.
        self._finish_unknown_search_if_due()
        if self.unknown_search_complete:
            return

        if detected == 'UNKNOWN':
            self.unknown_candidate_state = None
            self.unknown_candidate_count = 0
            return

        if detected == self.unknown_candidate_state:
            self.unknown_candidate_count += 1
        else:
            # 새로운 상태가 나온 현재 프레임부터 다시 1회로 센다.
            self.unknown_candidate_state = detected
            self.unknown_candidate_count = 1

        if self.unknown_candidate_count >= self.unknown_vote_required:
            self._set_tracking_state(self.unknown_candidate_state)

    def _finish_unknown_search_if_due(self):
        if (
            self.tracking_state != 'UNKNOWN'
            or self.unknown_search_complete
            or time.monotonic() - self.unknown_started_at < self.unknown_duration
        ):
            return

        self.unknown_search_complete = True
        self.unknown_candidate_state = None
        self.unknown_candidate_count = 0
        self.filtered_steering = 0.0
        self.cmd_pub.publish(Twist())
        finished = Bool()
        finished.data = True
        self.finished_pub.publish(finished)
        self.shutdown_requested = True
        self.shutdown_timer = self.create_timer(
            0.2, self._shutdown_after_finish
        )
        self.get_logger().warn(
            '7초 동안 상태를 확정하지 못해 주행을 종료합니다.'
        )

    def _shutdown_after_finish(self):
        """Allow the finish and stop messages to leave before exiting."""
        if rclpy.ok():
            rclpy.shutdown()

    def offset_callback(self, msg):
        if self.tracking_state != 'STRAIGHT' or self.maneuver_phase != 'NONE':
            return
        if math.isfinite(msg.data) and msg.data != 999.0:
            self.offset_history.append(float(msg.data))
            self.current_offset = sum(self.offset_history) / len(self.offset_history)
            self.last_offset_time = time.monotonic()
            if abs(self.current_offset) > self.steering_deadband_px:
                requested = self.steering_sign * self.current_offset
                self.offset_recovery_steer = (
                    self.max_steer if requested > 0.0 else -self.max_steer
                )
                self.maneuver_phase = 'OFFSET_BACKUP'
                self.phase_started_at = self.last_offset_time
                self.filtered_steering = 0.0
                self.get_logger().info(
                    '조향 데드밴드 초과: 후진 후 최대 조향 보정을 시작합니다.'
                )
        else:
            self.get_logger().warn('오프셋을 찾지 못해 UNKNOWN 상태로 전환합니다.')
            self._set_tracking_state('UNKNOWN')

    def leftmost_callback(self, msg):
        if self.tracking_state not in CORNER_STATES:
            return
        if not math.isfinite(msg.data) or msg.data < 0.0:
            return
        if abs(float(msg.data) - self.target_edge_x_px) <= self.corner_align_tolerance_px:
            if self.maneuver_phase in ('CORNER_BACKUP', 'CORNER_FORWARD'):
                self.maneuver_phase = 'REACQUIRE'
                self.reacquire_count = 0
                self.get_logger().info('코너 좌측 픽셀 정렬 완료: 전체 화면 재진입을 확인합니다.')

    def roi_ratio_callback(self, msg):
        if self.maneuver_phase != 'REACQUIRE':
            return
        if msg.data >= self.reacquire_yellow_ratio:
            self.reacquire_count += 1
        else:
            self.reacquire_count = 0
        if self.reacquire_count >= self.reacquire_confirm_frames:
            self._set_tracking_state('UNKNOWN')

    def calculate_requested_steering(self, offset):
        if abs(offset) <= self.steering_deadband_px:
            offset = 0.0
        requested = self.steering_sign * offset * self.kp
        if requested > 0.0:
            requested *= self.left_steering_gain
        left_limit = min(1.0, self.max_steer * self.left_steering_gain)
        return max(-self.max_steer, min(requested, left_limit))

    def control_loop(self):
        twist = Twist()
        now = time.monotonic()

        if self.shutdown_requested:
            self.cmd_pub.publish(twist)
            return

        if self.is_obstacle_detected:
            self.cmd_pub.publish(twist)
            return

        # 카메라 프레임이 끊겨도 7초 제한은 제어 타이머에서 독립적으로 적용한다.
        self._finish_unknown_search_if_due()

        if self.maneuver_phase == 'CORNER_CONFIRM':
            pass
        elif self.maneuver_phase == 'OFFSET_BACKUP':
            if now - self.phase_started_at < self.offset_backup_duration:
                twist.linear.x = -self.reverse_speed
            else:
                self.maneuver_phase = 'OFFSET_FORWARD'
                self.phase_started_at = now
                twist.linear.x = self.drive_speed
                twist.angular.z = self.offset_recovery_steer
        elif self.maneuver_phase == 'OFFSET_FORWARD':
            if now - self.phase_started_at < self.offset_forward_duration:
                twist.linear.x = self.drive_speed
                twist.angular.z = self.offset_recovery_steer
            else:
                self.maneuver_phase = 'NONE'
                self.current_offset = 999.0
                self.offset_history.clear()
                self.last_offset_time = now
                self.filtered_steering = 0.0
        elif self.maneuver_phase == 'CORNER_BACKUP':
            if now - self.phase_started_at < self.corner_backup_duration:
                twist.linear.x = -self.reverse_speed
            else:
                self.maneuver_phase = 'CORNER_FORWARD'
                self.phase_started_at = now
                twist.linear.x = self.drive_speed
                twist.angular.z = self._corner_steering()
        elif self.maneuver_phase == 'CORNER_FORWARD':
            if now - self.phase_started_at < self.corner_forward_duration:
                twist.linear.x = self.drive_speed
                twist.angular.z = self._corner_steering()
            else:
                self.maneuver_phase = 'CORNER_BACKUP'
                self.phase_started_at = now
                twist.linear.x = -self.reverse_speed
        elif self.maneuver_phase == 'REACQUIRE':
            twist.linear.x = self.drive_speed
        elif self.tracking_state == STARTUP_STATE:
            # 최초 상태가 확정될 때까지 시간 제한 없이 전체 ROI로 직진한다.
            twist.linear.x = self.drive_speed
        elif self.tracking_state == 'UNKNOWN':
            # UNKNOWN 탐색 중에도 별도의 저속값을 쓰지 않고 현재 설정 속도로 주행한다.
            if not self.unknown_search_complete:
                twist.linear.x = self.drive_speed
        elif self.tracking_state == 'STRAIGHT':
            offset_is_valid = (
                math.isfinite(self.current_offset)
                and self.current_offset != 999.0
            )
            offset_timed_out = now - self.last_offset_time > self.offset_timeout
            if offset_is_valid and not offset_timed_out:
                requested = self.calculate_requested_steering(self.current_offset)
                alpha = max(0.0, min(self.steering_filter_alpha, 1.0))
                self.filtered_steering += alpha * (requested - self.filtered_steering)
                twist.linear.x = self.drive_speed
                twist.angular.z = self.filtered_steering
            elif offset_timed_out:
                self.get_logger().warn(
                    '오프셋 갱신 시간이 초과되어 UNKNOWN 상태로 전환합니다.',
                    throttle_duration_sec=1.0,
                )
                self._set_tracking_state('UNKNOWN')

        self.cmd_pub.publish(twist)

    def _corner_steering(self):
        return self.corner_steer if self.tracking_state == 'CORNER_LEFT' else -self.corner_steer


def main(args=None):
    rclpy.init(args=args)
    node = MainControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.cmd_pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
