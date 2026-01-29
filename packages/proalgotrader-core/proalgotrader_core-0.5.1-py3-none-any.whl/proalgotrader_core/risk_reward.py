from typing import Any, Dict
from proalgotrader_core.enums.risk_reward_unit import RiskRewardUnit
from proalgotrader_core.protocols.position import PositionProtocol


class StoplossTargetEntity:
    def __init__(
        self,
        value: float | int,
        trailing_value: float | int | None = None,
    ) -> None:
        self.value = value
        self.trailing_value = trailing_value


class Stoploss(StoplossTargetEntity):
    def __init__(
        self,
        value: float | int,
        trailing_value: float | int | None = None,
    ) -> None:
        super().__init__(value=value, trailing_value=trailing_value)


class Target(StoplossTargetEntity):
    def __init__(
        self,
        value: float | int,
        trailing_value: float | int | None = None,
    ) -> None:
        super().__init__(value=value, trailing_value=trailing_value)


class RiskReward:
    def __init__(
        self,
        *,
        position: PositionProtocol,
        stoploss: Stoploss | Any,
        target: Target | Any = None,
        unit: RiskRewardUnit = RiskRewardUnit.POINTS,
    ) -> None:
        if not stoploss:
            raise Exception("Stoploss is required")

        if stoploss and not isinstance(stoploss, Stoploss):
            raise Exception("Invalid Stoploss")

        if target and not isinstance(target, Target):
            raise Exception("Invalid Target")

        self.position = position
        self.stoploss = stoploss
        self.target = target
        self.unit = unit.value if isinstance(unit, RiskRewardUnit) else unit

    def to_item(self) -> Dict[str, Any]:
        stoploss = self.calculate_price_level(self.stoploss.value, "stoploss")
        trail_stoploss_by = self.calculate_price(self.stoploss.trailing_value)
        target = self.calculate_price_level(self.target.value, "target")
        trail_target_by = self.calculate_price(self.target.trailing_value)

        return {
            "stoploss": round(stoploss, 2) if stoploss is not None else None,
            "trail_stoploss_by": (
                round(trail_stoploss_by, 2) if trail_stoploss_by is not None else None
            ),
            "target": round(target, 2) if target is not None else None,
            "trail_target_by": (
                round(trail_target_by, 2) if trail_target_by is not None else None
            ),
        }

    def calculate_price_level(
        self, value: float | None, level_type: str
    ) -> float | None:
        """
        Calculate price level for stoploss or target based on position type.

        Args:
            value: The value to calculate price from
            level_type: Either "stoploss" or "target"

        Returns:
            Calculated price level or None if value is None
        """
        price = self.calculate_price(value)

        if not price:
            return None

        position_type = self.position.position_type

        net_price = float(self.position.net_price)

        if level_type == "stoploss":
            return net_price - price if position_type == "BUY" else net_price + price
        else:
            return net_price + price if position_type == "BUY" else net_price - price

    def calculate_price(self, value: float | None) -> float | None:
        if not value:
            return None

        if self.unit == "Points":
            return value

        net_price = float(self.position.net_price)

        return round((value * net_price) / 100, 2)
