from types import SimpleNamespace

from control.main_control_node import MainControlNode


def make_controller():
    controller = MainControlNode.__new__(MainControlNode)
    controller.image_width_px = 1000
    controller.target_edge_x_px = 500
    controller.max_steer = 1.0
    controller.steering_sign = -1.0
    controller.current_state = 'TRACK_DRIVE'
    controller.current_offset = 0.0
    controller.offset_history = []
    controller.last_offset_time = 0.0
    controller.startup_complete = True
    controller.offset_recovery_latched = False
    controller.is_obstacle_detected = False
    controller.tracking_state = 'STRAIGHT'
    controller.active_forward_steer = 1.0
    controller.filtered_steering = 0.0
    controller.maneuver_start_time = 0.0
    controller.unknown_forward_speed_ratio = 1.0
    return controller


def send_offset(controller, offset):
    controller.offset_callback(SimpleNamespace(data=float(offset)))


def test_offset_at_thirty_percent_boundary_drives_straight():
    controller = make_controller()

    send_offset(controller, 300)

    assert controller.current_state == 'TRACK_DRIVE'
    assert not controller.offset_recovery_required()


def test_offset_above_positive_thirty_percent_starts_backup():
    controller = make_controller()

    send_offset(controller, 301)

    assert controller.current_state == 'OFFSET_BACKUP'
    assert controller.active_forward_steer != 0.0
    assert controller.active_reverse_steer == 0.0


def test_offset_below_negative_thirty_percent_starts_backup():
    controller = make_controller()

    send_offset(controller, -301)

    assert controller.current_state == 'OFFSET_BACKUP'
    assert controller.active_reverse_steer == 0.0


def test_negative_offset_uses_the_opposite_steering_direction():
    controller = make_controller()

    positive = controller.calculate_offset_steering(100)
    negative = controller.calculate_offset_steering(-100)

    assert positive * negative < 0.0
    assert abs(positive) == controller.max_steer
    assert abs(negative) == controller.max_steer


def test_steering_magnitude_does_not_change_with_offset_size():
    controller = make_controller()

    small = controller.calculate_offset_steering(1)
    large = controller.calculate_offset_steering(349)

    assert abs(small) == controller.max_steer
    assert abs(large) == controller.max_steer


def test_non_straight_frame_does_not_update_offset():
    controller = make_controller()
    controller.tracking_state = 'UNKNOWN'

    send_offset(controller, 500)

    assert controller.current_offset == 0.0
    assert controller.current_state == 'TRACK_DRIVE'


def test_non_straight_detection_cancels_offset_maneuver():
    controller = make_controller()
    controller.current_state = 'OFFSET_BACKUP'
    controller.filtered_steering = 0.5
    controller.offset_recovery_latched = True

    controller.tracking_state_callback(SimpleNamespace(data='UNKNOWN'))

    assert controller.current_state == 'TRACK_DRIVE'
    assert controller.filtered_steering == 0.0
    assert not controller.offset_recovery_latched
