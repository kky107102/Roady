from setuptools import find_packages, setup

package_name = "hardware"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Roady Team",
    maintainer_email="todo@example.com",
    description="Hardware device interfaces and ROS2 nodes for Roady.",
    license="TODO",
    entry_points={
        "console_scripts": [
            "obstacle_camera_node = hardware.nodes.obstacle_camera_node:main",
            "obstacle_camera_capture_viewer = hardware.nodes.obstacle_camera_capture_viewer:main",
            "wide_camera_node = hardware.nodes.camera_node:main",
            "wide_camera_capture_viewer = hardware.nodes.wide_camera_capture_viewer:main",
            "dot_matrix_node = hardware.nodes.dot_matrix_node:main",
            "push_lock_node = hardware.nodes.push_lock_node:main",
            "battery_led_node = hardware.nodes.battery_led_node:main",
            "gps_location_node = hardware.nodes.gps_location_node:main",
            "hall_distance_node = hardware.nodes.hall_distance_node:main",
            "test_push_lock = hardware.tools.test_push_lock:main",
            "test_dot_matrix = hardware.tools.test_dot_matrix:main",
            "test_gps = hardware.tools.test_gps:main",
            "test_hall_sensor = hardware.tools.test_hall_sensor:main",
            "measure_hall_pulses = hardware.tools.measure_hall_pulses:main",
            "test_leds = hardware.tools.test_leds:main",
        ],
    },
)
