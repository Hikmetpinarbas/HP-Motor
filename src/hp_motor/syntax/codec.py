from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .signal_packet import SignalPacket


@dataclass(frozen=True)
class EncodeResult:
    packets: List[SignalPacket]
    meta: Dict[str, Any]


class BaseEncoder(ABC):
    """
    Each encoder maps a specific file kind -> list[SignalPacket]
    """

    @property
    @abstractmethod
    def file_kinds(self) -> Sequence[str]:
        ...

    @abstractmethod
    def can_handle(self, filename: str) -> bool:
        ...

    @abstractmethod
    def encode_bytes(self, filename: str, data: bytes) -> EncodeResult:
        ...