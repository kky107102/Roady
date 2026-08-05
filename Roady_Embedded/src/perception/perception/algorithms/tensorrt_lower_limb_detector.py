from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
try:
    import tensorrt as trt
except ImportError:  # TensorRT is installed only on the Jetson target.
    trt = None


@dataclass(frozen=True)
class TensorRTDetection:
    class_id: int
    label: str
    confidence: float
    xyxy: tuple[float, float, float, float]


class _CudaRuntime:
    HOST_TO_DEVICE = 1
    DEVICE_TO_HOST = 2

    def __init__(self) -> None:
        try:
            self._lib = ctypes.CDLL("libcudart.so.12")
        except OSError as exc:
            raise RuntimeError("CUDA 12 runtime (libcudart.so.12) is required") from exc

        self._lib.cudaMalloc.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t]
        self._lib.cudaMalloc.restype = ctypes.c_int
        self._lib.cudaFree.argtypes = [ctypes.c_void_p]
        self._lib.cudaFree.restype = ctypes.c_int
        self._lib.cudaMemcpy.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_int,
        ]
        self._lib.cudaMemcpy.restype = ctypes.c_int
        self._lib.cudaMemcpyAsync.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        self._lib.cudaMemcpyAsync.restype = ctypes.c_int
        self._lib.cudaStreamCreate.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        self._lib.cudaStreamCreate.restype = ctypes.c_int
        self._lib.cudaStreamSynchronize.argtypes = [ctypes.c_void_p]
        self._lib.cudaStreamSynchronize.restype = ctypes.c_int
        self._lib.cudaStreamDestroy.argtypes = [ctypes.c_void_p]
        self._lib.cudaStreamDestroy.restype = ctypes.c_int

    @staticmethod
    def _check(code: int, operation: str) -> None:
        if code != 0:
            raise RuntimeError(f"{operation} failed with CUDA error {code}")

    def malloc(self, size: int) -> ctypes.c_void_p:
        pointer = ctypes.c_void_p()
        self._check(self._lib.cudaMalloc(ctypes.byref(pointer), size), "cudaMalloc")
        return pointer

    def free(self, pointer: ctypes.c_void_p) -> None:
        if pointer.value:
            self._check(self._lib.cudaFree(pointer), "cudaFree")

    def create_stream(self) -> ctypes.c_void_p:
        stream = ctypes.c_void_p()
        self._check(self._lib.cudaStreamCreate(ctypes.byref(stream)), "cudaStreamCreate")
        return stream

    def synchronize(self, stream: ctypes.c_void_p) -> None:
        self._check(self._lib.cudaStreamSynchronize(stream), "cudaStreamSynchronize")

    def destroy_stream(self, stream: ctypes.c_void_p) -> None:
        if stream.value:
            self._check(self._lib.cudaStreamDestroy(stream), "cudaStreamDestroy")

    def copy_to_device(
        self, destination: ctypes.c_void_p, source: np.ndarray, stream: ctypes.c_void_p
    ) -> None:
        self._check(
            self._lib.cudaMemcpyAsync(
                destination,
                ctypes.c_void_p(source.ctypes.data),
                source.nbytes,
                self.HOST_TO_DEVICE,
                stream,
            ),
            "cudaMemcpyAsync host-to-device",
        )

    def copy_to_host(
        self, destination: np.ndarray, source: ctypes.c_void_p, stream: ctypes.c_void_p
    ) -> None:
        self._check(
            self._lib.cudaMemcpyAsync(
                ctypes.c_void_p(destination.ctypes.data),
                source,
                destination.nbytes,
                self.DEVICE_TO_HOST,
                stream,
            ),
            "cudaMemcpyAsync device-to-host",
        )


class TensorRTLowerLimbDetector:
    """YOLO TensorRT runner that does not depend on PyTorch or Ultralytics."""

    CLASS_NAMES = ("foot", "lower_leg")

    def __init__(
        self,
        engine_path: str | Path,
        confidence: float = 0.25,
        iou_threshold: float = 0.45,
        class_names: Sequence[str] | None = None,
    ) -> None:
        if trt is None:
            raise RuntimeError("TensorRT Python bindings are required for .engine inference")
        path = Path(engine_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)

        self._logger = trt.Logger(trt.Logger.WARNING)
        self._runtime = trt.Runtime(self._logger)
        self._engine = self._runtime.deserialize_cuda_engine(path.read_bytes())
        if self._engine is None:
            raise RuntimeError(f"Could not deserialize TensorRT engine: {path}")
        self._context = self._engine.create_execution_context()
        if self._context is None:
            raise RuntimeError("Could not create TensorRT execution context")

        tensor_names = [
            self._engine.get_tensor_name(index)
            for index in range(self._engine.num_io_tensors)
        ]
        inputs = [
            name
            for name in tensor_names
            if self._engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT
        ]
        outputs = [
            name
            for name in tensor_names
            if self._engine.get_tensor_mode(name) == trt.TensorIOMode.OUTPUT
        ]
        if len(inputs) != 1 or len(outputs) != 1:
            raise RuntimeError(f"Expected one input and output, got {inputs=} {outputs=}")
        self._input_name = inputs[0]
        self._output_name = outputs[0]
        self._input_shape = tuple(self._engine.get_tensor_shape(self._input_name))
        self._output_shape = tuple(self._engine.get_tensor_shape(self._output_name))
        if (
            len(self._input_shape) != 4
            or self._input_shape[0] != 1
            or self._input_shape[1] != 3
            or self._input_shape[2] <= 0
            or self._input_shape[3] <= 0
        ):
            raise RuntimeError(f"Unsupported engine input shape: {self._input_shape}")

        self._input_dtype = np.dtype(trt.nptype(self._engine.get_tensor_dtype(self._input_name)))
        self._output_dtype = np.dtype(trt.nptype(self._engine.get_tensor_dtype(self._output_name)))
        self._host_output = np.empty(self._output_shape, dtype=self._output_dtype)
        self._cuda = _CudaRuntime()
        self._device_input = self._cuda.malloc(int(np.prod(self._input_shape)) * self._input_dtype.itemsize)
        self._device_output = self._cuda.malloc(self._host_output.nbytes)
        self._stream = self._cuda.create_stream()
        self._context.set_tensor_address(self._input_name, int(self._device_input.value))
        self._context.set_tensor_address(self._output_name, int(self._device_output.value))
        self._confidence = confidence
        self._iou_threshold = iou_threshold
        self._class_names = tuple(class_names or self.CLASS_NAMES)
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._cuda.synchronize(self._stream)
        self._cuda.destroy_stream(self._stream)
        self._cuda.free(self._device_output)
        self._cuda.free(self._device_input)
        self._closed = True

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def detect(self, image: np.ndarray) -> tuple[list[TensorRTDetection], None]:
        if image is None or image.size == 0:
            raise ValueError("image is empty")
        tensor, scale, pad_x, pad_y = self._preprocess(image)
        self._cuda.copy_to_device(self._device_input, tensor, self._stream)
        if not self._context.execute_async_v3(int(self._stream.value)):
            raise RuntimeError("TensorRT execute_async_v3 failed")
        self._cuda.copy_to_host(self._host_output, self._device_output, self._stream)
        self._cuda.synchronize(self._stream)
        detections = self._postprocess(
            self._host_output,
            image.shape[1],
            image.shape[0],
            scale,
            pad_x,
            pad_y,
        )
        return detections, None

    def _preprocess(self, image: np.ndarray) -> tuple[np.ndarray, float, float, float]:
        height, width = image.shape[:2]
        target_height, target_width = self._input_shape[-2:]
        scale = min(target_width / width, target_height / height)
        resized_width = round(width * scale)
        resized_height = round(height * scale)
        resized = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR)
        pad_x = (target_width - resized_width) / 2.0
        pad_y = (target_height - resized_height) / 2.0
        left = round(pad_x - 0.1)
        right = round(pad_x + 0.1)
        top = round(pad_y - 0.1)
        bottom = round(pad_y + 0.1)
        letterboxed = cv2.copyMakeBorder(
            resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )
        rgb = cv2.cvtColor(letterboxed, cv2.COLOR_BGR2RGB)
        tensor = np.ascontiguousarray(rgb.transpose(2, 0, 1)[None], dtype=self._input_dtype)
        tensor /= self._input_dtype.type(255.0)
        return tensor, scale, pad_x, pad_y

    def _postprocess(
        self,
        output: np.ndarray,
        image_width: int,
        image_height: int,
        scale: float,
        pad_x: float,
        pad_y: float,
    ) -> list[TensorRTDetection]:
        boxes_xyxy, confidences, class_ids, already_nms = decode_yolo_output(
            output, self._confidence, len(self._class_names)
        )
        if not len(boxes_xyxy):
            return []
        boxes_xyxy[:, [0, 2]] = (boxes_xyxy[:, [0, 2]] - pad_x) / scale
        boxes_xyxy[:, [1, 3]] = (boxes_xyxy[:, [1, 3]] - pad_y) / scale
        boxes_xyxy[:, [0, 2]] = boxes_xyxy[:, [0, 2]].clip(0, image_width - 1)
        boxes_xyxy[:, [1, 3]] = boxes_xyxy[:, [1, 3]].clip(0, image_height - 1)

        nms_boxes = [
            [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]
            for x1, y1, x2, y2 in boxes_xyxy
        ]
        keep = (
            np.arange(len(boxes_xyxy))
            if already_nms
            else np.asarray(
                cv2.dnn.NMSBoxes(
                    nms_boxes,
                    confidences.astype(float).tolist(),
                    self._confidence,
                    self._iou_threshold,
                )
            ).reshape(-1)
        )
        detections: list[TensorRTDetection] = []
        for index in keep:
            class_id = int(class_ids[index])
            if class_id < 0 or class_id >= len(self._class_names):
                continue
            xyxy = tuple(float(value) for value in boxes_xyxy[index])
            detections.append(
                TensorRTDetection(
                    class_id=class_id,
                    label=self._class_names[class_id],
                    confidence=float(confidences[index]),
                    xyxy=xyxy,
                )
            )
        return detections


def decode_yolo_output(
    output: np.ndarray,
    confidence_threshold: float,
    class_count: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Decode YOLO26 end-to-end rows or legacy Ultralytics raw predictions."""
    predictions = np.asarray(output)
    if predictions.ndim == 3 and predictions.shape[0] == 1:
        predictions = predictions[0]
    if predictions.ndim != 2:
        raise RuntimeError(f"Unsupported TensorRT output shape: {output.shape}")

    # YOLO26 end-to-end output: [N, 6] = xyxy, confidence, class_id.
    if predictions.shape[1] == 6 and predictions.shape[0] != 4 + class_count:
        selected = predictions[:, 4] >= confidence_threshold
        rows = predictions[selected]
        return (
            rows[:, :4].astype(np.float32, copy=True),
            rows[:, 4].astype(np.float32, copy=False),
            rows[:, 5].astype(np.int32, copy=False),
            True,
        )

    channels = 4 + class_count
    if predictions.shape[0] == channels:
        predictions = predictions.T
    elif predictions.shape[1] != channels:
        raise RuntimeError(f"Unsupported TensorRT output shape: {output.shape}")

    class_scores = predictions[:, 4:]
    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(len(predictions)), class_ids]
    selected = confidences >= confidence_threshold
    predictions = predictions[selected]
    confidences = confidences[selected]
    class_ids = class_ids[selected]
    boxes_xywh = predictions[:, :4]
    boxes_xyxy = np.empty_like(boxes_xywh, dtype=np.float32)
    boxes_xyxy[:, 0] = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2
    boxes_xyxy[:, 1] = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2
    boxes_xyxy[:, 2] = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2
    boxes_xyxy[:, 3] = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2
    return boxes_xyxy, confidences.astype(np.float32), class_ids.astype(np.int32), False
