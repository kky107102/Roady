from __future__ import annotations

import os
import select
import termios
import tty
from abc import ABC, abstractmethod


class UartPort(ABC):
    @abstractmethod
    def readline(self, timeout: float = 1.0) -> bytes:
        """Read one newline-terminated frame, or b"" on timeout."""

    @abstractmethod
    def close(self) -> None:
        pass


class LinuxUart(UartPort):
    """Dependency-free Linux UART implementation for Raspberry Pi and Jetson."""

    _BAUD_RATES = {
        4800: termios.B4800,
        9600: termios.B9600,
        19200: termios.B19200,
        38400: termios.B38400,
        57600: termios.B57600,
        115200: termios.B115200,
    }

    def __init__(self, path: str, baudrate: int) -> None:
        if baudrate not in self._BAUD_RATES:
            supported = ", ".join(str(value) for value in self._BAUD_RATES)
            raise ValueError(f"unsupported baudrate {baudrate}; use {supported}")
        try:
            self._fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        except OSError as exc:
            raise RuntimeError(f"failed to open UART {path}: {exc}") from exc
        self.path = path
        self.baudrate = baudrate
        self._buffer = bytearray()
        self._closed = False
        tty.setraw(self._fd)
        attributes = termios.tcgetattr(self._fd)
        attributes[4] = self._BAUD_RATES[baudrate]
        attributes[5] = self._BAUD_RATES[baudrate]
        termios.tcsetattr(self._fd, termios.TCSANOW, attributes)
        termios.tcflush(self._fd, termios.TCIFLUSH)

    def readline(self, timeout: float = 1.0) -> bytes:
        if self._closed:
            raise RuntimeError("UART is closed")
        newline = self._buffer.find(b"\n")
        if newline >= 0:
            return self._pop_line(newline)
        readable, _, _ = select.select([self._fd], [], [], max(timeout, 0.0))
        if not readable:
            return b""
        try:
            chunk = os.read(self._fd, 4096)
        except BlockingIOError:
            return b""
        self._buffer.extend(chunk)
        newline = self._buffer.find(b"\n")
        return self._pop_line(newline) if newline >= 0 else b""

    def close(self) -> None:
        if not self._closed:
            os.close(self._fd)
            self._closed = True

    def _pop_line(self, newline: int) -> bytes:
        line = bytes(self._buffer[: newline + 1])
        del self._buffer[: newline + 1]
        return line
