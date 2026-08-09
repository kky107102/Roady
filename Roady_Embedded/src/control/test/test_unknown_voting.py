from collections import deque

from control.main_control_node import MainControlNode


class LoggerStub:
    def info(self, message):
        pass

    def warn(self, message):
        pass


def make_controller():
    controller = MainControlNode.__new__(MainControlNode)
    controller.tracking_state = 'UNKNOWN'
    controller.shutdown_requested = False
    controller.unknown_vote_frames = 10
    controller.unknown_max_consecutive_votes = 5
    controller.unknown_consecutive_votes = 0
    controller.unknown_frame_states = deque(maxlen=10)
    controller.finished_after_unknown_votes = False
    controller.get_logger = lambda: LoggerStub()
    controller._set_tracking_state = lambda state: setattr(
        controller, 'tracking_state', state
    )
    controller._finish_driving = lambda reason: setattr(
        controller, 'finished_after_unknown_votes', True
    )
    return controller


def send_frames(controller, states):
    for state in states:
        controller._collect_unknown_frame(state)


def test_vote_waits_for_exactly_ten_frames():
    controller = make_controller()

    send_frames(controller, ['STRAIGHT'] * 9)

    assert controller.tracking_state == 'UNKNOWN'
    assert len(controller.unknown_frame_states) == 9


def test_ten_frame_vote_transitions_to_most_frequent_known_state():
    controller = make_controller()

    send_frames(controller, ['STRAIGHT'] * 6 + ['UNKNOWN'] * 4)

    assert controller.tracking_state == 'STRAIGHT'
    assert not controller.unknown_frame_states


def test_unknown_plurality_counts_as_one_failed_vote():
    controller = make_controller()

    send_frames(
        controller,
        ['UNKNOWN'] * 5 + ['STRAIGHT'] * 3 + ['CORNER_LEFT'] * 2,
    )

    assert controller.tracking_state == 'UNKNOWN'
    assert controller.unknown_consecutive_votes == 1


def test_tied_vote_is_treated_as_unknown():
    controller = make_controller()

    send_frames(controller, ['STRAIGHT'] * 5 + ['CORNER_RIGHT'] * 5)

    assert controller.tracking_state == 'UNKNOWN'
    assert controller.unknown_consecutive_votes == 1


def test_five_consecutive_unknown_votes_finish_driving():
    controller = make_controller()

    for _ in range(5):
        send_frames(controller, ['UNKNOWN'] * 10)

    assert controller.unknown_consecutive_votes == 5
    assert controller.finished_after_unknown_votes
