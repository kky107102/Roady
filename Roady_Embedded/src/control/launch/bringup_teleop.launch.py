import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. 점자블록 인식용 카메라 노드
        Node(
            package='hardware',
            executable='tactile_camera_node',
            name='tactile_camera_node',
            output='screen',
            parameters=[{
                'device_index': 0,
                'device_path': '',
                'width': 1280,
                'height': 720,
                'fps': 30,
                'publish_rate': 30.0,
                'frame_id': 'tactile_camera',
                'topic': '/camera/tactile/image_raw',
            }]
        ),
        # 2. 비전 인지 노드
        Node(
            package='control',
            executable='tactile_tracer_node',
            name='tactile_tracer_node',
            output='screen',
            parameters=[{
                'image_topic': '/camera/tactile/image_raw',
                'target_edge_x_px': 750,
                'roi_top_ratio': 0.55,
                'startup_full_roi_duration': 5.0,
                'left_edge_limit_ratio': 0.50,
                'left_edge_critical_ratio': 0.30,
            }]
        ),
        # # 3. 라이다 장애물 탐지 노드
        # Node(
        #     package='control',
        #     executable='lidar_warning_node',
        #     name='lidar_warning_node',
        #     output='screen'
        # ),

        # 4. 하드웨어 액추에이터 노드
        Node(
            package='control',
            executable='motor_node',
            name='motor_node',
            output='screen'
        ),
        # 5. 자율주행 판단 및 자동 출발 메인 노드
        Node(
            package='control',
            executable='main_control_node',
            name='main_control_node',
            output='screen',
            parameters=[{
                'startup_delay': 5.0,
                'startup_crawl_duration': 1.0,
                'startup_crawl_speed': 0.20,
                'drive_speed': 0.35,
                'steering_speed_boost': 0.05,
                'kp': 0.004,
                'max_steer': 0.75,
                'left_steering_gain': 1.30,
                'steering_deadband_px': 8.0,
                'steering_filter_alpha': 0.35,
                'offset_timeout': 0.30,
                'steering_sign': -1.0,
                'backup_duration': 1.5,
                'corner_turn_duration': 2.0,
                'corner_steer': 0.75,
                'corner_steering_sign': 1.0,
                'left_edge_stop_duration': 0.5,
                'left_edge_backup_duration': 1.0,
                'left_edge_turn_duration': 1.0,
                'left_edge_recovery_steer': 0.75,
            }]
        ),
    ])
