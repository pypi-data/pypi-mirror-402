from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


class ApplicationProtocol(Protocol):
    """Protocol for Application functionality."""

    # Properties from concrete implementation
    algorithm: "AlgorithmProtocol"

    # Public methods from concrete implementation
    async def start(self) -> None: ...
