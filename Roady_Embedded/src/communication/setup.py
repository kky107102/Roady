from setuptools import find_packages, setup

package_name = "communication"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools", "requests"],
    zip_safe=True,
    maintainer="Roady Team",
    maintainer_email="todo@example.com",
    description="Network clients and bridge nodes for Roady.",
    license="TODO",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "image_upload_node = communication.nodes.image_upload_node:main",
        ],
    },
)
