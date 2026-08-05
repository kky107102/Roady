# Jetson YOLO26n 파손 후보 탐지 배포

## 확정 파이프라인

- Edge 모델: `YOLO26n Detect` 단일 모델
- 클래스: `tactile_block`, `damage_candidate`
- 입력 크기: `768`
- 기본 동작: 분류기 미사용 (`use_damage_classifier=false`)
- 이벤트: 연속 프레임에서 반복 검출된 파손 후보의 원본 이미지와 ROI 저장·전송
- 기존 YOLO11n 분류기는 단일 Detect 성능 저하 시에만 켤 수 있는 롤백 경로로 유지

## Jetson에서 ONNX → TensorRT FP16 변환

TensorRT 엔진은 JetPack, CUDA, TensorRT 및 Jetson 하드웨어에 종속되므로 Jetson Orin Nano에서 직접 생성한다.

```bash
python ROADY_AI/tactile_damage_detect/export_jetson.py \
  --weights ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt \
  --imgsz 768 \
  --workspace-mib 2048 \
  --output ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_fp16.engine
```

스크립트는 먼저 고정 입력 `batch=1`, `768x768` ONNX를 만들고, `trtexec --fp16`으로 엔진을 생성한다.

## ROS 2 실행

PyTorch 모델 확인:

```bash
ros2 run perception damage_detection_node --ros-args \
  -p detect_model_path:=../ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt \
  -p image_size:=768 \
  -p use_damage_classifier:=false
```

TensorRT 엔진 실행:

```bash
ros2 run perception damage_detection_node --ros-args \
  -p detect_model_path:=../ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_fp16.engine \
  -p image_size:=768 \
  -p use_damage_classifier:=false
```

`.engine` 입력 크기는 엔진에 고정된다. ROS의 `image_size`도 768로 유지해 설정과 배포 산출물의 기준을 일치시킨다.

## TensorRT 출력 호환성

커스텀 러너는 다음 두 출력 형식을 처리한다.

- YOLO26 end-to-end: `[N, 6]` (`x1, y1, x2, y2, confidence, class_id`)
- 기존 Ultralytics raw: `[1, 4+classes, N]` 또는 `[1, N, 4+classes]`

YOLO26 end-to-end 출력은 모델 그래프에서 NMS가 완료된 것으로 처리하며, 기존 raw 출력만 OpenCV NMS를 적용한다.

## Jetson 완료 기준

- FP16 엔진 로드 및 카메라 입력 추론 성공
- `damage_candidate` 클래스 좌표와 신뢰도 정상 출력
- 768 입력 기준 15 FPS 이상
- 전체 로봇 프로세스 포함 메모리 사용량 4 GB 이하
- PyTorch와 TensorRT의 고정 검증 영상 이벤트 Recall 차이 2%p 이내
