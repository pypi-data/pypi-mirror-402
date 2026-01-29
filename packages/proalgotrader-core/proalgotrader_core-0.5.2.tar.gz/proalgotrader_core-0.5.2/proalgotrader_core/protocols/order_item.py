from __future__ import annotations

from typing import Protocol, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
    from proalgotrader_core.enums.market_type import MarketType
    from proalgotrader_core.enums.order_type import OrderType
    from proalgotrader_core.enums.position_type import PositionType
    from proalgotrader_core.enums.product_type import ProductType


class OrderItemProtocol(Protocol):
    """Protocol for OrderItem functionality."""

    # Properties from concrete implementation
    broker_symbol: "BrokerSymbolProtocol"
    market_type: str
    product_type: str
    order_type: str
    position_type: str
    quantities: int
    limit_price: Optional[float]

    # Methods from concrete implementation
    def __init__(
        self,
        broker_symbol: "BrokerSymbolProtocol",
        market_type: "MarketType | str",
        product_type: "ProductType | str",
        order_type: "OrderType | str",
        position_type: "PositionType | str",
        quantities: int,
        limit_price: Optional[float] = None,
    ) -> None: ...

    async def validate(self, algorithm: "AlgorithmProtocol | None" = None) -> None: ...
