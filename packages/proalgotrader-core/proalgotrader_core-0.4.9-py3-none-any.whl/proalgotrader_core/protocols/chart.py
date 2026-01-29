from __future__ import annotations

from typing import Protocol, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
import polars as pl

if TYPE_CHECKING:
    from proalgotrader_core.protocols.chart_manager import ChartManagerProtocol
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
    from proalgotrader_core.protocols.broker import BrokerProtocol
    from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol
    from proalgotrader_core.protocols.tick import TickProtocol
    from proalgotrader_core.enums.candle_type import CandleType
    from proalgotrader_core.indicators.indicator import Indicator


class ChartProtocol(Protocol):
    """Protocol for Chart functionality."""

    # Properties from concrete implementation
    chart_manager: "ChartManagerProtocol"
    algo_session: "AlgoSessionProtocol"
    order_broker_manager: "BrokerProtocol"
    broker_symbol: "BrokerSymbolProtocol"
    timeframe: timedelta
    candle_type: "CandleType"
    current_candle_datetime: datetime

    @property
    def next_candle_datetime(self) -> datetime: ...

    @property
    def df(self) -> pl.DataFrame: ...

    @property
    def data(self) -> pl.DataFrame: ...

    # Methods from concrete implementation
    async def get_ltp(self) -> float: ...

    async def get_data(
        self, row_number: int = 0, column_name: Optional[str] = None
    ) -> Any: ...

    async def initialize(self) -> None: ...

    async def next(self) -> None: ...

    def is_new_candle(self) -> bool: ...

    async def on_tick(self, tick: "TickProtocol") -> None: ...

    async def update_existing_candle(self, tick: "TickProtocol") -> None: ...

    async def add_new_candle(self, tick: "TickProtocol") -> None: ...

    async def update_chart(self, tick: "TickProtocol") -> None: ...

    async def update_chart_indicators(self) -> None: ...

    async def add_indicator(
        self, *, key: str, indicator: "Indicator | Any"
    ) -> "Indicator": ...
