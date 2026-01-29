from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Dict, Any, Type
from datetime import timedelta
from asyncio import AbstractEventLoop
import polars as pl

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm_factory import AlgorithmFactoryProtocol
    from proalgotrader_core.protocols.api import ApiProtocol
    from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
    from proalgotrader_core.protocols.notification_manager import (
        NotificationManagerProtocol,
    )
    from proalgotrader_core.protocols.broker import BrokerProtocol
    from proalgotrader_core.protocols.chart_manager import ChartManagerProtocol
    from proalgotrader_core.protocols.position_manager import PositionManagerProtocol
    from proalgotrader_core.protocols.multiple_position_manager import (
        MultiplePositionManagerProtocol,
    )
    from proalgotrader_core.protocols.position import PositionProtocol
    from proalgotrader_core.enums.account_type import AccountType


class BaseAlgorithmProtocol(Protocol):
    """Protocol for BaseAlgorithm functionality."""

    # Properties from concrete implementation
    algorithm_factory: "AlgorithmFactoryProtocol"
    event_loop: AbstractEventLoop
    args_manager: "ArgsManagerProtocol"
    api: "ApiProtocol"
    algo_session_info: Dict[str, Any]
    algo_session: "AlgoSessionProtocol"
    notification_manager: "NotificationManagerProtocol"
    order_broker_manager: "BrokerProtocol"
    chart_manager: "ChartManagerProtocol"
    account_type: "AccountType | Any"
    position_manager_class: (
        Type["PositionManagerProtocol"] | Type["MultiplePositionManagerProtocol"] | Any
    )
    position_manager_type: str | Any
    position_manager: "PositionManagerProtocol | MultiplePositionManagerProtocol | Any"
    interval: timedelta

    # Public methods from concrete implementation
    async def get_trading_days(self) -> pl.DataFrame: ...
    async def get_market_status(self) -> str: ...
    async def boot(self) -> None: ...
    async def run(self) -> None: ...

    # Position event methods from BaseAlgorithm
    async def on_position_open(self, position: "PositionProtocol") -> None: ...

    async def on_position_closed(self, position: "PositionProtocol") -> None: ...
