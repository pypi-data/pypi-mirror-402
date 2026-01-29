from proalgotrader_core.protocols.position import PositionProtocol
from proalgotrader_core.protocols.broker import BrokerProtocol


class RiskRewardManager:
    def __init__(
        self,
        *,
        broker: BrokerProtocol,
        position: PositionProtocol,
        risk_reward_id: str,
        stoploss: float,
        trailing_stoploss: float | None,
        trail_stoploss_by: float | None,
        trail_stoploss_when: float | None,
        target: float | None,
        trailing_target: float | None,
        trail_target_by: float | None,
        trail_target_when: float | None,
    ) -> None:
        self.broker = broker
        self.position = position
        self.risk_reward_id = risk_reward_id
        self.stoploss = stoploss  # Initial stoploss for reference
        self.trailing_stoploss = trailing_stoploss  # Current trailing stoploss
        self.trail_stoploss_by = trail_stoploss_by  # Amount to trail by
        self.trail_stoploss_when = trail_stoploss_when  # Price when to trail stoploss
        self.target = target  # Initial target for reference
        self.trailing_target = trailing_target  # Current trailing target
        self.trail_target_by = trail_target_by  # Amount to trail by
        self.trail_target_when = trail_target_when  # Price when to trail target

    async def monitor(self) -> None:
        """
        Main method to monitor and execute trailing logic for both stoploss and target.
        Uses LTP from position.broker_symbol.ltp for calculations.
        """
        current_ltp = await self.position.broker_symbol.get_ltp()
        position_type = self.position.position_type

        # Check for stoploss hit
        if self.trailing_stoploss and self.__is_stoploss_hit(
            current_ltp, position_type
        ):
            await self.broker.on_risk_reward_hit(
                risk_reward_id=self.risk_reward_id,
                position_id=self.position.position_id,
                price=current_ltp,
                type="stoploss",
            )
            return  # Exit if stoploss is hit

        # Check for target hit
        if self.trailing_target and self.__is_target_hit(current_ltp, position_type):
            await self.broker.on_risk_reward_hit(
                risk_reward_id=self.risk_reward_id,
                position_id=self.position.position_id,
                price=current_ltp,
                type="target",
            )
            return  # Exit if target is hit

        # Monitor stoploss trailing
        if self.trailing_stoploss and self.trail_stoploss_by:
            await self.__monitor_sl_trailing(current_ltp, position_type)

        # Monitor target trailing
        if self.trailing_target and self.trail_target_by:
            await self.__monitor_tgt_trailing(current_ltp, position_type)

    async def __monitor_sl_trailing(
        self,
        current_ltp: float,
        position_type: str,
    ) -> None:
        """
        Monitor stoploss trailing and trigger callback when trailing should occur.
        """
        should_update = self.__should_update_trailing_sl(
            current_ltp=current_ltp,
            position_type=position_type,
        )

        if should_update:
            # Calculate new stoploss price after trailing
            # Trail by the full amount from the initial stoploss
            if position_type == "BUY":
                new_stoploss_price = self.stoploss + self.trail_stoploss_by
            else:  # SELL
                new_stoploss_price = self.stoploss - self.trail_stoploss_by

            # Check if new stoploss would cross target price
            if self.__would_stoploss_cross_target(new_stoploss_price, position_type):
                return  # Don't trail if it would cross target

            # Update the trailing stoploss
            self.trailing_stoploss = new_stoploss_price

            await self.broker.on_risk_reward_trail(
                risk_reward_id=self.risk_reward_id,
                position_id=self.position.position_id,
                price=new_stoploss_price,
                type="stoploss",
            )

    async def __monitor_tgt_trailing(
        self,
        current_ltp: float,
        position_type: str,
    ) -> None:
        """
        Monitor target trailing and trigger callback when trailing should occur.
        """
        should_update = self.__should_update_trailing_tgt(
            current_ltp=current_ltp,
            position_type=position_type,
        )

        if should_update:
            # Calculate new target price after trailing
            # Trail by the full amount from the initial target
            if position_type == "BUY":
                new_target_price = self.target + self.trail_target_by
            else:  # SELL
                new_target_price = self.target - self.trail_target_by

            # Check if new target would cross stoploss price
            if self.__would_target_cross_stoploss(new_target_price, position_type):
                return  # Don't trail if it would cross stoploss

            # Update the trailing target
            self.trailing_target = new_target_price

            await self.broker.on_risk_reward_trail(
                risk_reward_id=self.risk_reward_id,
                position_id=self.position.position_id,
                price=new_target_price,
                type="target",
            )

    def __should_update_trailing_sl(
        self,
        current_ltp: float,
        position_type: str,
    ) -> bool:
        """
        Check if we should update the trailing stop loss.
        Returns False if stoploss will hit (no update needed as order will execute).
        Returns True only if trailing should be updated.

        Uses trail_stoploss_when to determine when to trail.
        """
        if not self.trail_stoploss_when:
            return False

        if position_type == "BUY":
            # Check if stoploss will hit (price touches stoploss level)
            if current_ltp <= self.trailing_stoploss:
                return False

            # Trail when LTP crosses the trail_when threshold
            return current_ltp >= self.trail_stoploss_when

        else:  # SELL
            # Check if stoploss will hit (price touches stoploss level)
            if current_ltp >= self.trailing_stoploss:
                return False

            # Trail when LTP crosses the trail_when threshold
            return current_ltp <= self.trail_stoploss_when

    def __would_stoploss_cross_target(
        self,
        new_stoploss_price: float,
        position_type: str,
    ) -> bool:
        """
        Check if the new stoploss price would cross the target price.
        This prevents stoploss from trailing beyond the target level.
        """
        if not self.trailing_target:
            return False  # No target to cross

        if position_type == "BUY":
            # For BUY: stoploss should not trail above target
            return new_stoploss_price >= self.trailing_target
        else:  # SELL
            # For SELL: stoploss should not trail below target
            return new_stoploss_price <= self.trailing_target

    def __would_target_cross_stoploss(
        self,
        new_target_price: float,
        position_type: str,
    ) -> bool:
        """
        Check if the new target price would cross the stoploss price.
        This prevents target from trailing beyond the stoploss level.
        """
        if not self.trailing_stoploss:
            return False  # No stoploss to cross

        if position_type == "BUY":
            # For BUY: target should not trail below stoploss
            return new_target_price <= self.trailing_stoploss
        else:  # SELL
            # For SELL: target should not trail above stoploss
            return new_target_price >= self.trailing_stoploss

    def __should_update_trailing_tgt(
        self,
        current_ltp: float,
        position_type: str,
    ) -> bool:
        """
        Check if we should update the trailing target.
        Returns False if target will hit (no update needed as order will execute).
        Returns True only if trailing should be updated.

        Uses trail_target_when to determine when to trail.
        """
        if not self.trail_target_when:
            return False

        if position_type == "BUY":
            # Check if target will hit (price touches target level)
            if current_ltp >= self.trailing_target:
                return False

            # Trail when LTP crosses the trail_when threshold
            return current_ltp >= self.trail_target_when

        else:  # SELL
            # Check if target will hit (price touches target level)
            if current_ltp <= self.trailing_target:
                return False

            # Trail when LTP crosses the trail_when threshold
            return current_ltp <= self.trail_target_when

    def __is_stoploss_hit(self, current_ltp: float, position_type: str) -> bool:
        """
        Check if the stoploss has been hit.
        """
        if position_type == "BUY":
            return current_ltp <= self.trailing_stoploss
        else:  # SELL
            return current_ltp >= self.trailing_stoploss

    def __is_target_hit(self, current_ltp: float, position_type: str) -> bool:
        """
        Check if the target has been hit.
        """
        if position_type == "BUY":
            return current_ltp >= self.trailing_target
        else:  # SELL
            return current_ltp <= self.trailing_target
