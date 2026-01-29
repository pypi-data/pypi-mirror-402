from datetime import datetime
from typing import Literal, Any, Dict


from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol


class Order:
    def __init__(
        self,
        order_info: Dict[str, Any],
        broker_symbol: BrokerSymbolProtocol,
        algorithm: AlgorithmProtocol,
    ):
        self.id: int = order_info["id"]
        self.order_id: str = order_info["order_id"]
        self.position_type: str = order_info["position_type"]
        self.order_type: str = order_info["order_type"]
        self.product_type: str = order_info["product_type"]
        self.market_type: str = order_info["market_type"]
        self.quantities: int = order_info["quantities"]
        self.disclosed_quantities: int = order_info["disclosed_quantities"]
        self.price: float = order_info["price"]
        self.limit_price: float = order_info["limit_price"]
        self.stoploss_price: float = order_info["stoploss_price"]
        self.target_price: float = order_info["target_price"]
        self.trigger_price: float = order_info.get("trigger_price", 0.0)
        self.risk_reward: Dict[str, Any] | None = order_info.get("risk_reward")
        self.status: Literal["pending", "completed", "rejected", "failed"] = order_info[
            "status"
        ]
        self.created_at: datetime = order_info["created_at"]
        self.updated_at: datetime = order_info["updated_at"]

        self.broker_symbol: BrokerSymbolProtocol = broker_symbol

    async def initialize(self) -> None:
        pass

    async def next(self) -> None:
        pass

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update order properties from dictionary data."""
        self.price = data.get("price", self.price)
        self.limit_price = data.get("limit_price", self.limit_price)
        self.stoploss_price = data.get("stoploss_price", self.stoploss_price)
        self.target_price = data.get("target_price", self.target_price)
        self.trigger_price = data.get("trigger_price", self.trigger_price)
        self.status = data.get("status", self.status)
        self.updated_at = data.get("updated_at", self.updated_at)
