#!/usr/bin/env python3

import json
import time
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, String, UInt32


class TactileTracerNode(Node):

    def __init__(self):
        super().__init__('tactile_tracer_node')

        # 토픽 Publisher
        self.block_pub = self.create_publisher(String, '/tactile/block_type', 10)
        self.edge_offset_pub = self.create_publisher(Float32, '/tactile/edge_offset', 10)
        self.leftmost_pub = self.create_publisher(Float32, '/tactile/leftmost_x', 10)
        self.full_frame_ratio_pub = self.create_publisher(
            Float32, '/tactile/full_frame_yellow_ratio', 10
        )
        self.station_navy_count_pub = self.create_publisher(
            UInt32, '/tactile/station_navy_count', 10
        )
        self.full_frame_navy_count_pub = self.create_publisher(
            UInt32, '/tactile/full_frame_navy_count', 10
        )
        self.station_rightmost_pub = self.create_publisher(
            Float32, '/tactile/station_rightmost_x', 10
        )

        self.declare_parameter('image_topic', '/camera/tactile/image_raw')
        self.declare_parameter(
            'damage_annotated_topic', '/tactile/damage_annotated'
        )
        self.declare_parameter('damage_detection_topic', '/damage/detections')
        self.declare_parameter('damage_overlay_timeout_sec', 0.3)
        self.declare_parameter('target_edge_x_px', 750)
        self.declare_parameter('roi_top_ratio', 0.55)
        self.declare_parameter('station_navy_min_pixels', 3500)
        image_topic = str(self.get_parameter('image_topic').value)
        damage_annotated_topic = str(
            self.get_parameter('damage_annotated_topic').value
        )
        damage_detection_topic = str(
            self.get_parameter('damage_detection_topic').value
        )
        self.damage_overlay_timeout_sec = max(
            0.0,
            float(self.get_parameter('damage_overlay_timeout_sec').value),
        )
        self.target_edge_x_px = int(
            self.get_parameter('target_edge_x_px').value
        )
        self.roi_top_ratio = float(self.get_parameter('roi_top_ratio').value)
        self.roi_top_ratio = max(0.05, min(self.roi_top_ratio, 0.75))
        self.station_navy_min_pixels = max(
            1, int(self.get_parameter('station_navy_min_pixels').value)
        )
        self.tracking_state = 'UNKNOWN'
        self.last_station_navy_count = 0
        self.last_full_frame_navy_count = 0
        self.last_station_rightmost_point = None

        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )
        self.damage_annotated_pub = self.create_publisher(
            Image,
            damage_annotated_topic,
            qos_profile_sensor_data,
        )
        self.state_sub = self.create_subscription(
            String,
            '/tactile/tracking_state',
            self.tracking_state_callback,
            10,
        )
        self.damage_detection_sub = self.create_subscription(
            String,
            damage_detection_topic,
            self.damage_detection_callback,
            10,
        )
        self.latest_damage_detections = []
        self.last_damage_detection_time = 0.0

        self.prev_bbox = None

        self.get_logger().info(
            f'🔍 점자블록 추적 노드가 {image_topic} 구독을 시작했습니다.'
        )

    def image_callback(self, msg: Image):
        frame = self.image_message_to_bgr(msg)
        if frame is None:
            return

        block_type, offset, _, leftmost_x, debug_frame = (
            self.analyze_tactile_block(frame)
        )
        self.draw_damage_overlay(debug_frame)
        # Publish the same combined line-tracking + damage overlay shown in
        # the monitor so drive recordings contain the complete visualization.
        self.damage_annotated_pub.publish(
            self.bgr_to_image_message(debug_frame, msg)
        )

        # 1. 블록 타입 발행 (STRAIGHT / CORNER / UNKNOWN)
        type_msg = String()
        type_msg.data = block_type
        self.block_pub.publish(type_msg)

        # 2. 오차값 발행
        offset_msg = Float32()
        offset_msg.data = float(offset) if offset is not None else 999.0
        self.edge_offset_pub.publish(offset_msg)

        leftmost_msg = Float32()
        leftmost_msg.data = float(leftmost_x) if leftmost_x is not None else -1.0
        self.leftmost_pub.publish(leftmost_msg)

        ratio_msg = Float32()
        ratio_msg.data = float(self.last_full_frame_yellow_ratio)
        self.full_frame_ratio_pub.publish(ratio_msg)

        station_count_msg = UInt32()
        station_count_msg.data = self.last_station_navy_count
        self.station_navy_count_pub.publish(station_count_msg)

        full_frame_navy_count_msg = UInt32()
        full_frame_navy_count_msg.data = self.last_full_frame_navy_count
        self.full_frame_navy_count_pub.publish(full_frame_navy_count_msg)

        station_rightmost_msg = Float32()
        station_rightmost_msg.data = (
            float(self.last_station_rightmost_point[0])
            if self.last_station_rightmost_point is not None else -1.0
        )
        self.station_rightmost_pub.publish(station_rightmost_msg)

        # 3. 실시간 디버그 모니터링 화면 출력
        cv2.imshow('Tactile Line Tracer Monitor', debug_frame)
        cv2.waitKey(1)

    def tracking_state_callback(self, msg: String):
        self.tracking_state = msg.data

    def damage_detection_callback(self, msg: String):
        try:
            payload = json.loads(msg.data)
            detections = payload.get('detections', [])
            self.latest_damage_detections = [
                detection
                for detection in detections
                if (
                    isinstance(detection, dict)
                    and detection.get('label') == 'damage_candidate'
                    and len(detection.get('xyxy', [])) == 4
                )
            ]
            self.last_damage_detection_time = time.monotonic()
        except (json.JSONDecodeError, TypeError, ValueError):
            self.get_logger().warn(
                '파손 탐지 결과 메시지를 해석할 수 없습니다.',
                throttle_duration_sec=2.0,
            )

    def draw_damage_overlay(self, debug_frame):
        if (
            time.monotonic() - self.last_damage_detection_time
            > self.damage_overlay_timeout_sec
        ):
            return

        height, width = debug_frame.shape[:2]
        for detection in self.latest_damage_detections:
            try:
                x1, y1, x2, y2 = (
                    int(round(float(value))) for value in detection['xyxy']
                )
                confidence = float(detection.get('confidence', 0.0))
            except (TypeError, ValueError):
                continue
            x1 = max(0, min(width - 1, x1))
            y1 = max(0, min(height - 1, y1))
            x2 = max(0, min(width - 1, x2))
            y2 = max(0, min(height - 1, y2))
            cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(
                debug_frame,
                f'damage_candidate {confidence:.2f}',
                (x1, max(24, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

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

    @staticmethod
    def bgr_to_image_message(frame, source_msg):
        """OpenCV BGR 프레임을 원본 시각의 ROS 이미지로 변환한다."""
        output = Image()
        output.header = source_msg.header
        output.height, output.width = frame.shape[:2]
        output.encoding = 'bgr8'
        output.is_bigendian = 0
        output.step = output.width * 3
        output.data = np.ascontiguousarray(frame).tobytes()
        return output

    def analyze_tactile_block(self, frame):
        height, width, _ = frame.shape
        debug_frame = frame.copy()  # 모니터링용 프레임 복사

        # ----------------------------------------------------
        # 1. 카메라 시점에 맞춘 ROI 생성
        # ----------------------------------------------------

        roi_mask = np.zeros((height, width), dtype=np.uint8)

        # STARTUP, UNKNOWN, 코너, STATION에서는 전체 화면을 사용한다.
        full_frame_roi_active = self.tracking_state != 'STRAIGHT'
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

        (
            self.last_station_navy_count,
            self.last_station_rightmost_point,
            self.last_full_frame_navy_count,
        ) = self._station_navy_metrics(hsv)

        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([35, 255, 255])

        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # 코너 탈출 완료 여부는 높이 제한 없이 전체 화면의 노란색 점유율로 판단한다.
        full_frame_area = max(1, height * width)
        self.last_full_frame_yellow_ratio = cv2.countNonZero(mask) / full_frame_area

        # HSV 결과를 유지한 채 ROI를 적용한다. 기존 코드는 이 지점에서
        # yellow mask를 ROI mask로 덮어써 ROI 전체가 노란색으로 검출됐다.
        mask = cv2.bitwise_and(mask, roi_mask)

        # 코너의 가로 가지가 갑자기 나타날 수 있으므로 이전 프레임의
        # bounding box로 분류용 마스크를 제한하지 않는다.
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask_closed = cv2.morphologyEx(mask_closed, cv2.MORPH_OPEN, kernel)
        # 코너 정렬점은 형태학 연산으로 채워진 픽셀이 아니라 HSV 조건을
        # 실제로 통과한 ROI 내 노란색 픽셀 중 X가 가장 작은 점을 사용한다.
        yellow_points = np.where(mask > 0)
        leftmost_point = None
        if len(yellow_points[1]) > 0:
            leftmost_index = int(np.argmin(yellow_points[1]))
            leftmost_point = (
                int(yellow_points[1][leftmost_index]),
                int(yellow_points[0][leftmost_index]),
            )
        leftmost_x = leftmost_point[0] if leftmost_point is not None else None

        # ----------------------------------------------------
        # 2. 상태 표시에 사용할 ROI 내 노란색 비율
        # ----------------------------------------------------
        zone_y1 = int(height * 0.20)
        zone_y2 = int(height * 0.90)
        mask_top_zone = mask_closed[zone_y1:zone_y2, :]
        top_yellow_pixel_count = cv2.countNonZero(mask_top_zone)

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
                )
                # 선택한 윤곽선만 별도 마스크로 만들어 주변의 다른 노란색이
                # 오프셋 계산에 섞이지 않도록 한다.
                contour_mask = np.zeros_like(mask_closed)
                cv2.drawContours(contour_mask, [c], -1, 255, thickness=-1)

                if is_corner:
                    # 전체 화면 ROI의 모든 노란색 픽셀 중 최좌측 카메라
                    # 절대 X 좌표를 기준으로 코너 방향을 판정한다.
                    corner_direction = (
                        'LEFT'
                        if leftmost_x is not None and leftmost_x < target_x
                        else 'RIGHT'
                    )

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
                cv2.drawContours(
                    debug_frame,
                    [c],
                    -1,
                    (0, 255, 0),
                    2,
                )
            else:
                self.prev_bbox = None
        else:
            self.prev_bbox = None

        if self.last_station_navy_count >= self.station_navy_min_pixels:
            block_type = 'STATION'

        # ----------------------------------------------------
        # 4. 모니터링 시각화 요소 그리기
        # ----------------------------------------------------
        # A. 실제 판정에 사용하는 ROI 영역
        cv2.polylines(
            debug_frame,
            [pts],
            True,
            (0, 165, 255),
            2,
        )

        # B. 점자블록 left edge 픽셀
        if left_edge_x is not None:
            cv2.circle(
                debug_frame,
                (left_edge_x, edge_scan_y),
                7,
                (255, 0, 255),
                -1,
            )

        # C. STATION 판정에 사용되는 최우측 남색 픽셀
        if block_type == 'STATION' and self.last_station_rightmost_point is not None:
            station_x, station_y = self.last_station_rightmost_point
            cv2.circle(
                debug_frame,
                self.last_station_rightmost_point,
                8,
                (255, 0, 255),
                -1,
            )
            label_x = min(station_x + 10, max(0, width - 260))
            label_y = min(max(25, station_y + 25), height - 10)
            cv2.putText(
                debug_frame,
                f'({station_x}, {station_y})',
                (label_x, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 255),
                2,
            )

        # 좌상단에는 FSM 상태, 오프셋, ROI 모드만 표시한다.
        cv2.putText(
            debug_frame,
            f'State: {self.tracking_state}',
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

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

        roi_height_percent = int(round((1.0 - self.roi_top_ratio) * 100))
        roi_mode = (
            'FULL FRAME'
            if full_frame_roi_active
            else f'BOTTOM {roi_height_percent}%'
        )
        cv2.putText(
            debug_frame,
            f'ROI Mode: {roi_mode}',
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2,
        )

        return block_type, offset, top_yellow_pixel_count, leftmost_x, debug_frame

    @staticmethod
    def _station_navy_metrics(hsv):
        """Return navy letter pixels and their rightmost point on a white sign."""
        navy_mask = cv2.inRange(
            hsv,
            np.array([95, 55, 15], dtype=np.uint8),
            np.array([130, 255, 155], dtype=np.uint8),
        )
        component_count, labels, stats, _ = cv2.connectedComponentsWithStats(
            navy_mask, 8
        )
        components = []
        for label in range(1, component_count):
            x, y, w, h, area = (int(value) for value in stats[label])
            if area < 20 or w < 3 or h < 3 or w > 250 or h > 180:
                continue

            component_hsv = hsv[y:y + h, x:x + w]
            component_pixels = navy_mask[y:y + h, x:x + w] > 0
            background_pixels = ~component_pixels
            white_background = (
                (component_hsv[:, :, 1] < 70)
                & (component_hsv[:, :, 2] > 60)
                & background_pixels
            )
            white_ratio = cv2.countNonZero(
                white_background.astype(np.uint8)
            ) / max(1, cv2.countNonZero(background_pixels.astype(np.uint8)))
            if white_ratio > 0.35:
                components.append((label, area, x, y, w, h))

        groups = []
        visited = set()
        for index in range(len(components)):
            if index in visited:
                continue
            stack = [index]
            visited.add(index)
            group = []
            while stack:
                current = stack.pop()
                group.append(current)
                _, _, x1, y1, w1, h1 = components[current]
                for candidate in range(len(components)):
                    if candidate in visited:
                        continue
                    _, _, x2, y2, w2, h2 = components[candidate]
                    x_gap = max(0, max(x1, x2) - min(x1 + w1, x2 + w2))
                    y_gap = max(0, max(y1, y2) - min(y1 + h1, y2 + h2))
                    scale = max(h1, h2)
                    if x_gap <= 1.5 * scale and y_gap <= 0.8 * scale:
                        visited.add(candidate)
                        stack.append(candidate)
            if len(group) >= 6:
                groups.append(group)

        if not groups:
            return 0, None, cv2.countNonZero(navy_mask)

        selected = max(
            groups,
            key=lambda group: sum(components[index][1] for index in group),
        )
        selected_labels = np.array(
            [components[index][0] for index in selected], dtype=labels.dtype
        )
        station_mask = np.isin(labels, selected_labels)
        station_y, station_x = np.where(station_mask)
        if len(station_x) == 0:
            return 0, None, cv2.countNonZero(navy_mask)

        rightmost_index = int(np.argmax(station_x))
        return (
            int(len(station_x)),
            (
                int(station_x[rightmost_index]),
                int(station_y[rightmost_index]),
            ),
            cv2.countNonZero(navy_mask),
        )

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
