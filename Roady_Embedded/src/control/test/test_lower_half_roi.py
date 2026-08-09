import cv2
import numpy as np
from collections import deque

from control.tactile_tracer_node import TactileTracerNode


def make_tracer():
    tracer = TactileTracerNode.__new__(TactileTracerNode)
    tracer.roi_top_ratio = 0.50
    tracer.target_edge_x_px = 750
    tracer.prev_bbox = None
    tracer.roi_margin = 120
    tracer.lost_recovery_active = False
    tracer.no_yellow_frames = 0
    tracer.unknown_start_time = None
    tracer.unknown_forward_duration = 4.0
    tracer.tracking_finished = False
    tracer.tracking_state = 'UNKNOWN'
    tracer.corner_history = deque(maxlen=10)
    tracer.corner_vote_required = 8
    tracer.corner_width_ratio = 0.28
    tracer.corner_solidity_max = 0.86
    tracer.corner_concavity_ratio_min = 0.018
    tracer.corner_direction_margin_ratio = 0.10
    tracer.corner_align_tolerance_ratio = 0.20
    tracer.corner_align_confirm_frames = 5
    tracer.track_reacquire_frames = 5
    tracer.track_reacquire_timeout = 4.0
    tracer.confirmed_corner_direction = None
    tracer.corner_align_count = 0
    tracer.track_reacquire_count = 0
    tracer.track_reacquire_start_time = 0.0
    return tracer


def test_yellow_pixels_in_upper_half_are_ignored():
    tracer = make_tracer()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.rectangle(frame, (100, 50), (1000, 300), (0, 255, 255), -1)

    block_type, offset, _, leftmost_x, _ = tracer.analyze_tactile_block(frame)

    assert block_type == 'UNKNOWN'
    assert offset is None
    assert leftmost_x is None


def test_yellow_block_in_lower_half_produces_offset():
    tracer = make_tracer()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.rectangle(frame, (500, 400), (700, 700), (0, 255, 255), -1)

    block_type, offset, _, leftmost_x, _ = tracer.analyze_tactile_block(frame)

    assert block_type == 'STRAIGHT'
    assert offset == -250
    assert leftmost_x == 500
