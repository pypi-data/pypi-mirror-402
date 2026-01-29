from __future__ import annotations

from typing import Protocol, TYPE_CHECKING, runtime_checkable


if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


@runtime_checkable
class PositionManagerProtocol(Protocol):
    """Protocol for PositionManager functionality."""

    # Methods from concrete implementation
    def __init__(self, algorithm: "AlgorithmProtocol") -> None: ...

    async def initialize(self) -> None: ...

    async def next(self) -> None: ...
