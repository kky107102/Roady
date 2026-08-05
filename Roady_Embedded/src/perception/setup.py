from setuptools import find_packages, setup

package_name = "perception"

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
    description="Perception algorithms and ROS2 nodes for Roady.",
    license="TODO",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "damage_detection_node = perception.nodes.damage_detection_node:main",
            "mock_damage_detection_node = perception.nodes.mock_damage_detection_node:main",
            "visualize_mock_damage = perception.tools.visualize_mock_damage:main",
            "person_damage_pipeline_test_node = perception.nodes.person_damage_pipeline_test_node:main",
            "obstacle_detection_node = perception.nodes.obstacle_detection_node:main",
            "safety_fusion_node = perception.nodes.safety_fusion_node:main",
        ],
    },
)
