from __future__ import annotations

from typing import Protocol, Any, Dict, TYPE_CHECKING
from datetime import datetime

from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
    from proalgotrader_core.protocols.pnl_calculator import PnlCalculatorProtocol


class PositionProtocol(Protocol):
    """Protocol for Position functionality."""

    # Properties from concrete implementation
    position_info: Dict[str, Any]
    broker_symbol: BrokerSymbolProtocol
    algorithm: "AlgorithmProtocol"
    id: int
    position_id: str
    position_type: str
    order_type: str
    product_type: str
    market_type: str
    net_quantities: int
    net_price: float
    net_value: float
    risk_reward: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    pnl: "PnlCalculatorProtocol"
    position_manager: Any
    risk_reward_manager: Any

    # Methods from concrete implementation
    def __init__(
        self,
        position_info: Dict[str, Any],
        broker_symbol: BrokerSymbolProtocol,
        algorithm: "AlgorithmProtocol",
    ) -> None: ...

    @property
    def is_buy(self) -> bool: ...

    @property
    def is_sell(self) -> bool: ...

    async def initialize(self) -> None: ...

    async def next(self) -> None: ...

    async def on_after_market_closed(self) -> None: ...

    async def exit(self, quantities: int | None = None) -> None: ...

    def update_from_dict(self, data: Dict[str, Any]) -> None: ...
