#!/usr/bin/env python3

import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String, Float32


class TactileTracerNode(Node):

    def __init__(self):
        super().__init__('tactile_tracer_node')

        # 토픽 Publisher
        self.block_pub = self.create_publisher(String, '/tactile/block_type', 10)
        self.edge_offset_pub = self.create_publisher(Float32, '/tactile/edge_offset', 10)

        self.declare_parameter('image_topic', '/camera/tactile/image_raw')
        self.declare_parameter('target_edge_x_px', 750)
        self.declare_parameter('roi_top_ratio', 0.55)
        self.declare_parameter('startup_full_roi_duration', 5.0)
        self.declare_parameter('left_edge_limit_ratio', 0.50)
        self.declare_parameter('left_edge_critical_ratio', 0.30)
        image_topic = str(self.get_parameter('image_topic').value)
        self.target_edge_x_px = int(
            self.get_parameter('target_edge_x_px').value
        )
        self.roi_top_ratio = float(self.get_parameter('roi_top_ratio').value)
        self.roi_top_ratio = max(0.05, min(self.roi_top_ratio, 0.75))
        self.startup_full_roi_duration = max(
            0.0,
            float(self.get_parameter('startup_full_roi_duration').value),
        )
        self.startup_time = time.monotonic()
        self.narrow_roi_activated = False
        self.left_edge_limit_ratio = float(
            self.get_parameter('left_edge_limit_ratio').value
        )
        self.left_edge_limit_ratio = max(
            0.0,
            min(self.left_edge_limit_ratio, 1.0),
        )
        self.left_edge_critical_ratio = float(
            self.get_parameter('left_edge_critical_ratio').value
        )
        self.left_edge_critical_ratio = max(
            0.0,
            min(self.left_edge_critical_ratio, self.left_edge_limit_ratio),
        )

        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )

        # 동적 ROI 적용 위한 이전 프레임 정보
        self.prev_bbox = None
        self.roi_margin = 120

        self.get_logger().info(
            f'🔍 점자블록 추적 노드가 {image_topic} 구독을 시작했습니다.'
        )

    def image_callback(self, msg: Image):
        frame = self.image_message_to_bgr(msg)
        if frame is None:
            return

        block_type, offset, _, debug_frame = self.analyze_tactile_block(frame)

        # 1. 블록 타입 발행 (STRAIGHT / CORNER / UNKNOWN)
        type_msg = String()
        type_msg.data = block_type
        self.block_pub.publish(type_msg)

        # 2. 오차값 발행
        offset_msg = Float32()
        offset_msg.data = float(offset) if offset is not None else 999.0
        self.edge_offset_pub.publish(offset_msg)

        # 3. 실시간 디버그 모니터링 화면 출력
        cv2.imshow('Tactile Line Tracer Monitor', debug_frame)
        cv2.waitKey(1)

    def image_message_to_bgr(self, msg: Image):
        """sensor_msgs/Image를 OpenCV BGR 영상으로 변환한다."""
        if msg.encoding not in ('bgr8', 'rgb8'):
            self.get_logger().warn(
                f'지원하지 않는 카메라 인코딩입니다: {msg.encoding}',
                throttle_duration_sec=2.0,
            )
            return None

        channels = 3
        expected_row_size = msg.width * channels
        if msg.step < expected_row_size or len(msg.data) < msg.step * msg.height:
            self.get_logger().warn(
                '손상된 카메라 이미지 메시지를 수신했습니다.',
                throttle_duration_sec=2.0,
            )
            return None

        rows = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
        frame = rows[:, :expected_row_size].reshape(msg.height, msg.width, channels)
        if msg.encoding == 'rgb8':
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            frame = frame.copy()
        return frame

    def analyze_tactile_block(self, frame):
        height, width, _ = frame.shape
        debug_frame = frame.copy()  # 모니터링용 프레임 복사

        # ----------------------------------------------------
        # 1. 카메라 시점에 맞춘 ROI 생성
        # ----------------------------------------------------

        roi_mask = np.zeros((height, width), dtype=np.uint8)

        # 최소 준비 시간이 지나고 유효 오프셋이 처음 계산될 때까지
        # 전체 화면에서 블록을 탐색한다. 전환 후에는 하단 ROI를 유지한다.
        full_frame_roi_active = not self.narrow_roi_activated
        roi_top_y = (
            0
            if full_frame_roi_active
            else int(height * self.roi_top_ratio)
        )
        pts = np.array([
            [0, roi_top_y],
            [width - 1, roi_top_y],
            [width - 1, height - 1],
            [0, height - 1],
        ], dtype=np.int32)

        cv2.fillPoly(roi_mask, [pts], 255)

        # HSV 변환은 원본 프레임에서 수행
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_yellow = np.array([15,80,80])
        upper_yellow = np.array([35,255,255])

        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # HSV 결과를 유지한 채 ROI를 적용한다. 기존 코드는 이 지점에서
        # yellow mask를 ROI mask로 덮어써 ROI 전체가 노란색으로 검출됐다.
        mask = cv2.bitwise_and(mask, roi_mask)

        # 코너의 가로 가지가 갑자기 나타날 수 있으므로 이전 프레임의
        # bounding box로 분류용 마스크를 제한하지 않는다.
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask_closed = cv2.morphologyEx(mask_closed, cv2.MORPH_OPEN, kernel)

        # ----------------------------------------------------
        # 2. 상태 표시에 사용할 ROI 내 노란색 비율
        # ----------------------------------------------------
        zone_y1 = int(height * 0.20)
        zone_y2 = int(height * 0.90)
        mask_top_zone = mask_closed[zone_y1:zone_y2, :]
        top_yellow_pixel_count = cv2.countNonZero(mask_top_zone)

        zone_area = cv2.countNonZero(
            roi_mask[zone_y1:zone_y2, :]
        )

        yellow_ratio = (
            top_yellow_pixel_count / zone_area
            if zone_area > 0 else 0.0
        )

        # ----------------------------------------------------
        # 3. 윤곽선 및 좌측 모서리 스캔
        # ----------------------------------------------------
        contours, _ = cv2.findContours(
            mask_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        block_type = 'UNKNOWN'
        left_edge_x = None
        offset = None

        scan_y = int(height * 0.82)
        edge_scan_y = scan_y
        # 차량을 점자블록에서 50cm 떨어뜨렸을 때 측정한 Left Edge X를
        # 목표점으로 사용한다. 해상도 밖의 입력은 유효 픽셀 범위로 제한한다.
        target_x = max(0, min(self.target_edge_x_px, width - 1))
        left_edge_limit_x = int(width * self.left_edge_limit_ratio)
        left_edge_critical_x = int(width * self.left_edge_critical_ratio)

        if contours:
            c = max(contours, key=cv2.contourArea)
            contour_area = cv2.contourArea(c)
            if contour_area > width * height * 0.015:
                x, y, w, h = cv2.boundingRect(c)
                self.prev_bbox = (x, y, w, h)

                # 직선 블록은 원근 때문에 사다리꼴이어도 거의 볼록하다.
                # ㄱ자 블록은 두 방향의 가지 사이에 큰 오목 영역이 생기므로
                # convex hull 대비 실제 면적(solidity)으로 구도를 타지 않게 판별한다.
                hull = cv2.convexHull(c)
                hull_area = cv2.contourArea(hull)
                solidity = contour_area / hull_area if hull_area > 0 else 1.0
                concavity_area = max(0.0, hull_area - contour_area)
                concavity_ratio = concavity_area / (width * height)

                is_corner = (
                    solidity < 0.86
                    and concavity_ratio > 0.018
                    and w > width * 0.28
                    and h > height * 0.18
                )
                # 선택한 윤곽선만 별도 마스크로 만들어 주변의 다른 노란색이
                # 오프셋 계산에 섞이지 않도록 한다.
                contour_mask = np.zeros_like(mask_closed)
                cv2.drawContours(contour_mask, [c], -1, 255, thickness=-1)

                if is_corner:
                    # 차체에 가까운 하단 35%를 진입 방향의 세로 줄기로 보고,
                    # 전체 ㄱ자 영역이 줄기의 어느 쪽으로 더 뻗는지 비교한다.
                    bottom_y = y + int(h * 0.65)
                    bottom_points = np.where(contour_mask[bottom_y:y + h, :] > 0)
                    all_points = np.where(contour_mask[y:y + h, :] > 0)

                    if len(bottom_points[1]) > 0:
                        stem_center_x = float(np.median(bottom_points[1]))
                    else:
                        stem_center_x = x + w * 0.5

                    if len(all_points[1]) > 0:
                        contour_left = int(all_points[1].min())
                        contour_right = int(all_points[1].max())
                        left_reach = stem_center_x - contour_left
                        right_reach = contour_right - stem_center_x
                        corner_direction = (
                            'LEFT' if left_reach > right_reach else 'RIGHT'
                        )
                    else:
                        corner_direction = 'RIGHT'

                    block_type = f'CORNER_{corner_direction}'
                else:
                    block_type = 'STRAIGHT'

                # 우선 기존 하단 스캔라인을 사용한다. 블록 사이의 절단부가
                # 스캔라인에 걸리면 바운딩박스 안에서 위쪽으로 올라가며
                # 가장 가까운 유효 행을 찾아 주행을 계속한다.
                search_start_y = min(scan_y, y + h - 1)
                xs = np.where(contour_mask[search_start_y] > 0)[0]

                if len(xs) == 0:
                    bbox_rows = contour_mask[y:search_start_y + 1, :]
                    valid_rows = np.where(np.any(bbox_rows > 0, axis=1))[0]
                    if len(valid_rows) > 0:
                        edge_scan_y = y + int(valid_rows[-1])
                        xs = np.where(contour_mask[edge_scan_y] > 0)[0]
                else:
                    edge_scan_y = search_start_y

                if len(xs) > 0:
                    left_edge_x = int(xs.min())
                    offset = left_edge_x - target_x
                    if left_edge_x < left_edge_critical_x:
                        block_type = 'LEFT_EDGE_CRITICAL'
                    elif left_edge_x < left_edge_limit_x:
                        block_type = 'LEFT_EDGE_LIMIT'

                    if (
                        time.monotonic() - self.startup_time
                        >= self.startup_full_roi_duration
                    ):
                        self.narrow_roi_activated = True

                # [시각화] 검출된 점자블록 윤곽선 (초록색)
                cv2.drawContours(
                    debug_frame,
                    [c],
                    -1,
                    (0,255,0),
                    2
                )
                cv2.rectangle(
                    debug_frame,
                    (x, y),
                    (x + w - 1, y + h - 1),
                    (255, 255, 0),
                    2,
                )
            else:
                self.prev_bbox = None
        else:
            self.prev_bbox = None

        # ----------------------------------------------------
        # 4. 모니터링 시각화 요소 그리기
        # ----------------------------------------------------
        # A. 화면 하단 45% ROI
        cv2.polylines(
            debug_frame,
            [pts],
            True,
            (0, 165, 255),
            2
        )

        # B. Dynamic ROI
        if self.prev_bbox is not None:

            x, y, w, h = self.prev_bbox

            rx1 = max(0, x - self.roi_margin)
            ry1 = max(0, y - self.roi_margin)

            rx2 = min(width, x + w + self.roi_margin)
            ry2 = min(height, y + h + self.roi_margin)

            cv2.rectangle(
                debug_frame,
                (rx1, ry1),
                (rx2, ry2),
                (255, 0, 255),
                2
            )

        # C. Yellow Ratio 계산 영역
        cv2.rectangle(
            debug_frame,
            (0, zone_y1),
            (width - 1, zone_y2),
            (255, 255, 0),
            1
        )

        # D. Scan Line
        cv2.line(
            debug_frame,
            (0, scan_y),
            (width, scan_y),
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # E. Target X
        cv2.line(
            debug_frame,
            (target_x, 0),
            (target_x, height),
            (255, 0, 0),
            2,
        )

        # F. 좌측 경계 복구 동작 진입 기준선
        cv2.line(
            debug_frame,
            (left_edge_limit_x, 0),
            (left_edge_limit_x, height),
            (0, 0, 255),
            2,
        )

        # 좌측 최대 조향 복구 진입 기준선
        cv2.line(
            debug_frame,
            (left_edge_critical_x, 0),
            (left_edge_critical_x, height),
            (255, 0, 255),
            2,
        )

        # G. 좌측 모서리
        if left_edge_x is not None:
            cv2.circle(
                debug_frame,
                (left_edge_x, edge_scan_y),
                7,
                (0, 0, 255),
                -1,
            )

            cv2.line(
                debug_frame,
                (target_x, edge_scan_y),
                (left_edge_x, edge_scan_y),
                (255, 0, 255),
                3,
            )

            coordinate_text = f'({left_edge_x}, {edge_scan_y})'
            coordinate_x = min(left_edge_x + 10, max(0, width - 180))
            coordinate_y = max(25, edge_scan_y - 12)
            cv2.putText(
                debug_frame,
                coordinate_text,
                (coordinate_x, coordinate_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )
        # H. OSD 텍스트 오버레이 (상단 정보 출력)
        status_color = (
            (0, 255, 0) if block_type.startswith('STRAIGHT') else (0, 0, 255)
        )

        # 1) 블록 상태
        cv2.putText(
            debug_frame,
            f'Block: {block_type}',
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            status_color,
            2,
        )
        # 2) Offset 오차
        offset_str = f'Offset: {offset:.1f} px' if offset is not None else 'Offset: N/A'
        cv2.putText(
            debug_frame,
            offset_str,
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        # 3) [추가] ROI 상단 노란색 픽셀 수 카운트 (Yellow Pixel Count)
        cv2.putText(
          debug_frame,
          f'Yellow Ratio (ROI): {yellow_ratio*100:.1f}%',
          (20,120),
          cv2.FONT_HERSHEY_SIMPLEX,
          0.8,
          (0,255,255),
          2,
        )

        # 4) 오프셋 계산에 사용한 좌측 경계 픽셀 좌표
        left_edge_text = (
            f'Left Edge X: {left_edge_x} px (Y: {edge_scan_y})'
            if left_edge_x is not None
            else 'Left Edge X: N/A'
        )
        cv2.putText(
            debug_frame,
            left_edge_text,
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255) if left_edge_x is not None else (160, 160, 160),
            2,
        )

        cv2.putText(
            debug_frame,
            f'Target X: {target_x} px',
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 0),
            2,
        )

        roi_height_percent = int(round((1.0 - self.roi_top_ratio) * 100))
        roi_mode = (
            'FULL FRAME'
            if full_frame_roi_active
            else f'BOTTOM {roi_height_percent}%'
        )
        cv2.putText(
            debug_frame,
            f'ROI Mode: {roi_mode}',
            (20, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2,
        )

        return block_type, offset, top_yellow_pixel_count, debug_frame

    def destroy_node(self):
        cv2.destroyAllWindows()
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
