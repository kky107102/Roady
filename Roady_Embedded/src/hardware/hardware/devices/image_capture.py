from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def image_message_to_bgr(message) -> np.ndarray:
    """Convert a ROS Image-like object into a BGR image."""
    channels_by_encoding = {"bgr8": 3, "rgb8": 3, "mono8": 1}
    if message.encoding not in channels_by_encoding:
        raise ValueError(f"Unsupported image encoding: {message.encoding}")

    channels = channels_by_encoding[message.encoding]
    row_bytes = message.width * channels
    if message.step < row_bytes:
        raise ValueError(
            f"Invalid image step {message.step}; expected at least {row_bytes}"
        )

    raw = np.frombuffer(message.data, dtype=np.uint8)
    required_size = message.step * message.height
    if raw.size < required_size:
        raise ValueError(
            f"Image data is too short: {raw.size} bytes, expected {required_size}"
        )

    rows = raw[:required_size].reshape(message.height, message.step)
    pixels = rows[:, :row_bytes]
    if channels == 1:
        mono = pixels.reshape(message.height, message.width)
        return cv2.cvtColor(mono, cv2.COLOR_GRAY2BGR)

    image = pixels.reshape(message.height, message.width, channels)
    if message.encoding == "rgb8":
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image.copy()


def save_frame(
    frame: np.ndarray,
    output_dir: Path,
    jpeg_quality: int = 95,
    captured_at: Optional[datetime] = None,
    filename_prefix: str = "wide",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = (captured_at or datetime.now()).strftime("%Y%m%d_%H%M%S_%f")
    output_path = output_dir / f"{filename_prefix}_{timestamp}.jpg"
    if not cv2.imwrite(
        str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
    ):
        raise OSError(f"Failed to save image: {output_path}")
    return output_path
