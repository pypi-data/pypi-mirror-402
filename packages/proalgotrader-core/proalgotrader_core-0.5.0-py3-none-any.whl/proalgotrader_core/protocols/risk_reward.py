from __future__ import annotations

from typing import Protocol, Optional, TYPE_CHECKING, Any, Dict, Callable
from proalgotrader_core.enums.risk_reward_unit import RiskRewardUnit

if TYPE_CHECKING:
    from proalgotrader_core.protocols.position import PositionProtocol
    from proalgotrader_core.protocols.order import OrderProtocol


class StoplossTargetEntityProtocol(Protocol):
    value: float | int
    trailing_value: float | int | None

    def __init__(
        self,
        value: float | int,
        trailing_value: float | int | None = None,
    ) -> None: ...


class StoplossProtocol(StoplossTargetEntityProtocol):
    def __init__(
        self,
        value: float | int,
        trailing_value: float | int | None = None,
    ) -> None: ...


class TargetProtocol(StoplossTargetEntityProtocol):
    def __init__(
        self,
        value: float | int,
        trailing_value: float | int | None = None,
    ) -> None: ...


class RiskRewardProtocol(Protocol):
    position: "PositionProtocol"
    stoploss: StoplossProtocol
    target: Optional[TargetProtocol]
    unit: str

    def __init__(
        self,
        *,
        position: "PositionProtocol",
        stoploss: StoplossProtocol | Any,
        target: TargetProtocol | Any = None,
        unit: RiskRewardUnit = RiskRewardUnit.POINTS,
    ) -> None: ...

    def to_item(self) -> Dict[str, Any]: ...


class RiskRewardManagerProtocol(Protocol):
    stoploss_order: "OrderProtocol"
    target_order: "OrderProtocol | None"
    stoploss_trailing_price: float | None
    target_trailing_price: float | None
    on_trail_callback: Callable[..., Any]

    def __init__(
        self,
        *,
        stoploss_order: "OrderProtocol",
        stoploss_trailing_price: float | None,
        target_order: "OrderProtocol | None" = None,
        target_trailing_price: float | None,
        on_trail_callback: Callable[..., Any],
    ) -> None: ...

    async def monitor_trailing(self) -> None: ...
