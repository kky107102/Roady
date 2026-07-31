import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 🚨 Launch 파일 등록 (이 부분이 들어가야 함)
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    # ... 후략 ...
    entry_points={
        'console_scripts': [
            'motor_node = control.motor_node:main',
            'lidar_warning_node = control.lidar_warning_node:main',
            'tactile_tracer_node = control.tactile_tracer_node:main',
        ],
    },
)
