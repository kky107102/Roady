# ROADY hardware nodes

## 와이드카메라 학습 데이터 캡처

촉각 검사 카메라 노드가 `/camera/tactile/image_raw` 토픽을 발행하는 상태에서 캡처 뷰어를 실행한다.

```bash
cd Roady_Embedded
PYTHONNOUSERSITE=1 colcon build --symlink-install --packages-select hardware
source install/setup.bash
ros2 run hardware tactile_camera_capture_viewer
```

`PYTHONNOUSERSITE=1`은 사용자 경로에 별도로 설치된 `setuptools`가 ROS 2 Humble의 시스템 `packaging`과 충돌하는 것을 방지한다. 이 설정은 해당 빌드 명령에만 적용된다.

뷰어에서 `S` 또는 `Space`를 누르거나 우측 상단의 `SAVE` 버튼을 클릭하면 현재 원본 프레임을 JPEG로 저장한다. `Q` 또는 `Esc`로 종료한다. 기본 저장 경로는 `~/roady_dataset/wide_camera`이며 파일명은 `wide_YYYYMMDD_HHMMSS_ffffff.jpg` 형식이다.

저장 경로를 바꾸려면 ROS 파라미터를 전달한다.

```bash
ros2 run hardware tactile_camera_capture_viewer --ros-args \
  -p output_dir:=/home/ssafy/datasets/wide_camera
```

다른 토픽을 볼 때는 `topic` 파라미터도 변경할 수 있다.

```bash
ros2 run hardware tactile_camera_capture_viewer --ros-args \
  -p topic:=/camera/tactile/image_raw \
  -p output_dir:=/home/ssafy/datasets/wide_camera
```
