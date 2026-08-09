from pathlib import Path

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
from launch_ros.parameter_descriptions import ParameterValue


def _default_damage_model_path():
    relative_path = Path(
        'artifacts/tactile_damage_candidate/'
        'v4/'
        'tactile_damage_candidate_yolo26n_best.engine'
    )
    for parent in Path(__file__).resolve().parents:
        candidate = parent / relative_path
        if candidate.is_file():
            return str(candidate)
    return str(relative_path)


def generate_launch_description():
    main_control_node = Node(
        package='control',
        executable='main_control_node',
        name='main_control_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('start_drive')),
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
            'station_end_confirm_frames': 10,
            'wait_for_upload': ParameterValue(
                LaunchConfiguration('wait_for_upload'), value_type=bool
            ),
            'upload_wait_timeout_sec': 60.0,
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
            'wait_for_upload',
            default_value='false',
            description='Wait for arrival-triggered damage upload before shutdown',
        ),
        DeclareLaunchArgument(
            'enable_drive_recording',
            default_value='true',
            description='Record the raw tactile camera topic to an MP4 file',
        ),
        DeclareLaunchArgument(
            'recording_image_topic',
            default_value='/tactile/damage_annotated',
            description='Damage-only annotated tactile image topic to record',
        ),
        DeclareLaunchArgument(
            'recording_output_path',
            default_value='~/%Y%m%d_%H%M%S.mp4',
            description='MP4 path; datetime strftime tokens are supported',
        ),
        DeclareLaunchArgument(
            'start_damage_detection',
            default_value='true',
            description='Start damage detection on the tactile camera stream',
        ),
        DeclareLaunchArgument(
            'damage_model_path',
            default_value=_default_damage_model_path(),
            description='TensorRT engine used by damage_detection_node',
        ),
        DeclareLaunchArgument(
            'damage_process_every_n_frames',
            default_value='2',
            description='Run damage inference every 2 frames (up to 15 FPS)',
        ),
        DeclareLaunchArgument(
            'start_line_tracking',
            default_value='true',
            description='Start tactile_tracer_node',
        ),
        DeclareLaunchArgument(
            'start_drive',
            default_value='true',
            description='Start motor_node and main_control_node',
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
            condition=IfCondition(LaunchConfiguration('start_line_tracking')),
            parameters=[{
                'image_topic': '/camera/tactile/image_raw',
                'damage_annotated_topic': '/tactile/damage_annotated',
                'damage_detection_topic': '/damage/detections',
                'damage_overlay_timeout_sec': 0.3,
                'target_edge_x_px': 750,
                'roi_top_ratio': 0.55,
                'station_navy_min_pixels': 3500,
            }],
        ),
        # 4. 촉각 카메라 파손 탐지 노드
        Node(
            package='perception',
            executable='damage_detection_node',
            name='damage_detection_node',
            output='screen',
            condition=IfCondition(
                LaunchConfiguration('start_damage_detection')
            ),
            parameters=[{
                'image_topic': '/camera/tactile/image_raw',
                'detection_topic': '/damage/detections',
                'location_topic': '/location/fix',
                'detect_model_path': LaunchConfiguration('damage_model_path'),
                'inference_device': '0',
                'inference_image_size': 768,
                'detection_threshold': 0.225,
                'require_tactile_roi_for_event': True,
                'require_verified_frame_for_event': True,
                'minimum_event_confidence': 0.375,
                'group_by_tactile_unit': True,
                'stable_observation_count': 2,
                'process_every_n_frames': ParameterValue(
                    LaunchConfiguration('damage_process_every_n_frames'),
                    value_type=int,
                ),
                'publish_annotated': False,
                'detection_only_mode': False,
                'confirm_count': 3,
                'confirm_window_sec': 2.0,
                'min_confirm_duration_sec': 0.2,
                'min_observation_interval_sec': 0.1,
                'candidate_timeout_sec': 1.2,
                'reported_track_cooldown_sec': 10.0,
            }],
        ),
        # # 5. 라이다 장애물 탐지 노드
        # Node(
        #     package='control',
        #     executable='lidar_warning_node',
        #     name='lidar_warning_node',
        #     condition=IfCondition(LaunchConfiguration('enable_lidar')),
        #     output='screen'
        # ),

        # 6. 하드웨어 액추에이터 노드
        Node(
            package='control',
            executable='motor_node',
            name='motor_node',
            output='screen',
            condition=IfCondition(LaunchConfiguration('start_drive')),
        ),
        # 7. 자율주행 판단 및 자동 출발 메인 노드
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
