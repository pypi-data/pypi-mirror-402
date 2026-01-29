from __future__ import annotations

from typing import Protocol, TYPE_CHECKING, runtime_checkable

from proalgotrader_core.protocols.position import PositionProtocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


@runtime_checkable
class MultiplePositionManagerProtocol(Protocol):
    """Protocol for Multiple PositionManager functionality."""

    # Methods from concrete implementation
    def __init__(
        self, algorithm: "AlgorithmProtocol", position: PositionProtocol
    ) -> None: ...

    async def initialize(self) -> None: ...

    async def next(self) -> None: ...
