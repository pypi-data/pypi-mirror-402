from datetime import datetime
from typing import Any, Dict

from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol


class Trade:
    def __init__(
        self,
        trade_info: Dict[str, Any],
        broker_symbol: BrokerSymbolProtocol,
        algorithm: AlgorithmProtocol,
    ) -> None:
        self.trade_info = trade_info
        self.broker_symbol: BrokerSymbolProtocol = broker_symbol
        self.algorithm: AlgorithmProtocol = algorithm

        self.id: int = trade_info["id"]
        self.trade_id: str = trade_info["trade_id"]
        self.position_type: str = trade_info["position_type"]
        self.order_type: str = trade_info["order_type"]
        self.product_type: str = trade_info["product_type"]
        self.market_type: str = trade_info["market_type"]

        self.net_quantities: int = trade_info["net_quantities"]
        self.buy_price: float | None = trade_info["buy_price"]
        self.buy_value: float | None = trade_info["buy_value"]
        self.sell_price: float | None = trade_info["sell_price"]
        self.sell_value: float | None = trade_info["sell_value"]

        self.created_at: datetime = trade_info["created_at"]
        self.updated_at: datetime = trade_info["updated_at"]

    async def initialize(self) -> None:
        pass

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        self.net_quantities = data.get("net_quantities", self.net_quantities)
        self.buy_price = data.get("buy_price", self.buy_price)
        self.buy_value = data.get("buy_value", self.buy_value)
        self.sell_price = data.get("sell_price", self.sell_price)
        self.sell_value = data.get("sell_value", self.sell_value)
        self.created_at = data.get("created_at", self.created_at)
        self.updated_at = data.get("updated_at", self.updated_at)
