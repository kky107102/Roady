from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    main_control_node = Node(
        package='control',
        executable='main_control_node',
        name='main_control_node',
        output='screen',
        parameters=[{
            'drive_speed': 0.4,
            'reverse_speed': 0.4,
            'kp': 0.004,
            'max_steer': 0.75,
            'left_steering_gain': 1.30,
            'steering_deadband_px': 30.0,
            'steering_filter_alpha': 0.35,
            'offset_timeout': 1.0,
            'steering_sign': -1.0,
            'target_edge_x_px': 750.0,
            'corner_target_edge_x_px': 750.0,
            'corner_align_tolerance_px': 30.0,
            'corner_align_kp': 0.004,
            'corner_confirm_frames': 10,
            'corner_backup_duration': 1.5,
            'corner_forward_duration': 1.0,
            'corner_steer': 0.75,
            'startup_duration': 4.0,
            'unknown_vote_frames': 10,
            'unknown_max_consecutive_votes': 5,
            'station_target_samples': 5,
            'station_steering_kp': 0.004,
            'station_end_navy_pixels': 1000,
            'station_end_confirm_frames': 30,
        }],
        remappings=[
            ('/obstacle_warning', LaunchConfiguration('obstacle_stop_topic')),
        ],
    )

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
        DeclareLaunchArgument(
            'shutdown_on_main_exit',
            default_value='false',
            description=(
                'Shut down the complete launch when main control exits'
            ),
        ),
        DeclareLaunchArgument(
            'enable_drive_recording',
            default_value='true',
            description='Record the raw tactile camera topic to an MP4 file',
        ),
        DeclareLaunchArgument(
            'recording_image_topic',
            default_value='/camera/tactile/image_raw',
            description='Raw tactile camera topic to record',
        ),
        DeclareLaunchArgument(
            'recording_output_path',
            default_value='~/%Y%m%d_%H%M%S.mp4',
            description='MP4 path; datetime strftime tokens are supported',
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
        # 2. 가공 전 점자 카메라 원본 영상 저장 노드
        Node(
            package='perception',
            executable='image_topic_video_recorder',
            name='tactile_raw_video_recorder',
            condition=IfCondition(
                LaunchConfiguration('enable_drive_recording')
            ),
            output='screen',
            parameters=[{
                'image_topic': LaunchConfiguration('recording_image_topic'),
                'output_path': LaunchConfiguration('recording_output_path'),
                'output_fps': 30.0,
                'codec': 'mp4v',
            }],
        ),
        # 3. 비전 인지 노드
        Node(
            package='control',
            executable='tactile_tracer_node',
            name='tactile_tracer_node',
            output='screen',
            parameters=[{
                'image_topic': '/camera/tactile/image_raw',
                'target_edge_x_px': 750,
                'roi_top_ratio': 0.55,
                'station_navy_min_pixels': 3500,
            }],
        ),
        # # 4. 라이다 장애물 탐지 노드
        # Node(
        #     package='control',
        #     executable='lidar_warning_node',
        #     name='lidar_warning_node',
        #     condition=IfCondition(LaunchConfiguration('enable_lidar')),
        #     output='screen'
        # ),

        # 5. 하드웨어 액추에이터 노드
        Node(
            package='control',
            executable='motor_node',
            name='motor_node',
            output='screen'
        ),
        # 6. 자율주행 판단 및 자동 출발 메인 노드
        main_control_node,
        RegisterEventHandler(
            OnProcessExit(
                target_action=main_control_node,
                on_exit=[
                    EmitEvent(
                        event=Shutdown(
                            reason='Main controller finished driving'
                        )
                    )
                ],
            ),
            condition=IfCondition(
                LaunchConfiguration('shutdown_on_main_exit')
            ),
        ),
    ])
