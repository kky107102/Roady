import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    control_share = get_package_share_directory('control')
    lidar_share = get_package_share_directory('ydlidar_ros2_driver')

    model_path = LaunchConfiguration('obstacle_model_path')
    camera_device_path = LaunchConfiguration('obstacle_camera_device_path')
    lidar_params = LaunchConfiguration('lidar_params_file')
    enable_lidar = LaunchConfiguration('enable_lidar')
    enable_drive_recording = LaunchConfiguration('enable_drive_recording')
    recording_image_topic = LaunchConfiguration('recording_image_topic')
    recording_output_path = LaunchConfiguration('recording_output_path')
    start_damage_detection = LaunchConfiguration('start_damage_detection')
    damage_model_path = LaunchConfiguration('damage_model_path')
    damage_process_every_n_frames = LaunchConfiguration(
        'damage_process_every_n_frames'
    )
    start_line_tracking = LaunchConfiguration('start_line_tracking')
    start_drive = LaunchConfiguration('start_drive')
    start_image_upload = LaunchConfiguration('start_image_upload')
    upload_enabled = LaunchConfiguration('upload_enabled')
    upload_base_url = LaunchConfiguration('upload_base_url')
    upload_access_token = LaunchConfiguration('upload_access_token')
    obstacle_roi_left_ratio = LaunchConfiguration('obstacle_roi_left_ratio')
    obstacle_roi_top_ratio = LaunchConfiguration('obstacle_roi_top_ratio')
    obstacle_roi_right_ratio = LaunchConfiguration('obstacle_roi_right_ratio')
    obstacle_roi_bottom_ratio = LaunchConfiguration('obstacle_roi_bottom_ratio')
    obstacle_publish_annotated = LaunchConfiguration('obstacle_publish_annotated')
    obstacle_min_ground_y_ratio = LaunchConfiguration('obstacle_min_ground_y_ratio')
    obstacle_min_box_height_ratio = LaunchConfiguration(
        'obstacle_min_box_height_ratio'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'obstacle_model_path',
            default_value='artifacts/obstacle_lower_limb/best.engine',
            description='Lower-limb detector model (.engine, .onnx, or .pt)',
        ),
        DeclareLaunchArgument(
            'obstacle_camera_device_path',
            default_value='usb-HBVCAM_Camera_USB_Camera_HB202400001-video-index0',
            description='Obstacle camera name under /dev/v4l/by-id',
        ),
        DeclareLaunchArgument(
            'lidar_params_file',
            default_value=os.path.join(lidar_share, 'params', 'X4-Pro.yaml'),
        ),

        DeclareLaunchArgument(
            'enable_lidar',
            default_value='true',
            description='Start LiDAR driver and obstacle detector',
        ),
        DeclareLaunchArgument(
            'enable_drive_recording',
            default_value='true',
            description='Record the driving webcam topic to an MP4 file',
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
            default_value=(
                'artifacts/tactile_damage_candidate/'
                'v4/'
                'tactile_damage_candidate_yolo26n_best.engine'
            ),
            description='TensorRT engine used by damage_detection_node',
        ),
        DeclareLaunchArgument(
            'damage_process_every_n_frames',
            default_value='3',
            description='Run damage inference every N tactile-camera frames',
        ),
        DeclareLaunchArgument('start_line_tracking', default_value='true'),
        DeclareLaunchArgument('start_drive', default_value='true'),
        DeclareLaunchArgument('start_image_upload', default_value='true'),
        DeclareLaunchArgument('upload_enabled', default_value='false'),
        DeclareLaunchArgument(
            'upload_base_url',
            default_value='https://i15a404.p.ssafy.io',
        ),
        DeclareLaunchArgument('upload_access_token', default_value=''),
        DeclareLaunchArgument('obstacle_roi_left_ratio', default_value='0.40'),
        DeclareLaunchArgument('obstacle_roi_top_ratio', default_value='0.05'),
        DeclareLaunchArgument('obstacle_roi_right_ratio', default_value='0.60'),
        DeclareLaunchArgument('obstacle_roi_bottom_ratio', default_value='0.70'),
        DeclareLaunchArgument('obstacle_publish_annotated', default_value='false'),
        DeclareLaunchArgument('obstacle_min_ground_y_ratio', default_value='0.0'),
        DeclareLaunchArgument('obstacle_min_box_height_ratio', default_value='0.0'),

        # Tactile camera/tracing, motor, and main controller.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(control_share, 'launch', 'bringup_teleop.launch.py')
            ),
            launch_arguments={
                'obstacle_stop_topic': '/emergency_stop',
                'enable_lidar': 'false',
                'shutdown_on_main_exit': 'true',
                'enable_drive_recording': enable_drive_recording,
                'recording_image_topic': recording_image_topic,
                'recording_output_path': recording_output_path,
                'start_damage_detection': start_damage_detection,
                'damage_model_path': damage_model_path,
                'damage_process_every_n_frames': damage_process_every_n_frames,
                'start_line_tracking': start_line_tracking,
                'start_drive': start_drive,
            }.items(),
        ),

        Node(
            package='hardware',
            executable='obstacle_camera_node',
            name='obstacle_camera_node',
            output='screen',
            parameters=[{
                'device_path': camera_device_path,
                'width': 1280,
                'height': 720,
                'fps': 30,
                'publish_rate': 30.0,
                'topic': '/camera/obstacle/image_raw',
            }],
        ),
        Node(
            package='perception',
            executable='obstacle_detection_node',
            name='obstacle_detection_node',
            output='screen',
            parameters=[{
                'model_path': model_path,
                'image_topic': '/camera/obstacle/image_raw',
                'detected_topic': '/obstacle/human_lower_limb_detected',
                'annotated_topic': '/obstacle/lower_limb_annotated',
                'roi_left_ratio': obstacle_roi_left_ratio,
                'roi_top_ratio': obstacle_roi_top_ratio,
                'roi_right_ratio': obstacle_roi_right_ratio,
                'roi_bottom_ratio': obstacle_roi_bottom_ratio,
                'publish_annotated': obstacle_publish_annotated,
                'min_ground_y_ratio': obstacle_min_ground_y_ratio,
                'min_box_height_ratio': obstacle_min_box_height_ratio,
            }],
        ),
        Node(
            package='hardware',
            executable='obstacle_camera_capture_viewer',
            name='obstacle_detection_viewer',
            output='screen',
            parameters=[{
                'topic': '/obstacle/lower_limb_annotated',
                'output_dir': '~/roady_dataset/obstacle_lower_limb',
            }],
        ),
        Node(
            package='ydlidar_ros2_driver',
            executable='ydlidar_ros2_driver_node',
            name='ydlidar_ros2_driver_node',
            condition=IfCondition(enable_lidar),
            output='screen',
            emulate_tty=True,
            parameters=[lidar_params],
        ),
        Node(
            package='control',
            executable='lidar_warning_node',
            name='lidar_warning_node',
            condition=IfCondition(enable_lidar),
            output='screen',
            parameters=[{
                'scan_topic': '/scan',
                'warning_topic': '/obstacle/lidar_detected',
                'min_detection_distance': 0.20,
                'max_detection_distance': 0.50,
                'front_exclusion_angle_deg': 90.0,
            }],
        ),
        Node(
            package='perception',
            executable='safety_fusion_node',
            name='safety_fusion_node',
            output='screen',
            parameters=[{
                'camera_detection_topic': '/obstacle/human_lower_limb_detected',
                'lidar_detection_topic': '/obstacle/lidar_detected',
                'stop_topic': '/emergency_stop',
                'stop_on_camera_timeout': True,
                'camera_startup_grace_sec': 5.0,
            }],
        ),
        Node(
            package='communication',
            executable='image_upload_node',
            name='image_upload_node',
            condition=IfCondition(start_image_upload),
            output='screen',
            parameters=[{
                'arrival_topic': '/driving/finished',
                'upload_enabled': ParameterValue(upload_enabled, value_type=bool),
                'base_url': upload_base_url,
                'access_token': upload_access_token,
                'storage_dir': 'data/damage_events',
            }],
        ),
    ])
