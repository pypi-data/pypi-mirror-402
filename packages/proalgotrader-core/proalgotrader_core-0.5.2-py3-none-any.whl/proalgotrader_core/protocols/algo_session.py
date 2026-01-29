from __future__ import annotations

from typing import Protocol, Literal, Dict, Any
from datetime import datetime, date, time

from proalgotrader_core.protocols.project import ProjectProtocol


class AlgoSessionProtocol(Protocol):
    """Protocol for AlgoSession functionality."""

    id: int
    key: str
    secret: str
    mode: Literal["Paper", "Live"]
    tz: str
    initial_capital: float
    current_capital: float
    market_start_time: time
    market_end_time: time
    market_start_datetime: datetime
    market_end_datetime: datetime
    pre_market_time: datetime

    # Additional properties from concrete implementation
    algo_session_info: Dict[str, Any]
    broker_token_info: Dict[str, Any]
    reverb_info: Dict[str, Any]
    project_info: Dict[str, Any]
    project: ProjectProtocol
    tz_info: Any  # pytz timezone

    @property
    def current_datetime(self) -> datetime: ...

    @property
    def current_timestamp(self) -> int: ...

    @property
    def current_date(self) -> date: ...

    @property
    def current_time(self) -> time: ...
