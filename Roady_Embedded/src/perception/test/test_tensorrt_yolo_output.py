import numpy as np

from perception.algorithms.tensorrt_lower_limb_detector import decode_yolo_output


def test_decodes_yolo26_end_to_end_output():
    output = np.array(
        [[[10, 20, 30, 40, 0.8, 1], [1, 2, 3, 4, 0.1, 0]]],
        dtype=np.float32,
    )
    boxes, scores, classes, already_nms = decode_yolo_output(output, 0.15, 2)
    np.testing.assert_allclose(boxes, [[10, 20, 30, 40]])
    np.testing.assert_allclose(scores, [0.8])
    np.testing.assert_array_equal(classes, [1])
    assert already_nms is True


def test_decodes_legacy_raw_output():
    output = np.array(
        [[[20], [30], [10], [12], [0.2], [0.9]]], dtype=np.float32
    )
    boxes, scores, classes, already_nms = decode_yolo_output(output, 0.15, 2)
    np.testing.assert_allclose(boxes, [[15, 24, 25, 36]])
    np.testing.assert_allclose(scores, [0.9])
    np.testing.assert_array_equal(classes, [1])
    assert already_nms is False
