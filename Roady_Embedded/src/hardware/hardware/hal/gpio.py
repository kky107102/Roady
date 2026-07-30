from __future__ import annotations

from abc import ABC, abstractmethod
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
    def __init__(self, gpio, pin: int) -> None:
        self._gpio, self._pin, self._closed = gpio, pin, False

    def read(self) -> bool:
        return bool(self._gpio.input(self._pin))

    def close(self) -> None:
        if not self._closed:
            self._gpio.cleanup(self._pin)
            self._closed = True


class _JetsonOutput(DigitalOutput):
    def __init__(self, gpio, pin: int) -> None:
        self._gpio, self._pin, self._closed = gpio, pin, False

    def write(self, value: bool) -> None:
        self._gpio.output(self._pin, self._gpio.HIGH if value else self._gpio.LOW)

    def close(self) -> None:
        if not self._closed:
            self._gpio.cleanup(self._pin)
            self._closed = True


class JetsonGpio(GpioBackend):
    """Jetson.GPIO backend. Pin arguments use BOARD numbering."""

    def __init__(self) -> None:
        try:
            import Jetson.GPIO as GPIO
        except ImportError as exc:
            raise RuntimeError(
                "Jetson.GPIO is required: sudo apt install python3-jetson-gpio"
            ) from exc
        self._gpio = GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        self._devices = []

    def input(self, pin: int, *, pull_up: Optional[bool] = None) -> DigitalInput:
        if pull_up is None:
            self._gpio.setup(pin, self._gpio.IN)
        else:
            pull = self._gpio.PUD_UP if pull_up else self._gpio.PUD_DOWN
            self._gpio.setup(pin, self._gpio.IN, pull_up_down=pull)
        device = _JetsonInput(self._gpio, pin)
        self._devices.append(device)
        return device

    def output(self, pin: int, *, initial: bool = False) -> DigitalOutput:
        level = self._gpio.HIGH if initial else self._gpio.LOW
        self._gpio.setup(pin, self._gpio.OUT, initial=level)
        device = _JetsonOutput(self._gpio, pin)
        self._devices.append(device)
        return device

    def close(self) -> None:
        while self._devices:
            self._devices.pop().close()


def create_gpio_backend(platform: str) -> GpioBackend:
    normalized = platform.strip().lower().replace("-", "_")
    if normalized in {"raspberry_pi", "raspberrypi", "rpi"}:
        return RaspberryPiGpio()
    if normalized in {"jetson", "nvidia_jetson"}:
        return JetsonGpio()
    raise ValueError("platform must be 'raspberry_pi' or 'jetson'")
