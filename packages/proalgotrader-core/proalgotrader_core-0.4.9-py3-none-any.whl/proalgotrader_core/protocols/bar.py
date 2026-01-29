from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, List, Any
from datetime import datetime

if TYPE_CHECKING:
    from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol


class BarProtocol(Protocol):
    """Protocol for Bar functionality."""

    # Properties from concrete implementation
    broker_symbol: "BrokerSymbolProtocol"
    current_timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int
    current_candle: datetime
    current_datetime: datetime

    # Public methods from concrete implementation
    def get_item(self) -> List[Any]: ...
