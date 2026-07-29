from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass(frozen=True)
class CameraConfig:
    name: str = "wide_camera"
    device_index: int = 0
    backend: str = "v4l2"
    pixel_format: Optional[str] = "MJPG"
    width: Optional[int] = 1280
    height: Optional[int] = 720
    fps: Optional[int] = 30
    reconnect_delay_sec: float = 1.0


@dataclass(frozen=True)
class CameraFrame:
    camera_name: str
    frame_id: int
    timestamp: float
    image: np.ndarray


class CameraWorker:
    """Continuously reads frames and exposes the latest frame safely."""

    def __init__(self, config: CameraConfig):
        self.config = config
        self._capture: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[CameraFrame] = None
        self._frame_id = 0
        self._running = threading.Event()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._last_error: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._running.set()
        self._thread = threading.Thread(
            target=self._capture_loop,
            name=f"CameraWorker-{self.config.name}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._release_capture()

    def read_latest(self, copy: bool = True) -> Optional[CameraFrame]:
        with self._lock:
            frame = self._latest_frame
            if frame is None:
                return None
            if not copy:
                return frame
            return CameraFrame(
                camera_name=frame.camera_name,
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                image=frame.image.copy(),
            )

    def _resolve_backend(self) -> int:
        backend = self.config.backend.lower()
        if backend == "v4l2":
            return cv2.CAP_V4L2
        if backend == "gstreamer":
            return cv2.CAP_GSTREAMER
        if backend == "auto":
            return cv2.CAP_ANY
        raise ValueError(f"Unsupported camera backend: {self.config.backend}")

    def _build_gstreamer_pipeline(self) -> str:
        device = f"/dev/video{self.config.device_index}"
        width = self.config.width or 1280
        height = self.config.height or 720
        fps = self.config.fps or 30

        if (self.config.pixel_format or "").upper() == "MJPG":
            return (
                f"v4l2src device={device} ! "
                f"image/jpeg,width={width},height={height},framerate={fps}/1 ! "
                "jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink drop=true sync=false"
            )

        return (
            f"v4l2src device={device} ! "
            f"video/x-raw,width={width},height={height},framerate={fps}/1 ! "
            "videoconvert ! video/x-raw,format=BGR ! appsink drop=true sync=false"
        )

    def _open_capture(self) -> bool:
        self._release_capture()
        backend = self._resolve_backend()
        if backend == cv2.CAP_GSTREAMER:
            capture = cv2.VideoCapture(self._build_gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        else:
            capture = cv2.VideoCapture(self.config.device_index, backend)

        if not capture.isOpened() and backend not in (cv2.CAP_ANY, cv2.CAP_GSTREAMER):
            capture.release()
            capture = cv2.VideoCapture(self.config.device_index, cv2.CAP_ANY)

        if self.config.pixel_format:
            fourcc = cv2.VideoWriter_fourcc(*self.config.pixel_format)
            capture.set(cv2.CAP_PROP_FOURCC, fourcc)

        if self.config.width:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        if self.config.height:
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        if self.config.fps:
            capture.set(cv2.CAP_PROP_FPS, self.config.fps)

        if not capture.isOpened():
            self._last_error = f"Failed to open camera index: {self.config.device_index}"
            capture.release()
            return False

        self._capture = capture
        self._last_error = None
        return True

    def _release_capture(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _capture_loop(self) -> None:
        while self._running.is_set():
            if self._capture is None and not self._open_capture():
                time.sleep(self.config.reconnect_delay_sec)
                continue

            assert self._capture is not None
            ok, image = self._capture.read()
            if not ok or image is None:
                self._last_error = "Failed to read frame; reconnecting"
                self._release_capture()
                time.sleep(self.config.reconnect_delay_sec)
                continue

            self._frame_id += 1
            frame = CameraFrame(
                camera_name=self.config.name,
                frame_id=self._frame_id,
                timestamp=time.time(),
                image=image,
            )
            with self._lock:
                self._latest_frame = frame

        self._release_capture()
