import time

import numpy as np
from sensor_msgs.msg import Image

from control.tactile_tracer_node import TactileTracerNode


def test_bgr_debug_frame_keeps_source_header_and_shape():
    source = Image()
    source.header.frame_id = 'tactile_camera'
    source.header.stamp.sec = 12
    frame = np.arange(4 * 6 * 3, dtype=np.uint8).reshape(4, 6, 3)

    output = TactileTracerNode.bgr_to_image_message(frame, source)

    assert output.header.frame_id == 'tactile_camera'
    assert output.header.stamp.sec == 12
    assert output.height == 4
    assert output.width == 6
    assert output.encoding == 'bgr8'
    assert output.step == 18
    assert bytes(output.data) == frame.tobytes()


def test_damage_annotation_draws_only_red_damage_box_on_source_frame():
    tracer = TactileTracerNode.__new__(TactileTracerNode)
    tracer.damage_overlay_timeout_sec = 0.3
    tracer.last_damage_detection_time = time.monotonic()
    tracer.latest_damage_detections = [
        {'xyxy': [10, 10, 30, 30], 'confidence': 0.8}
    ]
    frame = np.zeros((60, 80, 3), dtype=np.uint8)

    tracer.draw_damage_overlay(frame)

    assert np.array_equal(frame[10, 10], [0, 0, 255])
    assert np.array_equal(frame[50, 70], [0, 0, 0])
