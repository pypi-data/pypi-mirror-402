from __future__ import annotations

from typing import Protocol, Any, Dict, TYPE_CHECKING
from datetime import datetime

from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


class TradeProtocol(Protocol):
    """Protocol for Trade functionality."""

    # Properties from concrete implementation
    trade_info: Dict[str, Any]
    broker_symbol: BrokerSymbolProtocol
    algorithm: "AlgorithmProtocol"
    id: int
    trade_id: str
    position_type: str
    order_type: str
    product_type: str
    market_type: str
    net_quantities: int
    buy_price: float | None
    buy_value: float | None
    sell_price: float | None
    sell_value: float | None
    created_at: datetime
    updated_at: datetime

    # Methods from concrete implementation
    def __init__(
        self,
        trade_info: Dict[str, Any],
        broker_symbol: BrokerSymbolProtocol,
        algorithm: "AlgorithmProtocol",
    ) -> None: ...

    async def initialize(self) -> None: ...

    def update_from_dict(self, data: Dict[str, Any]) -> None: ...
