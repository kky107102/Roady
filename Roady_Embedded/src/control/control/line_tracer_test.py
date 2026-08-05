import cv2
import numpy as np


def detect_tactile_left_edge(frame):
    """카메라 원본 이미지에서 점자블록의 좌측 모서리 X 좌표를 검출합니다.

    :param frame: 카메라 입력 이미지 (BGR 형식, e.g., 640x480)
    :return: (left_edge_x, debug_frame)
             - left_edge_x: ROI 스캔라인 기준 점자블록 좌측 모서리 X 좌표 (미인식 시 None)
             - debug_frame: 시각화 처리가 완료된 ROI 디버깅 이미지
    """
    height, width, _ = frame.shape

    # 1. ROI(관심영역) 설정: 카메라 하단 50% 영역만 자르기
    roi_y_start = int(height * 0.5)
    roi = frame[roi_y_start:height, 0:width]
    roi_h, roi_w, _ = roi.shape

    # 2. HSV 색상 공간 변환 및 노란색 영역 마스킹
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # 조명 환경에 따른 노란색 HSV 범위 설정 (H: Hue, S: Saturation, V: Value)
    lower_yellow = np.array([15, 80, 80])
    upper_yellow = np.array([35, 255, 255])
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # 3. 모폴로지 연산 (Closing): 돌기 패턴으로 인한 마스크 내부 구멍 메우기
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 4. 윤곽선(Contour) 검출
    contours, _ = cv2.findContours(
        mask_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    left_edge_x = None
    debug_frame = roi.copy()

    # ROI 내부 기준 스캔라인 높이 (ROI 상단에서 60% 지점)
    scan_y = int(roi_h * 0.6)

    if contours:
        # 노이즈를 제외하고 가장 큰 면적의 윤곽선(점자블록 덩어리) 선택
        c = max(contours, key=cv2.contourArea)

        if cv2.contourArea(c) > 1000:  # 최소 노이즈 면적 기준
            # 스캔라인(Y=scan_y) 부근과 만나는 윤곽선 점들의 X 좌표 추출
            points_at_scany = [
                p[0][0] for p in c if abs(p[0][1] - scan_y) <= 2
            ]

            if points_at_scany:
                # 그 중 '가장 좌측(최소값)'에 위치한 X 좌표를 좌측 모서리로 판단
                left_edge_x = min(points_at_scany)

            # 시각화 1: 검출된 점자블록 전체 윤곽선 (초록색 테두리)
            cv2.drawContours(debug_frame, [c], -1, (0, 255, 0), 2)

    # 5. 디버깅 안내선 및 모서리 점 표시
    # 가로 스캔라인 (노란색 점선)
    cv2.line(
        debug_frame, (0, scan_y), (roi_w, scan_y), (0, 255, 255), 1, cv2.LINE_AA
    )

    # 화면 중앙선 (파란색 선)
    car_center_x = width // 2
    cv2.line(
        debug_frame,
        (car_center_x, 0),
        (car_center_x, roi_h),
        (255, 0, 0),
        2,
    )

    if left_edge_x is not None:
        # 검출된 좌측 모서리 위치 (빨간색 원)
        cv2.circle(debug_frame, (left_edge_x, scan_y), 6, (0, 0, 255), -1)

    return left_edge_x, debug_frame

if __name__ == '__main__':
    # 웹캠 열기 (USB 카메라는 보통 0번 또는 1번)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 좌측 모서리 검출 로직 호출
        edge_x, debug_img = detect_tactile_left_edge(frame)

        # 터미널에 검출된 X 좌표 출력
        if edge_x is not None:
            print(f'📍 점자블록 좌측 모서리 X 좌표: {edge_x} px')
        else:
            print('⚠️ 점자블록 미인식')

        # 화면 출력
        cv2.imshow('Tactile Left Edge Detection', debug_img)

        # 'q' 키 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
