from __future__ import annotations

from typing import Protocol, Dict, List, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
    from proalgotrader_core.protocols.chart import ChartProtocol
    from proalgotrader_core.protocols.broker import BrokerProtocol
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
    from proalgotrader_core.broker_symbol import BrokerSymbol
    from proalgotrader_core.enums.candle_type import CandleType


class ChartManagerProtocol(Protocol):
    """Protocol for ChartManager functionality."""

    # Properties from concrete implementation
    algorithm: "AlgorithmProtocol"
    algo_session: "AlgoSessionProtocol"
    order_broker_manager: "BrokerProtocol"
    warmup_days: Dict[timedelta, int]

    @property
    def charts(self) -> List["ChartProtocol"]: ...

    # Methods from concrete implementation
    async def get_chart(
        self, key: Tuple[int, timedelta, "CandleType"]
    ) -> "ChartProtocol | None": ...

    async def register_chart(
        self,
        broker_symbol: "BrokerSymbol",
        timeframe: timedelta,
        candle_type: "CandleType" = ...,
        **kwargs,
    ) -> "ChartProtocol": ...

    async def fetch_ranges(self, timeframe: timedelta) -> Tuple[datetime, datetime]: ...

    def get_current_candle(self, timeframe: timedelta) -> datetime: ...
