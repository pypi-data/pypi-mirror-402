from __future__ import annotations

from typing import Protocol


class BaseSymbolProtocol(Protocol):
    """Protocol for BaseSymbol functionality."""

    # Properties from concrete implementation
    id: int
    exchange: str
    key: str
    value: str
    type: str
    strike_size: int
