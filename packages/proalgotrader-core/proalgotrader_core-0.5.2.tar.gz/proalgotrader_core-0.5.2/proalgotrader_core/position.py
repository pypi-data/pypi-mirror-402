from logzero import logger
from datetime import datetime
from typing import Any, Dict

from proalgotrader_core.order_item import OrderItem
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol
from proalgotrader_core.protocols.pnl_calculator import PnlCalculatorProtocol
from proalgotrader_core.enums.position_type import PositionType
from proalgotrader_core.pnl_calculator import PnlCalculator
from proalgotrader_core.risk_reward_manager import RiskRewardManager


class Position:
    def __init__(
        self,
        position_info: Dict[str, Any],
        broker_symbol: BrokerSymbolProtocol,
        algorithm: AlgorithmProtocol,
    ) -> None:
        self.position_info = position_info
        self.broker_symbol: BrokerSymbolProtocol = broker_symbol
        self.algorithm: AlgorithmProtocol = algorithm

        self.id: int = position_info["id"]
        self.position_id: str = position_info["position_id"]
        self.position_type: str = position_info["position_type"]
        self.order_type: str = position_info["order_type"]
        self.product_type: str = position_info["product_type"]
        self.market_type: str = position_info["market_type"]

        self.net_quantities: int = position_info["net_quantities"]
        self.net_price: float | None = position_info["net_price"]
        self.net_value: float | None = position_info["net_value"]

        self.risk_reward: Dict[str, Any] = position_info["risk_reward"]
        self.created_at: datetime = position_info["created_at"]
        self.updated_at: datetime = position_info["updated_at"]

        self.pnl: PnlCalculatorProtocol = PnlCalculator([self])
        self.position_manager = self.algorithm.get_position_manager(position=self)
        self.risk_reward_manager = self.__get_risk_reward_manager(self.risk_reward)

    @property
    def is_buy(self) -> bool:
        return self.position_type == PositionType.BUY.value

    @property
    def is_sell(self) -> bool:
        return self.position_type == PositionType.SELL.value

    async def initialize(self) -> None:
        if self.position_manager:
            await self.position_manager.initialize()

    async def next(self) -> None:
        if self.risk_reward_manager:
            await self.risk_reward_manager.monitor()

    def __get_risk_reward_manager(self, risk_reward: Dict[str, Any]):
        if not risk_reward:
            return None

        # Extract all fields from the risk reward record
        risk_reward_id = risk_reward.get("id")
        stoploss = risk_reward.get("stoploss")
        trailing_stoploss = risk_reward.get("trailing_stoploss")
        trail_stoploss_by = risk_reward.get("trail_stoploss_by")
        trail_stoploss_when = risk_reward.get("trail_stoploss_when")
        target = risk_reward.get("target")
        trailing_target = risk_reward.get("trailing_target")
        trail_target_by = risk_reward.get("trail_target_by")
        trail_target_when = risk_reward.get("trail_target_when")

        assert stoploss is not None, "Stoploss cannot be None"
        assert risk_reward_id is not None, "Risk reward ID cannot be None"

        risk_reward_manager = RiskRewardManager(
            broker=self.algorithm.order_broker_manager,
            position=self,
            risk_reward_id=risk_reward_id,
            stoploss=stoploss,
            trailing_stoploss=trailing_stoploss,
            trail_stoploss_by=trail_stoploss_by,
            trail_stoploss_when=trail_stoploss_when,
            target=target,
            trailing_target=trailing_target,
            trail_target_by=trail_target_by,
            trail_target_when=trail_target_when,
        )

        return risk_reward_manager

    async def on_after_market_closed(self) -> None:
        await self.algorithm.on_market_closed()

    async def exit(self, quantities: int | None = None) -> None:
        try:
            logger.debug("exiting position")
            exit_position_type: PositionType = (
                PositionType.SELL if self.is_buy else PositionType.BUY
            )
            exit_quantities = quantities if quantities else self.net_quantities
            order_item = OrderItem(
                broker_symbol=self.broker_symbol,
                market_type=self.market_type,
                product_type=self.product_type,
                order_type=self.order_type,
                position_type=exit_position_type.value,
                quantities=exit_quantities,
            )
            await self.algorithm.create_order(order_item=order_item)
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        self.net_quantities = data.get("net_quantities", self.net_quantities)
        self.net_price = data.get("net_price", self.net_price)
        self.net_value = data.get("net_value", self.net_value)
        self.created_at = data.get("created_at", self.created_at)
        self.updated_at = data.get("updated_at", self.updated_at)
