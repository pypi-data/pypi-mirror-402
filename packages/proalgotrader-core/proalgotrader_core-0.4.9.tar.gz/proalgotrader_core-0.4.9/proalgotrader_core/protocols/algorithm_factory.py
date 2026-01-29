from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Any, Dict
from asyncio import AbstractEventLoop

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
    from proalgotrader_core.protocols.api import ApiProtocol
    from proalgotrader_core.protocols.notification_manager import (
        NotificationManagerProtocol,
    )
    from proalgotrader_core.protocols.chart_manager import ChartManagerProtocol
    from proalgotrader_core.protocols.broker import BrokerProtocol


class AlgorithmFactoryProtocol(Protocol):
    """Protocol for AlgorithmFactory functionality."""

    # Properties from concrete implementation
    event_loop: AbstractEventLoop
    strategy_class: type["AlgorithmProtocol"]

    # Public methods from concrete implementation
    def get_notification_manager(
        self, algo_session: "AlgoSessionProtocol"
    ) -> "NotificationManagerProtocol": ...

    def get_chart_manager(
        self, algorithm: "AlgorithmProtocol"
    ) -> "ChartManagerProtocol": ...

    def get_order_broker_manager(
        self,
        algorithm: "AlgorithmProtocol",
        api: "ApiProtocol",
        algo_session: "AlgoSessionProtocol",
        notification_manager: "NotificationManagerProtocol",
    ) -> "BrokerProtocol": ...

    def get_algo_session(
        self, algo_session_info: Dict[str, Any]
    ) -> "AlgoSessionProtocol": ...

    async def create_algorithm_with_session(self) -> "AlgorithmProtocol": ...
