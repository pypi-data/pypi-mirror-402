from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, Dict, Optional


class BaseCandleProcessorProtocol(Protocol):
    """Protocol for BaseCandleProcessor functionality."""

    # Properties from concrete implementation
    previous_close: Optional[float]
    previous_open: Optional[float]
    previous_high: Optional[float]
    previous_low: Optional[float]

    # Abstract methods from concrete implementation
    @abstractmethod
    async def process_candle(
        self,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: int,
    ) -> Dict[str, float]: ...

    @abstractmethod
    async def process_new_candle(self, ltp: float, volume: int) -> Dict[str, float]: ...

    @abstractmethod
    async def process_existing_candle(
        self,
        current_open: float,
        current_high: float,
        current_low: float,
        current_close: float,
        ltp: float,
        volume: int,
    ) -> Dict[str, float]: ...


class RegularCandleProcessorProtocol(BaseCandleProcessorProtocol, Protocol):
    """Protocol for RegularCandleProcessor functionality."""

    pass  # Inherits all methods from BaseCandleProcessorProtocol


class HeikenAshiCandleProcessorProtocol(BaseCandleProcessorProtocol, Protocol):
    """Protocol for HeikenAshiCandleProcessor functionality."""

    pass  # Inherits all methods from BaseCandleProcessorProtocol


class RenkoCandleProcessorProtocol(BaseCandleProcessorProtocol, Protocol):
    """Protocol for RenkoCandleProcessor functionality."""

    # Additional properties specific to RenkoCandleProcessor
    brick_size: float
    current_brick_open: Optional[float]
    current_brick_close: Optional[float]
    brick_direction: Optional[str]  # "up" or "down"
