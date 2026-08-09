from __future__ import annotations

from abc import ABC, abstractmethod
import os
import subprocess
from typing import Optional


class DigitalInput(ABC):
    @abstractmethod
    def read(self) -> bool:
        """Return True for HIGH and False for LOW."""

    @abstractmethod
    def close(self) -> None:
        """Release this input."""


class DigitalOutput(ABC):
    @abstractmethod
    def write(self, value: bool) -> None:
        """Drive HIGH when true, otherwise LOW."""

    @abstractmethod
    def close(self) -> None:
        """Release this output without choosing a device-specific safe level."""


class GpioBackend(ABC):
    @abstractmethod
    def input(self, pin: int, *, pull_up: Optional[bool] = None) -> DigitalInput:
        """Open input; None means that an external pull resistor is used."""

    @abstractmethod
    def output(self, pin: int, *, initial: bool = False) -> DigitalOutput:
        """Open an output."""

    @abstractmethod
    def close(self) -> None:
        """Release all resources owned by this backend."""


class _GpioZeroInput(DigitalInput):
    def __init__(self, device) -> None:
        self._device = device
        self._closed = False

    def read(self) -> bool:
        return bool(self._device.pin.state)

    def close(self) -> None:
        if not self._closed:
            self._device.close()
            self._closed = True


class _GpioZeroOutput(DigitalOutput):
    def __init__(self, device) -> None:
        self._device = device
        self._closed = False

    def write(self, value: bool) -> None:
        self._device.value = bool(value)

    def close(self) -> None:
        if not self._closed:
            self._device.close()
            self._closed = True


class RaspberryPiGpio(GpioBackend):
    """gpiozero backend. Pin arguments use BCM numbering."""

    def __init__(self) -> None:
        try:
            from gpiozero import DigitalInputDevice, DigitalOutputDevice
        except ImportError as exc:
            raise RuntimeError(
                "gpiozero is required: sudo apt install python3-gpiozero"
            ) from exc
        self._input_type = DigitalInputDevice
        self._output_type = DigitalOutputDevice
        self._devices = []

    def input(self, pin: int, *, pull_up: Optional[bool] = None) -> DigitalInput:
        device = _GpioZeroInput(
            self._input_type(pin=pin, pull_up=pull_up)
        )
        self._devices.append(device)
        return device

    def output(self, pin: int, *, initial: bool = False) -> DigitalOutput:
        device = _GpioZeroOutput(
            self._output_type(pin=pin, active_high=True, initial_value=initial)
        )
        self._devices.append(device)
        return device

    def close(self) -> None:
        while self._devices:
            self._devices.pop().close()


class _JetsonInput(DigitalInput):
    def __init__(self, line) -> None:
        self._line, self._closed = line, False

    def read(self) -> bool:
        return bool(self._line.get_value())

    def close(self) -> None:
        if not self._closed:
            self._line.release()
            self._closed = True


class _JetsonOutput(DigitalOutput):
    def __init__(self, line) -> None:
        self._line, self._closed = line, False

    def write(self, value: bool) -> None:
        self._line.set_value(1 if value else 0)

    def close(self) -> None:
        if not self._closed:
            self._line.release()
            self._closed = True


class JetsonGpio(GpioBackend):
    """Jetson Orin gpiod backend using physical BOARD pin numbering.

    L4T r36.4.x can restore the SFIO bit while requesting a GPIO. Each line is
    therefore requested first and its PADCTL register is corrected afterwards.
    """

    _PINS = {
        7: ("PAC.06", "0x2448030"),
        15: ("PN.01", "0x2440020"),
        29: ("PQ.05", "0x2430068"),
        31: ("PQ.06", "0x2430070"),
        33: ("PH.00", "0x2434040"),
    }
    _OUTPUT_PADCTL = "0x00000004"
    _INPUT_PADCTL = "0x00000050"
    _INPUT_PULL_DOWN_PADCTL = "0x00000054"

    def __init__(self) -> None:
        try:
            import gpiod
        except ImportError as exc:
            raise RuntimeError(
                "gpiod is required: sudo apt install python3-libgpiod"
            ) from exc
        if os.geteuid() != 0:
            raise RuntimeError("Jetson GPIO PADCTL 설정을 위해 sudo로 실행하세요")
        self._gpiod = gpiod
        self._devices = []

    def input(self, pin: int, *, pull_up: Optional[bool] = None) -> DigitalInput:
        if pull_up is True:
            raise ValueError("Jetson 입력은 검증된 외부 pull-up 배선을 사용하세요")
        line = self._request_line(pin, self._gpiod.LINE_REQ_DIR_IN, "ROADY_INPUT")
        value = self._INPUT_PULL_DOWN_PADCTL if pull_up is False else self._INPUT_PADCTL
        try:
            self._configure_padctl(pin, value)
        except Exception:
            line.release()
            raise
        device = _JetsonInput(line)
        self._devices.append(device)
        return device

    def output(self, pin: int, *, initial: bool = False) -> DigitalOutput:
        line = self._request_line(pin, self._gpiod.LINE_REQ_DIR_OUT, "ROADY_OUTPUT")
        try:
            self._configure_padctl(pin, self._OUTPUT_PADCTL)
        except Exception:
            line.release()
            raise
        device = _JetsonOutput(line)
        device.write(initial)
        self._devices.append(device)
        return device

    def close(self) -> None:
        while self._devices:
            self._devices.pop().close()

    def _request_line(self, pin: int, request_type: int, consumer: str):
        line_name, _ = self._pin_info(pin)
        line = self._gpiod.find_line(line_name)
        if line is None:
            raise RuntimeError(f"GPIO 라인을 찾을 수 없습니다: {line_name}")
        line.request(consumer=consumer, type=request_type)
        return line

    def _configure_padctl(self, pin: int, value: str) -> None:
        line_name, address = self._pin_info(pin)
        subprocess.run(["busybox", "devmem", address, "w", value], check=True)
        result = subprocess.run(
            ["busybox", "devmem", address], check=True, capture_output=True, text=True
        )
        actual = result.stdout.strip()
        if actual.lower() != value.lower():
            raise RuntimeError(
                f"{line_name} PADCTL 설정 실패: expected={value}, actual={actual}"
            )
        print(f"{line_name} PADCTL={actual}")

    def _pin_info(self, pin: int) -> tuple[str, str]:
        try:
            return self._PINS[pin]
        except KeyError as exc:
            supported = ", ".join(str(value) for value in sorted(self._PINS))
            raise ValueError(
                f"지원하지 않는 Jetson BOARD pin {pin}; 사용 가능: {supported}"
            ) from exc


def create_gpio_backend(platform: str) -> GpioBackend:
    normalized = platform.strip().lower().replace("-", "_")
    if normalized in {"raspberry_pi", "raspberrypi", "rpi"}:
        return RaspberryPiGpio()
    if normalized in {"jetson", "nvidia_jetson"}:
        return JetsonGpio()
    raise ValueError("platform must be 'raspberry_pi' or 'jetson'")
