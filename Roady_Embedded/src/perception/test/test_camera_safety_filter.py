import pytest

from perception.algorithms.camera_safety_filter import CameraSafetyFilter


def make_filter(**overrides):
    parameters = {
        "vote_window": 3,
        "vote_required": 2,
        "clear_frames": 10,
        "minimum_hold_sec": 1.0,
    }
    parameters.update(overrides)
    return CameraSafetyFilter(**parameters)


def test_two_of_three_detections_engage_stop():
    safety_filter = make_filter()

    assert not safety_filter.update(True, 0.00).stop_required
    assert not safety_filter.update(False, 0.04).stop_required
    state = safety_filter.update(True, 0.08)

    assert state.stop_required
    assert state.reason == "camera_lower_limb"


def test_one_detection_in_window_does_not_engage_stop():
    safety_filter = make_filter()

    safety_filter.update(False, 0.00)
    safety_filter.update(True, 0.04)
    state = safety_filter.update(False, 0.08)

    assert not state.stop_required


def test_stop_requires_clear_frames_and_minimum_hold_time():
    safety_filter = make_filter(clear_frames=3, minimum_hold_sec=1.0)
    safety_filter.update(True, 0.00)
    safety_filter.update(True, 0.04)
    safety_filter.update(False, 0.08)

    safety_filter.update(False, 0.20)
    safety_filter.update(False, 0.30)
    state = safety_filter.update(False, 0.40)
    assert state.stop_required

    state = safety_filter.update(False, 1.10)
    assert not state.stop_required
    assert state.reason == "clear"


def test_detection_resets_consecutive_clear_count():
    safety_filter = make_filter(clear_frames=3, minimum_hold_sec=0.0)
    safety_filter.update(True, 0.00)
    safety_filter.update(True, 0.04)
    safety_filter.update(False, 0.08)
    safety_filter.update(False, 0.12)
    assert safety_filter.state.clear_count == 1

    state = safety_filter.update(True, 0.16)
    assert state.clear_count == 0
    assert state.stop_required


def test_timeout_can_warn_without_stopping():
    safety_filter = make_filter()
    safety_filter.update(False, 0.0)

    state = safety_filter.check_timeout(0.6, timeout_sec=0.5, stop_on_timeout=False)

    assert not state.camera_alive
    assert not state.stop_required


def test_timeout_can_fail_safe_to_stop():
    safety_filter = make_filter()

    state = safety_filter.check_timeout(0.6, timeout_sec=0.5, stop_on_timeout=True)

    assert not state.camera_alive
    assert state.stop_required
    assert state.reason == "camera_timeout"


@pytest.mark.parametrize(
    "arguments",
    [
        {"vote_window": 0},
        {"vote_window": 3, "vote_required": 4},
        {"clear_frames": 0},
        {"minimum_hold_sec": -1.0},
    ],
)
def test_invalid_parameters_are_rejected(arguments):
    with pytest.raises(ValueError):
        make_filter(**arguments)
