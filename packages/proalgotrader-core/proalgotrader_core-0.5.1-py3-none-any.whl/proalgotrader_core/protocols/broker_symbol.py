from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.base_symbol import BaseSymbolProtocol
    from proalgotrader_core.protocols.broker import BrokerProtocol
    from proalgotrader_core.protocols.tick import TickProtocol


class BrokerSymbolProtocol(Protocol):
    """Protocol for BrokerSymbol functionality."""

    # Properties from concrete implementation
    order_broker_manager: "BrokerProtocol"
    base_symbol: "BaseSymbolProtocol"
    id: int
    market_type: str
    segment_type: str
    expiry_date: str
    strike_price: int
    option_type: str
    lot_size: int
    symbol_name: str
    symbol_token: str
    exchange_token: int
    total_volume: int
    subscribed: bool

    # Properties from concrete implementation
    @property
    def can_trade(self) -> bool: ...

    # Methods from concrete implementation
    async def get_ltp(self) -> float: ...
    async def initialize(self) -> None: ...
    async def on_bar(self, ltp: float, total_volume: int) -> None: ...
    async def on_tick(self, tick: "TickProtocol") -> None: ...
    def __str__(self) -> str: ...
