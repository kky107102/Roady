from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'obstacle_stop_topic',
            default_value='/obstacle_warning',
            description='Obstacle stop topic consumed by main_control_node',
        ),
        DeclareLaunchArgument(
            'enable_lidar',
            default_value='false',
            description='Start the standalone LiDAR obstacle detector',
        ),
        # 1. 점자블록 인식용 카메라 노드
        Node(
            package='hardware',
            executable='tactile_camera_node',
            name='tactile_camera_node',
            output='screen',
            parameters=[{
                'device_path': 'usb-046d_Brio_100_2515ZBA0WRC8-video-index0',
                'width': 1280,
                'height': 720,
                'fps': 30,
                'publish_rate': 30.0,
                'frame_id': 'tactile_camera',
                'topic': '/camera/tactile/image_raw',
            }],
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
                'left_edge_extreme_ratio': 0.20,
            }],
        ),
        # # 3. 라이다 장애물 탐지 노드
        # Node(
        #     package='control',
        #     executable='lidar_warning_node',
        #     name='lidar_warning_node',
        #     condition=IfCondition(LaunchConfiguration('enable_lidar')),
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
                'startup_crawl_speed': 0.5,
                'drive_speed': 0.65,
                'reverse_speed': 0.5,
                'steering_speed_boost': 0.05,
                'kp': 0.004,
                'max_steer': 0.75,
                'left_steering_gain': 1.30,
                'steering_deadband_px': 8.0,
                'steering_filter_alpha': 0.35,
                'offset_timeout': 1.0,
                'steering_sign': -1.0,
                'backup_duration': 1.5,
                'corner_turn_duration': 2.0,
                'corner_steer': 0.75,
                'corner_steering_sign': 1.0,
                'left_edge_stop_duration': 0.5,
                'left_edge_backup_duration': 1.0,
                'left_edge_extreme_backup_multiplier': 2.0,
                'left_edge_turn_duration': 1.0,
                'left_edge_recovery_steer': 0.75,
            }],
            remappings=[
                ('/obstacle_warning', LaunchConfiguration('obstacle_stop_topic')),
            ],
        ),
    ])
