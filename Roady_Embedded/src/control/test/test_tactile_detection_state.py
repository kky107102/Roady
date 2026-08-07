from collections import deque

import numpy as np

from control.tactile_tracer_node import TactileTracerNode


def make_tracer():
    tracer = TactileTracerNode.__new__(TactileTracerNode)
    tracer.no_yellow_frames = 0
    tracer.unknown_start_time = None
    tracer.unknown_forward_duration = 4.0
    tracer.lost_recovery_active = False
    tracer.tracking_finished = False
    tracer.tracking_state = 'UNKNOWN'
    tracer.corner_history = deque(maxlen=10)
    tracer.corner_vote_required = 8
    tracer.corner_align_tolerance_ratio = 0.20
    tracer.corner_align_confirm_frames = 5
    tracer.track_reacquire_frames = 5
    tracer.track_reacquire_timeout = 4.0
    tracer.confirmed_corner_direction = None
    tracer.corner_align_count = 0
    tracer.track_reacquire_count = 0
    tracer.track_reacquire_start_time = 0.0
    return tracer


def test_unknown_starts_forward_confirmation():
    tracer = make_tracer()

    tracer._update_tracking_end_state(True)

    assert tracer.no_yellow_frames == 1
    assert tracer.lost_recovery_active
    assert not tracer.tracking_finished


def test_four_seconds_of_unknown_finishes_tracking(monkeypatch):
    clock = {'now': 10.0}
    monkeypatch.setattr(
        'control.tactile_tracer_node.time.monotonic',
        lambda: clock['now'],
    )
    tracer = make_tracer()

    tracer._update_tracking_end_state(True)
    clock['now'] = 13.9
    tracer._update_tracking_end_state(True)

    assert tracer.lost_recovery_active
    assert not tracer.tracking_finished

    clock['now'] = 14.0
    tracer._update_tracking_end_state(True)

    assert not tracer.lost_recovery_active
    assert tracer.tracking_finished


def test_known_detection_cancels_unknown_confirmation():
    tracer = make_tracer()
    tracer._update_tracking_end_state(True)

    tracer._update_tracking_end_state(False)

    assert tracer.no_yellow_frames == 0
    assert not tracer.lost_recovery_active
    assert not tracer.tracking_finished


def test_initial_unknown_starts_forward_recovery():
    tracer = make_tracer()

    tracer._update_tracking_end_state(True)

    assert tracer.no_yellow_frames == 1
    assert tracer.lost_recovery_active
    assert not tracer.tracking_finished


def test_corner_requires_eight_votes_in_last_ten_frames():
    tracer = make_tracer()

    for detected in (
        'CORNER_LEFT', 'CORNER_LEFT', 'STRAIGHT', 'CORNER_LEFT',
        'CORNER_LEFT', 'CORNER_LEFT', 'STRAIGHT', 'CORNER_LEFT',
        'CORNER_LEFT',
    ):
        tracer._update_tracking_state(
            detected, np.array([500, 900]), True, 750, 1280
        )

    assert tracer.tracking_state == 'CORNER_LEFT_CANDIDATE'

    tracer._update_tracking_state(
        'CORNER_LEFT', np.array([500, 900]), True, 750, 1280
    )

    assert tracer.tracking_state == 'CORNER_LEFT'
    assert tracer.confirmed_corner_direction == 'LEFT'


def test_corner_alignment_requires_five_tolerance_frames():
    tracer = make_tracer()
    tracer.tracking_state = 'CORNER_LEFT'

    for _ in range(4):
        tracer._update_tracking_state(
            'CORNER_LEFT', np.array([500, 900]), False, 750, 1280
        )
        assert tracer.tracking_state == 'CORNER_LEFT'

    tracer._update_tracking_state(
        'CORNER_LEFT', np.array([500, 900]), False, 750, 1280
    )

    assert tracer.tracking_state == 'TRACK_REACQUIRE'


def test_track_reacquire_requires_five_bottom_frames(monkeypatch):
    monkeypatch.setattr(
        'control.tactile_tracer_node.time.monotonic', lambda: 10.0
    )
    tracer = make_tracer()
    tracer.tracking_state = 'TRACK_REACQUIRE'
    tracer.track_reacquire_start_time = 10.0

    for _ in range(4):
        tracer._update_tracking_state(
            'STRAIGHT', np.array([500]), True, 750, 1280
        )
        assert tracer.tracking_state == 'TRACK_REACQUIRE'

    tracer._update_tracking_state(
        'STRAIGHT', np.array([500]), True, 750, 1280
    )

    assert tracer.tracking_state == 'STRAIGHT'
