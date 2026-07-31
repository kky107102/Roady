import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # X4-Pro.yaml 경로 설정
    driver_share_dir = get_package_share_directory('ydlidar_ros2_driver')
    ydlidar_param_file = os.path.join(driver_share_dir, 'params', 'X4-Pro.yaml')

    return LaunchDescription([
        # 1. YDLidar X4 Pro 드라이버 노드
        Node(
            package='ydlidar_ros2_driver',
            executable='ydlidar_ros2_driver_node',
            name='ydlidar_ros2_driver_node',
            output='screen',
            emulate_tty=True,
            parameters=[ydlidar_param_file]
        ),

        # 2. 장애물 감지 노드 (50cm 제한)
        Node(
            package='control',
            executable='lidar_warning_node',
            name='lidar_warning_node',
            output='screen'
        ),

        # 3. 모터 제어 노드 (PCA9685 조향/주행 모터 제어)
        Node(
            package='control',
            executable='motor_node',
            name='motor_node',
            output='screen'
        ),

        # 4. 키보드 제어 노드 (cmd_vel 발행)
        Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            name='teleop_twist_keyboard',
            output='screen',
            prefix='xterm -e'  # 키보드 입력을 위한 별도 터미널 창 실행
        ),
    ])
