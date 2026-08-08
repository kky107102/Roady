import math
from types import SimpleNamespace

import pytest

from control.lidar_warning_node import LidarWarningNode


class Publisher:
    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message.data)


class Logger:
    def warn(self, *args, **kwargs):
        pass


def detect(ranges, angle_min=math.radians(-90.0), angle_increment=0.0):
    node = LidarWarningNode.__new__(LidarWarningNode)
    node.MIN_DETECTION_DISTANCE = 0.20
    node.MAX_DETECTION_DISTANCE = 0.50
    node.FRONT_EXCLUSION_HALF_ANGLE_RAD = math.radians(45.0)
    node.stop_pub = Publisher()
    node.get_logger = lambda: Logger()

    node.scan_callback(SimpleNamespace(
        ranges=ranges,
        angle_min=angle_min,
        angle_increment=angle_increment,
    ))

    return node.stop_pub.messages[-1]


@pytest.mark.parametrize('distance', [0.20, 0.35, 0.50])
def test_detects_obstacle_inside_inclusive_range(distance):
    assert detect([distance])


@pytest.mark.parametrize('distance', [0.19, 0.51, float('inf'), float('nan')])
def test_ignores_measurement_outside_detection_range(distance):
    assert not detect([distance])


def test_detects_in_range_measurement_when_closer_noise_is_also_present():
    assert detect([0.10, 0.30, 0.80])


@pytest.mark.parametrize('angle_deg', [-45.0, -20.0, 0.0, 20.0, 45.0, 360.0])
def test_ignores_obstacle_inside_front_ninety_degree_sector(angle_deg):
    assert not detect([0.30], angle_min=math.radians(angle_deg))


@pytest.mark.parametrize(
    'angle_deg',
    [-180.0, -135.0, -90.0, -45.1, 45.1, 90.0, 135.0, 180.0, 270.0],
)
def test_detects_obstacle_at_sides_and_rear(angle_deg):
    assert detect([0.30], angle_min=math.radians(angle_deg))


def test_detects_only_non_front_measurements_in_a_full_scan():
    ranges = [float('inf')] * 360
    ranges[90] = 0.30
    assert detect(
        ranges,
        angle_min=math.radians(-180.0),
        angle_increment=math.radians(1.0),
    )


def test_ignores_front_measurement_in_a_full_scan():
    ranges = [float('inf')] * 360
    ranges[180] = 0.30
    assert not detect(
        ranges,
        angle_min=math.radians(-180.0),
        angle_increment=math.radians(1.0),
    )
