from __future__ import annotations

from typing import Protocol, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol


class TickProtocol(Protocol):
    """Protocol for Tick functionality."""

    # Properties from concrete implementation
    broker_symbol: "BrokerSymbolProtocol"
    current_timestamp: int
    ltp: float
    total_volume: int
    current_datetime: datetime

    # Methods from concrete implementation
    def __init__(
        self,
        *,
        broker_symbol: "BrokerSymbolProtocol",
        current_timestamp: int,
        ltp: float,
        total_volume: int,
    ) -> None: ...
