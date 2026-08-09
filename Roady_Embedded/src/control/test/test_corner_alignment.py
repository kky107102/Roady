from control.main_control_node import MainControlNode


class Message:
    def __init__(self, data):
        self.data = data


class LoggerStub:
    def info(self, message):
        pass


def make_controller():
    controller = MainControlNode.__new__(MainControlNode)
    controller.corner_target_edge_x_px = 750.0
    controller.corner_align_kp = 0.004
    controller.steering_sign = -1.0
    controller.max_steer = 0.75
    return controller


def test_corner_steering_is_proportional_to_pixel_error():
    controller = make_controller()

    small = controller.calculate_corner_alignment_steering(700.0)
    large = controller.calculate_corner_alignment_steering(650.0)

    assert small == 0.2
    assert large == 0.4


def test_corner_steering_changes_direction_across_target():
    controller = make_controller()

    left = controller.calculate_corner_alignment_steering(650.0)
    right = controller.calculate_corner_alignment_steering(850.0)

    assert left == -right


def test_corner_steering_is_limited_to_maximum():
    controller = make_controller()

    assert controller.calculate_corner_alignment_steering(0.0) == 0.75
    assert controller.calculate_corner_alignment_steering(1500.0) == -0.75


def test_aligned_corner_transitions_directly_to_unknown():
    controller = make_controller()
    controller.tracking_state = 'CORNER_LEFT'
    controller.maneuver_phase = 'CORNER_FORWARD'
    controller.corner_align_tolerance_px = 30.0
    controller.get_logger = lambda: LoggerStub()
    controller._set_tracking_state = lambda state: setattr(
        controller, 'tracking_state', state
    )

    controller.leftmost_callback(Message(750.0))

    assert controller.tracking_state == 'UNKNOWN'
