#!/usr/bin/env python3
from collections import Counter, deque
import math
import time

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, Float32, String, UInt32

TRACKING_STATES = (
    'UNKNOWN', 'STRAIGHT', 'CORNER_LEFT', 'CORNER_RIGHT', 'STATION'
)
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
            '/tactile/station_rightmost_x',
            self.station_rightmost_callback,
            10,
        )
        self.create_subscription(
            UInt32,
            '/tactile/full_frame_navy_count',
            self.full_frame_navy_count_callback,
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
        self.create_subscription(
            Bool,
            '/damage/upload_complete',
            self.upload_complete_callback,
            finished_qos,
        )

        self.declare_parameter('drive_speed', 0.4)
        self.declare_parameter('reverse_speed', 0.4)
        self.declare_parameter('kp', 0.004)
        self.declare_parameter('max_steer', 0.75)
        self.declare_parameter('left_steering_gain', 1.30)
        self.declare_parameter('steering_deadband_px', 30.0)
        self.declare_parameter('steering_filter_alpha', 0.35)
        self.declare_parameter('offset_timeout', 1.0)
        self.declare_parameter('steering_sign', -1.0)
        self.declare_parameter('target_edge_x_px', 750.0)
        self.declare_parameter('corner_target_edge_x_px', 750.0)
        self.declare_parameter('corner_align_tolerance_px', 30.0)
        self.declare_parameter('corner_align_kp', 0.004)
        self.declare_parameter('corner_confirm_frames', 10)
        self.declare_parameter('corner_backup_duration', 1.5)
        self.declare_parameter('corner_forward_duration', 1.0)
        self.declare_parameter('corner_steer', 0.75)
        self.declare_parameter('startup_duration', 4.0)
        self.declare_parameter('unknown_vote_frames', 10)
        self.declare_parameter('unknown_max_consecutive_votes', 5)
        self.declare_parameter('station_target_samples', 5)
        self.declare_parameter('station_steering_kp', 0.004)
        self.declare_parameter('station_end_navy_pixels', 1000)
        self.declare_parameter('station_end_confirm_frames', 10)
        self.declare_parameter('wait_for_upload', False)
        self.declare_parameter('upload_wait_timeout_sec', 60.0)

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
        self.corner_target_edge_x_px = float(
            self.get_parameter('corner_target_edge_x_px').value
        )
        self.corner_align_tolerance_px = abs(
            float(self.get_parameter('corner_align_tolerance_px').value)
        )
        self.corner_align_kp = abs(
            float(self.get_parameter('corner_align_kp').value)
        )
        self.corner_confirm_frames = max(
            1, int(self.get_parameter('corner_confirm_frames').value)
        )
        self.corner_backup_duration = max(
            0.0, float(self.get_parameter('corner_backup_duration').value)
        )
        self.corner_forward_duration = max(
            0.0, float(self.get_parameter('corner_forward_duration').value)
        )
        self.corner_steer = min(
            1.0, abs(float(self.get_parameter('corner_steer').value))
        )
        self.startup_duration = max(
            0.0, float(self.get_parameter('startup_duration').value)
        )
        self.unknown_vote_frames = max(
            1, int(self.get_parameter('unknown_vote_frames').value)
        )
        self.unknown_max_consecutive_votes = max(
            1,
            int(self.get_parameter('unknown_max_consecutive_votes').value),
        )
        self.station_target_samples = max(
            1, int(self.get_parameter('station_target_samples').value)
        )
        self.station_steering_kp = abs(
            float(self.get_parameter('station_steering_kp').value)
        )
        self.station_end_navy_pixels = max(
            0, int(self.get_parameter('station_end_navy_pixels').value)
        )
        self.station_end_confirm_frames = max(
            1, int(self.get_parameter('station_end_confirm_frames').value)
        )

        self.tracking_state = STARTUP_STATE
        self.maneuver_phase = 'NONE'
        self.phase_started_at = time.monotonic()
        self.startup_started_at = time.monotonic()
        self.startup_paused_at = None
        self.startup_state_counts = Counter()
        self.unknown_frame_states = deque(maxlen=self.unknown_vote_frames)
        self.unknown_consecutive_votes = 0
        self.station_target_history = deque(maxlen=self.station_target_samples)
        self.station_target_x = None
        self.station_rightmost_x = None
        self.station_end_count = 0
        self.corner_candidate_direction = None
        self.corner_candidate_count = 0
        self.corner_recovery_active = False
        self.current_offset = 999.0
        self.offset_history = deque(maxlen=5)
        self.last_offset_time = 0.0
        self.filtered_steering = 0.0
        self.corner_alignment_steer = 0.0
        self.is_obstacle_detected = False
        self.shutdown_requested = False
        self.shutdown_timer = None

        self.timer = self.create_timer(0.05, self.control_loop)
        self._publish_tracking_state()
        self.get_logger().info(
            f'주행 FSM 시작: STARTUP 전체 화면 {self.startup_duration:.1f}초 탐색'
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
        if state == 'UNKNOWN':
            self.corner_recovery_active = False
            self.maneuver_phase = 'NONE'
            if previous_state != 'UNKNOWN':
                self.unknown_frame_states.clear()
                self.unknown_consecutive_votes = 0
        elif state in CORNER_STATES:
            # 코너 확정 이후에는 일반 상태 판정을 잠그고 복구 입력만 처리한다.
            self.corner_recovery_active = True
            self.maneuver_phase = 'CORNER_BACKUP'
            self.phase_started_at = time.monotonic()
            self.corner_alignment_steer = self._corner_steering()
        elif state == 'STATION':
            self.corner_recovery_active = False
            self.maneuver_phase = 'STATION_CALIBRATE'
            self.station_target_history.clear()
            self.station_target_x = None
            self.station_rightmost_x = None
            self.station_end_count = 0
            self.cmd_pub.publish(Twist())
            self.get_logger().info(
                f'STATION 정지: 최우측 X 좌표를 '
                f'{self.station_target_samples}회 수집합니다.'
            )
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
        # leftmost_callback만 코너 정렬 완료 상태로 전환할 수 있다.
        if self.corner_recovery_active:
            return

        detected = msg.data if msg.data in TRACKING_STATES else 'UNKNOWN'

        if detected == 'STATION' and self.tracking_state != 'STATION':
            self.get_logger().info(
                '흰색 간판의 남색 픽셀 3500개 이상 감지: STATION 진입'
            )
            self._set_tracking_state('STATION')
            return

        if self.tracking_state == STARTUP_STATE:
            if detected != 'UNKNOWN':
                self.startup_state_counts[detected] += 1
            return

        if self.maneuver_phase == 'CORNER_CONFIRM':
            if detected in CORNER_STATES:
                if detected == self.corner_candidate_direction:
                    self.corner_candidate_count += 1
                else:
                    self.corner_candidate_direction = detected
                    self.corner_candidate_count = 1
            else:
                self.corner_candidate_direction = None
                self.corner_candidate_count = 0

            if self.corner_candidate_count >= self.corner_confirm_frames:
                confirmed_state = self.corner_candidate_direction
                self.get_logger().info(
                    f'코너 {self.corner_confirm_frames}프레임 연속 확인: '
                    f'{confirmed_state}'
                )
                self._set_tracking_state(confirmed_state)
            return

        if self.tracking_state == 'UNKNOWN':
            self._collect_unknown_frame(detected)
            return

        if self.tracking_state == 'STRAIGHT':
            if detected in CORNER_STATES:
                self.maneuver_phase = 'CORNER_CONFIRM'
                self.corner_candidate_direction = detected
                self.corner_candidate_count = 1
                self.filtered_steering = 0.0
                self.get_logger().warn(
                    '최초 코너 감지: 즉시 정지하고 같은 방향 코너를 '
                    f'{self.corner_confirm_frames}프레임 연속 확인합니다.'
                )
            else:
                self.corner_candidate_direction = None
                self.corner_candidate_count = 0

    def _finish_startup_if_due(self, now):
        """Choose the most frequent detection after mandatory startup drive."""
        if (
            self.tracking_state != STARTUP_STATE
            or now - self.startup_started_at < self.startup_duration
        ):
            return

        if self.startup_state_counts:
            next_state = self.startup_state_counts.most_common(1)[0][0]
        else:
            next_state = 'UNKNOWN'
        counts = dict(self.startup_state_counts)
        self.get_logger().info(
            f'STARTUP {self.startup_duration:.1f}초 판정 결과: '
            f'{counts}, 최종 상태: {next_state}'
        )
        self._set_tracking_state(next_state)

    def _collect_unknown_frame(self, detected):
        if self.shutdown_requested:
            return

        self.unknown_frame_states.append(detected)
        if len(self.unknown_frame_states) >= self.unknown_vote_frames:
            self._evaluate_unknown_vote()

    def _evaluate_unknown_vote(self):
        if self.tracking_state != 'UNKNOWN' or self.shutdown_requested:
            return

        states = list(self.unknown_frame_states)
        if len(states) < self.unknown_vote_frames:
            return

        self.unknown_frame_states.clear()
        counts = Counter(states)
        highest_count = max(counts.values())
        winners = [
            state for state, count in counts.items() if count == highest_count
        ]
        next_state = winners[0] if len(winners) == 1 else 'UNKNOWN'
        self.get_logger().info(
            f'UNKNOWN 판정 결과: frames={len(states)}, counts={dict(counts)}, '
            f'최종 상태={next_state}'
        )

        if next_state != 'UNKNOWN':
            self._set_tracking_state(next_state)
            return

        self.unknown_consecutive_votes += 1
        self.get_logger().warn(
            'UNKNOWN 투표 연속 '
            f'{self.unknown_consecutive_votes}/'
            f'{self.unknown_max_consecutive_votes}회'
        )
        if (
            self.unknown_consecutive_votes
            < self.unknown_max_consecutive_votes
        ):
            return

        self._finish_driving(
            f'투표 결과가 {self.unknown_max_consecutive_votes}회 연속 '
            'UNKNOWN이어서 주행을 종료합니다.'
        )

    def _finish_driving(self, reason):
        if self.shutdown_requested:
            return
        self.unknown_frame_states.clear()
        self.filtered_steering = 0.0
        self.cmd_pub.publish(Twist())
        finished = Bool()
        finished.data = True
        self.finished_pub.publish(finished)
        self.shutdown_requested = True
        if bool(self.get_parameter('wait_for_upload').value):
            timeout = max(
                1.0,
                float(self.get_parameter('upload_wait_timeout_sec').value),
            )
            self.shutdown_timer = self.create_timer(
                timeout, self._shutdown_after_finish
            )
            self.get_logger().info(
                f'파손 이미지 업로드 완료를 최대 {timeout:.0f}초 기다립니다.'
            )
        else:
            self.shutdown_timer = self.create_timer(
                0.2, self._shutdown_after_finish
            )
        self.get_logger().warn(reason)

    def upload_complete_callback(self, msg):
        if not msg.data or not self.shutdown_requested:
            return
        if self.shutdown_timer is not None:
            self.shutdown_timer.cancel()
        self.get_logger().info('파손 이미지 업로드 절차가 완료되었습니다.')
        self.shutdown_timer = self.create_timer(
            0.2, self._shutdown_after_finish
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
        else:
            self.get_logger().warn('오프셋을 찾지 못해 UNKNOWN 상태로 전환합니다.')
            self._set_tracking_state('UNKNOWN')

    def leftmost_callback(self, msg):
        if self.tracking_state not in CORNER_STATES:
            return
        if not math.isfinite(msg.data) or msg.data < 0.0:
            return
        if (
            abs(float(msg.data) - self.corner_target_edge_x_px)
            <= self.corner_align_tolerance_px
        ):
            if self.maneuver_phase in ('CORNER_BACKUP', 'CORNER_FORWARD'):
                self.get_logger().info(
                    '코너 좌측 픽셀 정렬 완료: UNKNOWN 상태로 전환합니다.'
                )
                self._set_tracking_state('UNKNOWN')
        elif self.maneuver_phase in ('CORNER_BACKUP', 'CORNER_FORWARD'):
            self.corner_alignment_steer = (
                self.calculate_corner_alignment_steering(float(msg.data))
            )

    def station_rightmost_callback(self, msg):
        if self.tracking_state != 'STATION':
            return
        if not math.isfinite(msg.data) or msg.data < 0.0:
            return

        self.station_rightmost_x = float(msg.data)
        if self.maneuver_phase != 'STATION_CALIBRATE':
            return

        self.station_target_history.append(self.station_rightmost_x)
        self.get_logger().info(
            f'STATION 타겟 좌표 수집 {len(self.station_target_history)}/'
            f'{self.station_target_samples}: x={self.station_rightmost_x:.1f}'
        )
        if len(self.station_target_history) >= self.station_target_samples:
            self.station_target_x = (
                sum(self.station_target_history)
                / len(self.station_target_history)
            )
            self.maneuver_phase = 'STATION_APPROACH'
            self.get_logger().info(
                f'STATION 타겟 X 확정: {self.station_target_x:.1f}px, '
                '조향 전진을 시작합니다.'
            )

    def full_frame_navy_count_callback(self, msg):
        if (
            self.tracking_state != 'STATION'
            or self.maneuver_phase != 'STATION_APPROACH'
        ):
            return

        if int(msg.data) <= self.station_end_navy_pixels:
            self.station_end_count += 1
            self.get_logger().info(
                f'STATION 종료 후보 {self.station_end_count}/'
                f'{self.station_end_confirm_frames}: navy={int(msg.data)}px'
            )
        if self.station_end_count >= self.station_end_confirm_frames:
            self._finish_driving(
                f'전체 화면 남색 픽셀 {self.station_end_navy_pixels}개 이하가 '
                f'{self.station_end_confirm_frames}프레임 확인되어 '
                '스테이션 복귀를 완료했습니다.'
            )

    def calculate_requested_steering(self, offset):
        if abs(offset) <= self.steering_deadband_px:
            offset = 0.0
        requested = self.steering_sign * offset * self.kp
        if requested > 0.0:
            requested *= self.left_steering_gain
        left_limit = min(1.0, self.max_steer * self.left_steering_gain)
        return max(-self.max_steer, min(requested, left_limit))

    def calculate_corner_alignment_steering(self, leftmost_x):
        error = leftmost_x - self.corner_target_edge_x_px
        requested = self.steering_sign * error * self.corner_align_kp
        return max(-self.max_steer, min(requested, self.max_steer))

    def calculate_station_steering(self):
        if self.station_target_x is None or self.station_rightmost_x is None:
            return 0.0
        error = self.station_rightmost_x - self.station_target_x
        requested = self.steering_sign * error * self.station_steering_kp
        return max(-self.max_steer, min(requested, self.max_steer))

    def control_loop(self):
        twist = Twist()
        now = time.monotonic()

        if self.shutdown_requested:
            self.cmd_pub.publish(twist)
            return

        if self.is_obstacle_detected:
            if (
                self.tracking_state == STARTUP_STATE
                and self.startup_paused_at is None
            ):
                self.startup_paused_at = now
            self.cmd_pub.publish(twist)
            return

        if (
            self.tracking_state == STARTUP_STATE
            and self.startup_paused_at is not None
        ):
            self.startup_started_at += now - self.startup_paused_at
            self.startup_paused_at = None
        self._finish_startup_if_due(now)

        if self.maneuver_phase == 'CORNER_CONFIRM':
            pass
        elif self.maneuver_phase == 'CORNER_BACKUP':
            if now - self.phase_started_at < self.corner_backup_duration:
                twist.linear.x = -self.reverse_speed
            else:
                self.maneuver_phase = 'CORNER_FORWARD'
                self.phase_started_at = now
                twist.linear.x = self.drive_speed
                twist.angular.z = self.corner_alignment_steer
        elif self.maneuver_phase == 'CORNER_FORWARD':
            if now - self.phase_started_at < self.corner_forward_duration:
                twist.linear.x = self.drive_speed
                twist.angular.z = self.corner_alignment_steer
            else:
                self.maneuver_phase = 'CORNER_BACKUP'
                self.phase_started_at = now
                twist.linear.x = -self.reverse_speed
        elif self.maneuver_phase == 'STATION_CALIBRATE':
            pass
        elif self.maneuver_phase == 'STATION_APPROACH':
            twist.linear.x = self.drive_speed
            twist.angular.z = self.calculate_station_steering()
        elif self.tracking_state == STARTUP_STATE:
            # 최초 4초 동안 전체 ROI 판정을 수집하며 직진한다.
            twist.linear.x = self.drive_speed
        elif self.tracking_state == 'UNKNOWN':
            # UNKNOWN 투표 중에도 현재 설정된 일반 주행 속도로 주행한다.
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
