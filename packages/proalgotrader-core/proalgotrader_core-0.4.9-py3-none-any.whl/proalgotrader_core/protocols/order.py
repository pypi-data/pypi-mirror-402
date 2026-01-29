from __future__ import annotations

from typing import Protocol, Literal, Any, Dict, TYPE_CHECKING
from datetime import datetime

from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


class OrderProtocol(Protocol):
    id: int
    order_id: str
    position_type: str
    order_type: str
    product_type: str
    market_type: str
    quantities: int
    disclosed_quantities: int
    price: float
    limit_price: float
    stoploss_price: float
    target_price: float
    trigger_price: float
    status: Literal["pending", "completed", "rejected", "failed"]
    risk_reward: Dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    broker_symbol: BrokerSymbolProtocol

    # Methods from concrete implementation
    def __init__(
        self,
        order_info: Dict[str, Any],
        broker_symbol: BrokerSymbolProtocol,
        algorithm: "AlgorithmProtocol",
    ) -> None: ...

    async def initialize(self) -> None: ...

    async def next(self) -> None: ...

    @property
    def is_completed(self) -> bool: ...

    @property
    def is_pending(self) -> bool: ...

    def update_from_dict(self, data: Dict[str, Any]) -> None: ...
