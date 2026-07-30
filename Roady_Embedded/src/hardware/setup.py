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
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "obstacle_camera_node = hardware.nodes.obstacle_camera_node:main",
            "wide_camera_node = hardware.nodes.camera_node:main",
        ],
    },
)
