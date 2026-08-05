import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    location_mode = LaunchConfiguration("location_mode")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "location_mode",
                default_value="indoor",
                description="Location mode: indoor (Hall only) or outdoor (GPS first)",
            ),
            Node(
                package="hardware",
                executable="hall_distance_node",
                name="hall_distance",
                output="screen",
            ),
            Node(
                package="hardware",
                executable="gps_location_node",
                name="gps_location",
                output="screen",
                parameters=[{"location_mode": location_mode}],
            ),
            Node(
                package="communication",
                executable="telemetry_node",
                name="telemetry_node",
                output="screen",
                additional_env={
                    "PYTHONPATH": os.pathsep.join(
                        filter(
                            None,
                            [
                                os.environ.get("PYTHONPATH", ""),
                                "/home/ssafy/.local/lib/python3.10/site-packages",
                            ],
                        )
                    )
                },
            ),
        ]
    )
