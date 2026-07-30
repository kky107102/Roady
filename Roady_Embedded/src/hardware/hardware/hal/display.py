from __future__ import annotations

from abc import ABC, abstractmethod


class DotMatrixDisplay(ABC):
    """Board-independent monochrome dot-matrix interface."""

    @property
    @abstractmethod
    def width(self) -> int:
        pass

    @property
    @abstractmethod
    def height(self) -> int:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def fill(self) -> None:
        pass

    @abstractmethod
    def vertical_line(self, x: int) -> None:
        pass

    @abstractmethod
    def horizontal_line(self, y: int) -> None:
        pass

    @abstractmethod
    def pixel(self, x: int, y: int) -> None:
        pass

    @abstractmethod
    def block_boundaries(self, block_width: int = 8) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
