from __future__ import annotations

from abc import abstractmethod
from datetime import date, datetime, time, timedelta
from typing import (
    Any,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    Type,
    TYPE_CHECKING,
)

from proalgotrader_core.protocols.trade import TradeProtocol
from proalgotrader_core.risk_reward import Stoploss, Target, RiskRewardUnit

if TYPE_CHECKING:
    from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol
    from proalgotrader_core.protocols.pnl_calculator import PnlCalculatorProtocol
    from proalgotrader_core.protocols.chart import ChartProtocol
    from proalgotrader_core.protocols.position import PositionProtocol
    from proalgotrader_core.protocols.position_manager import PositionManagerProtocol
    from proalgotrader_core.protocols.multiple_position_manager import (
        MultiplePositionManagerProtocol,
    )
    from proalgotrader_core.protocols.order import OrderProtocol
    from proalgotrader_core.protocols.signal_manager import SignalManagerProtocol
    from proalgotrader_core.enums.account_type import AccountType
    from proalgotrader_core.enums.candle_type import CandleType
    from proalgotrader_core.enums.market_type import MarketType
    from proalgotrader_core.enums.order_type import OrderType
    from proalgotrader_core.enums.product_type import ProductType
    from proalgotrader_core.order_item import OrderItem

# Import BaseAlgorithmProtocol at module level to avoid circular import
from proalgotrader_core.protocols.base_algorithm import BaseAlgorithmProtocol


class AlgorithmProtocol(BaseAlgorithmProtocol, Protocol):
    # Abstract methods that must be implemented
    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def next(self) -> None: ...

    # Properties from Algorithm (not in BaseAlgorithm)
    @property
    def market_start_time(self) -> time: ...

    @property
    def market_end_time(self) -> time: ...

    @property
    def market_start_datetime(self) -> datetime: ...

    @property
    def market_end_datetime(self) -> datetime: ...

    @property
    def pre_market_time(self) -> datetime: ...

    @property
    def current_datetime(self) -> datetime: ...

    @property
    def current_timestamp(self) -> int: ...

    @property
    def current_date(self) -> date: ...

    @property
    def current_time(self) -> time: ...

    @property
    def orders(self) -> List["OrderProtocol"]: ...

    @property
    def pending_orders(self) -> List["OrderProtocol"]: ...

    @property
    def positions(self) -> List["PositionProtocol"]: ...

    @property
    def trades(self) -> List["TradeProtocol"]: ...

    @property
    def net_pnl(self) -> "PnlCalculatorProtocol": ...

    @property
    def unrealized_pnl(self) -> "PnlCalculatorProtocol": ...

    # Methods from Algorithm
    def set_interval(self, interval: timedelta) -> None: ...

    def between_time(self, first: time, second: time) -> bool: ...

    async def add_signals(
        self,
        *,
        signal_manager: Optional[Type["SignalManagerProtocol"]],
        symbol_names: List[str],
    ) -> None: ...

    def set_position_manager(
        self,
        *,
        position_manager_class: (
            Type["PositionManagerProtocol | MultiplePositionManagerProtocol"] | Any
        ) = None,
    ) -> None: ...

    def get_position_manager(
        self, position: "PositionProtocol"
    ) -> "PositionManagerProtocol | MultiplePositionManagerProtocol | None": ...

    def set_account_type(self, *, account_type: "AccountType | Any") -> None: ...

    async def add_chart(
        self,
        *,
        broker_symbol: "BrokerSymbolProtocol",
        timeframe: timedelta,
        candle_type: "CandleType" = None,
        **kwargs,
    ) -> "ChartProtocol": ...

    async def add_equity(
        self,
        *,
        symbol_name: str,
    ) -> "BrokerSymbolProtocol": ...

    async def add_future(
        self,
        *,
        symbol_name: str,
        expiry_input: Tuple[Literal["Weekly", "Monthly"], int] | None = None,
    ) -> "BrokerSymbolProtocol": ...

    async def add_option(
        self,
        *,
        symbol_name: str,
        expiry_input: Tuple[Literal["Weekly", "Monthly"], int] | None = None,
        strike_price_input: int | None = None,
        option_type: Literal["CE", "PE"] | None = None,
    ) -> "BrokerSymbolProtocol": ...

    async def buy(
        self,
        *,
        broker_symbol: "BrokerSymbolProtocol",
        market_type: "MarketType",
        product_type: "ProductType",
        order_type: "OrderType",
        quantities: int,
    ) -> None: ...

    async def sell(
        self,
        *,
        broker_symbol: "BrokerSymbolProtocol",
        market_type: "MarketType",
        product_type: "ProductType",
        order_type: "OrderType",
        quantities: int,
    ) -> None: ...

    async def create_risk_reward(
        self,
        *,
        position: "PositionProtocol",
        stoploss: Stoploss | Any = None,
        target: Target | Any = None,
        unit: RiskRewardUnit,
    ) -> None: ...

    async def create_order(
        self,
        *,
        order_item: "OrderItem",
    ) -> None: ...

    async def create_multiple_orders(
        self, *, order_items: List["OrderItem"]
    ) -> None: ...

    async def exit_all_positions(self) -> None: ...
