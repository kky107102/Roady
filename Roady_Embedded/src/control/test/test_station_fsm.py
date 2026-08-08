from collections import deque

import pytest

from control.main_control_node import MainControlNode


class Message:
    def __init__(self, data):
        self.data = data


class LoggerStub:
    def info(self, message):
        pass


def make_controller():
    controller = MainControlNode.__new__(MainControlNode)
    controller.tracking_state = 'STATION'
    controller.maneuver_phase = 'STATION_CALIBRATE'
    controller.station_target_samples = 5
    controller.station_target_history = deque(maxlen=5)
    controller.station_target_x = None
    controller.station_rightmost_x = None
    controller.station_steering_kp = 0.004
    controller.steering_sign = -1.0
    controller.max_steer = 0.75
    controller.station_end_navy_pixels = 1000
    controller.station_end_confirm_frames = 30
    controller.station_end_count = 0
    controller.finished_reason = None
    controller.get_logger = lambda: LoggerStub()
    controller._finish_driving = lambda reason: setattr(
        controller, 'finished_reason', reason
    )
    return controller


def test_station_target_is_average_of_five_rightmost_samples():
    controller = make_controller()

    for value in (700.0, 710.0, 720.0, 730.0, 740.0):
        controller.station_rightmost_callback(Message(value))

    assert controller.station_target_x == 720.0
    assert controller.maneuver_phase == 'STATION_APPROACH'


def test_station_steering_is_proportional_and_limited():
    controller = make_controller()
    controller.station_target_x = 700.0
    controller.station_rightmost_x = 650.0

    assert controller.calculate_station_steering() == pytest.approx(0.2)

    controller.station_rightmost_x = 1000.0
    assert controller.calculate_station_steering() == -0.75


def test_thirty_low_navy_frames_finish_station_return():
    controller = make_controller()
    controller.maneuver_phase = 'STATION_APPROACH'

    for _ in range(30):
        controller.full_frame_navy_count_callback(Message(900))

    assert controller.station_end_count == 30
    assert controller.finished_reason is not None
