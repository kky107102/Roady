from datetime import datetime

import cv2
import numpy as np

from hardware.devices.image_capture import (
    image_message_to_bgr,
    save_frame,
)


class ImageMessage:
    pass


def make_image_message(image, encoding="bgr8", padding=0):
    height, width = image.shape[:2]
    channels = 1 if image.ndim == 2 else image.shape[2]
    row_bytes = width * channels
    message = ImageMessage()
    message.height = height
    message.width = width
    message.encoding = encoding
    message.step = row_bytes + padding
    if padding:
        rows = np.zeros((height, message.step), dtype=np.uint8)
        rows[:, :row_bytes] = image.reshape(height, row_bytes)
        message.data = rows.tobytes()
    else:
        message.data = image.tobytes()
    return message


def test_image_message_to_bgr_handles_rgb_and_row_padding():
    rgb = np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8)
    converted = image_message_to_bgr(make_image_message(rgb, "rgb8", padding=4))

    assert converted.tolist() == [[[0, 0, 255], [0, 255, 0]]]


def test_save_frame_creates_output_directory_and_timestamped_jpeg(tmp_path):
    frame = np.full((12, 16, 3), 127, dtype=np.uint8)
    captured_at = datetime(2026, 8, 3, 14, 5, 6, 123456)

    output = save_frame(frame, tmp_path / "captures", captured_at=captured_at)

    assert output.name == "wide_20260803_140506_123456.jpg"
    saved = cv2.imread(str(output))
    assert saved is not None and saved.shape == frame.shape


def test_save_frame_supports_an_obstacle_filename_prefix(tmp_path):
    frame = np.zeros((8, 8, 3), dtype=np.uint8)

    output = save_frame(frame, tmp_path, filename_prefix="obstacle")

    assert output.name.startswith("obstacle_")
