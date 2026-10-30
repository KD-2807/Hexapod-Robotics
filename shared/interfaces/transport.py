"""Lớp trừu tượng cho kênh truyền dữ liệu dạng dòng (TCP, Serial...)."""
from abc import ABC, abstractmethod
from typing import Optional


class Transport(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Mở kết nối. Ném OSError nếu thất bại."""

    @abstractmethod
    def send_line(self, line: str) -> None:
        """Gửi một dòng (tự thêm '\\n')."""

    @abstractmethod
    def receive_line(self, timeout: float):
        """Nhận một dòng; None nếu hết thời gian chờ. Ném ConnectionError khi mất kết nối."""

    @abstractmethod
    def close(self) -> None:
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        ...
