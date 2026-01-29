from __future__ import annotations

from abc import abstractmethod
from typing import Any, Callable, Dict, List, Protocol, TYPE_CHECKING

from proalgotrader_core.protocols.trade import TradeProtocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.base_symbol import BaseSymbolProtocol
    from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol
    from proalgotrader_core.protocols.order import OrderProtocol
    from proalgotrader_core.protocols.position import PositionProtocol
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
    from proalgotrader_core.protocols.request_processor import RequestProcessorProtocol
    from proalgotrader_core.order_item import OrderItem


class BrokerProtocol(Protocol):
    """Protocol for Broker functionality."""

    # Properties from concrete implementation
    id: str
    broker_uid: str
    broker_title: str
    broker_name: str
    broker_config: Dict[str, Any]
    base_symbols: Dict[str, "BaseSymbolProtocol"]
    broker_symbols: Dict[Any, "BrokerSymbolProtocol"]
    initial_capital: float
    current_capital: float

    def get_symbol_subscriptions(self) -> Dict[str, Any]: ...

    def get_broker_symbol_listeners(self) -> Dict[str, List[Callable[..., Any]]]: ...

    def get_unsubscribed_symbols(self) -> List["BrokerSymbolProtocol"]: ...

    async def start_subscriptions(
        self, broker_symbols: List["BrokerSymbolProtocol"]
    ) -> None: ...

    # Properties
    @property
    def orders(self) -> List["OrderProtocol"]: ...

    @property
    def pending_orders(self) -> List["OrderProtocol"]: ...

    @property
    def positions(self) -> List["PositionProtocol"]: ...

    @property
    def trades(self) -> List["TradeProtocol"]: ...

    async def subscribe(
        self, broker_symbol: "BrokerSymbolProtocol", on_tick: Callable[..., Any]
    ) -> None: ...

    async def fetch_quotes(self, broker_symbol: "BrokerSymbolProtocol") -> None: ...

    def get_order(self, order_id: str) -> "OrderProtocol | None": ...

    def get_position(self, position_id: str) -> "PositionProtocol | None": ...

    def get_trade(self, trade_id: str) -> "TradeProtocol | None": ...

    def is_processing(self) -> bool: ...

    @property
    def request_processor(self) -> "RequestProcessorProtocol": ...

    async def initialize(self) -> None: ...

    async def start_connection(self) -> None: ...

    async def get_order_info(self, data: Dict[str, Any]) -> "OrderProtocol": ...

    async def get_position_info(self, data: Dict[str, Any]) -> "PositionProtocol": ...

    async def get_trade_info(self, data: Dict[str, Any]) -> "TradeProtocol": ...

    async def set_portfolio(self) -> None: ...

    async def set_orders(self, orders: List) -> None: ...

    async def set_positions(self, positions: List) -> None: ...

    async def set_trades(self, trades: List) -> None: ...

    async def on_after_market_closed(self) -> None: ...

    async def add_equity(
        self,
        *,
        base_symbol: "BaseSymbolProtocol",
        market_type: str,
        segment_type: str,
    ) -> Any: ...  # BrokerSymbol

    async def add_future(
        self,
        *,
        base_symbol: "BaseSymbolProtocol",
        market_type: str,
        segment_type: str,
        expiry_date: str,
    ) -> Any: ...  # BrokerSymbol

    async def add_option(
        self,
        *,
        base_symbol: "BaseSymbolProtocol",
        market_type: str,
        segment_type: str,
        expiry_date: str,
        strike_price: int,
        option_type: str,
    ) -> Any: ...  # BrokerSymbol

    async def get_symbol(
        self,
        broker_symbol_info: Dict[str, Any],
        should_refresh: bool,
    ) -> Any: ...  # BrokerSymbol

    async def get_positions(
        self,
        symbol_name: str,
        market_type: str,
        order_type: str,
        product_type: str,
        position_type: str,
    ) -> List["PositionProtocol"]: ...

    async def create_order(self, *, order_item: "OrderItem") -> None: ...

    async def create_multiple_orders(
        self, *, order_items: List["OrderItem"]
    ) -> None: ...

    async def create_risk_reward(
        self, *, position: PositionProtocol, item: Dict[str, Any]
    ) -> None: ...

    async def on_risk_reward_trail(
        self,
        *,
        risk_reward_id: str,
        position_id: str,
        price: float,
        type: str,
    ) -> None: ...

    async def on_risk_reward_hit(
        self,
        *,
        risk_reward_id: str,
        position_id: str,
        price: float,
        type: str,
    ) -> None: ...

    async def _process_order(
        self, *, data: Dict[str, Any], actions: Dict[str, Any]
    ) -> None: ...

    async def build_payload(
        self,
        algo_session: "AlgoSessionProtocol",
        payload_item: "OrderItem",
    ) -> Dict[str, Any]: ...

    async def exit_all_positions(self) -> None: ...

    async def next(self) -> None: ...

    async def set_initial_capital(self) -> None: ...

    async def set_current_capital(self) -> None: ...

    async def stop_connection(self) -> None: ...

    async def process_notifiable_actions(self) -> None: ...

    # Abstract method that must be implemented
    @abstractmethod
    async def manage_pending_limit_orders(self, order: "OrderProtocol") -> None: ...
