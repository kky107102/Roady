import cv2

# ROS 2 필수 모듈
from geometry_msgs.msg import Twist
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class TactileTracerNode(Node):

    def __init__(self):
        super().__init__('tactile_tracer_node')

        # 1. Publisher: motor_node가 구독할 cmd_vel 발행
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)

        # 2. USB 카메라 직접 캡처 (또는 image_raw 토픽 구독 가능)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # 3. 제어 루프 타이머 (30 FPS = 약 0.033초 간격)
        self.timer = self.create_timer(0.033, self.process_frame)

        # 4. 제어 파라미터 (PID 중 P-Gain 및 목표 오프셋)
        self.kp = 0.0015  # 픽셀 오차 -> 조향각 변환 비율 (실차 테스트하며 조절)
        self.base_speed = 0.15  # 기본 전진 속도 (m/s)
        self.target_offset_pixels = 200  # 점자블록 모서리에서 왼쪽으로 떨어질 거리(px)

        self.get_logger().info('✅ 점자블록 라인트레이싱 노드가 시작되었습니다.')

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn('카메라 프레임을 읽을 수 없습니다.')
            return

        # --- 이미지 처리 (점자블록 좌측 모서리 검출) ---
        left_edge_x, debug_img = self.detect_tactile_left_edge(frame)

        twist = Twist()

        if left_edge_x is not None:
            # 1. 목표 위치(Target X) 및 화면 중앙과의 오차(Error) 계산
            height, width, _ = frame.shape
            car_center_x = width // 2

            # 점자블록 좌측 모서리로부터 offset만큼 왼쪽으로 떨어진 지점이 목표점
            target_x = left_edge_x - self.target_offset_pixels
            error = target_x - car_center_x  # 음수: 좌회전 필요, 양수: 우회전 필요

            # 2. P 제어로 조향각(Angular Z) 산출
            # ROS 2 좌표계: +z = 반시계방향(좌회전), -z = 시계방향(우회전)
            angular_z = -1.0 * (self.kp * error)

            # 조향각 범위를 -1.0 ~ 1.0 으로 제한 (Saturation)
            angular_z = max(-1.0, min(1.0, angular_z))

            twist.linear.x = self.base_speed
            twist.angular.z = float(angular_z)

            self.get_logger().info(
                f'Edge X: {left_edge_x} | Error: {error} | Angular Z: {angular_z:.2f}'
            )
        else:
            # 점자블록을 놓쳤을 경우 감속 정지
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.get_logger().warn('⚠️ 점자블록 미인식 - 정지 중')

        # 3. 제어 명령 발행
        self.cmd_pub.publish(twist)

        # 디버깅 화면 출력 (화면이 없는 환경이라면 주석 처리 가능)
#        cv2.imshow('Tactile Line Tracer Debug', debug_img)
#        cv2.waitKey(1)

    def detect_tactile_left_edge(self, frame):
        """점자블록 좌측 모서리 검출 함수"""
        height, width, _ = frame.shape

        # ROI: 카메라 하단 50%
        roi_y_start = int(height * 0.5)
        roi = frame[roi_y_start:height, 0:width]
        roi_h, roi_w, _ = roi.shape

        # HSV 마스킹 (노란색)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # 모폴로지 (구멍 메우기)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 윤곽선 검출
        contours, _ = cv2.findContours(
            mask_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        left_edge_x = None
        debug_frame = roi.copy()
        scan_y = int(roi_h * 0.6)

        if contours:
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > 1000:
                points_at_scany = [
                    p[0][0] for p in c if abs(p[0][1] - scan_y) <= 2
                ]
                if points_at_scany:
                    left_edge_x = min(points_at_scany)

                cv2.drawContours(debug_frame, [c], -1, (0, 255, 0), 2)

        # 시각화 가이드라인
        cv2.line(
            debug_frame,
            (0, scan_y),
            (roi_w, scan_y),
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )
        if left_edge_x is not None:
            cv2.circle(debug_frame, (left_edge_x, scan_y), 6, (0, 0, 255), -1)

        return left_edge_x, debug_frame

    def destroy_node(self):
        self.cap.release()
 #       cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TactileTracerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
