import asyncio

from datetime import date, datetime, time, timedelta
from typing import Any, List, Literal, Optional, Tuple, Type
from logzero import logger

from proalgotrader_core.base_algorithm import BaseAlgorithm
from proalgotrader_core._helpers.get_strike_price import get_strike_price
from proalgotrader_core.enums.risk_reward_unit import RiskRewardUnit
from proalgotrader_core.order_item import OrderItem
from proalgotrader_core.pnl_calculator import PnlCalculator
from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol
from proalgotrader_core.protocols.chart import ChartProtocol
from proalgotrader_core.protocols.order import OrderProtocol
from proalgotrader_core.protocols.position import PositionProtocol
from proalgotrader_core.protocols.pnl_calculator import PnlCalculatorProtocol
from proalgotrader_core.enums.account_type import AccountType
from proalgotrader_core.enums.candle_type import CandleType
from proalgotrader_core.enums.market_type import MarketType
from proalgotrader_core.enums.order_type import OrderType
from proalgotrader_core.enums.position_type import PositionType
from proalgotrader_core.enums.product_type import ProductType
from proalgotrader_core.enums.segment_type import SegmentType
from proalgotrader_core.protocols.position_manager import PositionManagerProtocol
from proalgotrader_core.protocols.multiple_position_manager import (
    MultiplePositionManagerProtocol,
)
from proalgotrader_core.protocols.signal_manager import SignalManagerProtocol
from proalgotrader_core.protocols.trade import TradeProtocol
from proalgotrader_core.risk_reward import RiskReward, Stoploss, Target


class Algorithm(BaseAlgorithm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @property
    def market_start_time(self) -> time:
        return self.algo_session.market_start_time

    @property
    def market_end_time(self) -> time:
        return self.algo_session.market_end_time

    @property
    def market_start_datetime(self) -> datetime:
        return self.algo_session.market_start_datetime

    @property
    def market_end_datetime(self) -> datetime:
        return self.algo_session.market_end_datetime

    @property
    def pre_market_time(self) -> datetime:
        return self.algo_session.pre_market_time

    @property
    def current_datetime(self) -> datetime:
        return self.algo_session.current_datetime

    @property
    def current_timestamp(self) -> int:
        return self.algo_session.current_timestamp

    @property
    def current_date(self) -> date:
        return self.algo_session.current_date

    @property
    def current_time(self) -> time:
        return self.algo_session.current_time

    @property
    def orders(self) -> List[OrderProtocol]:
        return self.order_broker_manager.orders.copy()

    @property
    def pending_orders(self) -> List[OrderProtocol]:
        return self.order_broker_manager.pending_orders.copy()

    @property
    def positions(self) -> List[PositionProtocol]:
        return self.order_broker_manager.positions.copy()

    @property
    def trades(self) -> List[TradeProtocol]:
        return self.order_broker_manager.trades.copy()

    @property
    def net_pnl(self) -> PnlCalculatorProtocol:
        return PnlCalculator(self.trades)

    @property
    def unrealized_pnl(self) -> PnlCalculatorProtocol:
        return PnlCalculator(self.positions)

    def set_interval(self, interval: timedelta) -> None:
        self.interval = interval

    def between_time(self, first: time, second: time) -> bool:
        return first < self.current_time < second

    async def add_signals(
        self,
        *,
        signal_manager: Optional[Type[SignalManagerProtocol]],
        symbol_names: List[str],
    ) -> None:
        if not signal_manager or not issubclass(signal_manager, SignalManagerProtocol):
            raise Exception("SignalManager is required.")

        base_symbol_ids = [
            self.order_broker_manager.base_symbols[symbol_name].id
            for symbol_name in symbol_names
        ]

        try:
            broker_title = self.order_broker_manager.broker_title

            payload = {
                "base_symbol_ids": base_symbol_ids,
                "exchange": "NSE",
                "market_type": "Cash",
                "segment_type": "Equity",
            }

            result = await self.api.get_signals(broker_title, payload)

            broker_symbols_data = result.get("broker_symbols", [])

            # Convert API data to BrokerSymbol objects using get_symbol
            signals = []

            for broker_symbol_data in broker_symbols_data:
                broker_symbol = await self.order_broker_manager.get_symbol(
                    broker_symbol_info=broker_symbol_data,
                    should_refresh=False,
                )

                signal = signal_manager(
                    algorithm=self,
                    broker_symbol=broker_symbol,
                )

                signals.append(signal)

            await asyncio.gather(*[signal.initialize() for signal in signals])

            self.signals.extend(signals)

        except Exception as e:
            logger.error(f"Failed to add signals: {e}")
            raise Exception(f"Failed to add signals: {e}")

    def set_position_manager(
        self,
        *,
        position_manager_class: (
            Type[PositionManagerProtocol | MultiplePositionManagerProtocol] | Any
        ) = None,
    ) -> None:
        if not position_manager_class:
            raise Exception("PositionManager is required.")

        # Check if it extends either protocol
        is_single = issubclass(position_manager_class, PositionManagerProtocol)

        is_multiple = issubclass(
            position_manager_class, MultiplePositionManagerProtocol
        )

        if not (is_single or is_multiple):
            raise Exception(
                "PositionManager must extend either PositionManagerProtocol or MultiplePositionManagerProtocol."
            )

        self.position_manager_class = position_manager_class
        self.position_manager_type = "single" if is_single else "multiple"

        # For single instance, create the position manager immediately
        if is_single and not is_multiple:
            self.position_manager = position_manager_class(algorithm=self)

    def get_position_manager(
        self, position: PositionProtocol
    ) -> PositionManagerProtocol | MultiplePositionManagerProtocol | None:
        """
        Get position manager instance for the specified position.

        Args:
            position: Position to get manager for

        Returns:
            Position manager instance for the specified position, or None if no manager is set
        """
        if not self.position_manager_class:
            return None

        # Check if it's a MultiplePositionManagerProtocol
        if issubclass(self.position_manager_class, PositionManagerProtocol):
            if not self.position_manager:
                self.position_manager = self.position_manager_class(algorithm=self)

            return self.position_manager

        if issubclass(self.position_manager_class, MultiplePositionManagerProtocol):
            return self.position_manager_class(algorithm=self, position=position)

        return None

    def set_account_type(self, *, account_type: AccountType | Any) -> None:
        if account_type and not isinstance(account_type, AccountType):
            logger.error("Invalid account type")
            raise ValueError("account_type must be an instance of AccountType or None")

        self.account_type = account_type

    async def add_chart(
        self,
        *,
        broker_symbol: BrokerSymbolProtocol,
        timeframe: timedelta,
        candle_type: CandleType = CandleType.REGULAR,
        **kwargs,
    ) -> ChartProtocol:
        try:
            chart = await self.chart_manager.register_chart(
                broker_symbol, timeframe, candle_type=candle_type, **kwargs
            )

            return chart
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def add_equity(
        self,
        *,
        symbol_name: str,
    ) -> BrokerSymbolProtocol:
        try:
            base_symbol = self.order_broker_manager.base_symbols[symbol_name]

            equity_symbol = await self.order_broker_manager.add_equity(
                base_symbol=base_symbol,
                market_type=MarketType.Cash.value,
                segment_type=SegmentType.Equity.value,
            )

            return equity_symbol
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def add_future(
        self,
        *,
        symbol_name: str,
        expiry_input: Tuple[Literal["Weekly", "Monthly"], int] | None = None,
    ) -> BrokerSymbolProtocol:
        try:
            equity_symbol = await self.add_equity(symbol_name=symbol_name)

            expiry_date = await self._get_fno_expiry(
                expiry_type="future",
                expiry_input=expiry_input,
                base_symbol=equity_symbol.base_symbol,
                market_type=MarketType.Derivative.value,
                segment_type=SegmentType.Option.value,
            )

            future_symbol = await self.order_broker_manager.add_future(
                base_symbol=equity_symbol.base_symbol,
                market_type=MarketType.Derivative.value,
                segment_type=SegmentType.Future.value,
                expiry_date=expiry_date,
            )

            return future_symbol
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def add_option(
        self,
        *,
        symbol_name: str,
        expiry_input: Tuple[Literal["Weekly", "Monthly"], int] | None = None,
        strike_price_input: int | None = None,
        option_type: Literal["CE", "PE"] | None = None,
    ) -> BrokerSymbolProtocol:
        try:
            equity_symbol = await self.add_equity(symbol_name=symbol_name)

            expiry_date = await self._get_fno_expiry(
                expiry_type="option",
                expiry_input=expiry_input,
                base_symbol=equity_symbol.base_symbol,
                market_type=MarketType.Derivative.value,
                segment_type=SegmentType.Option.value,
            )

            if not isinstance(strike_price_input, int):
                raise Exception(
                    "Invalid strike price input, must be integer like -1, 0, 1"
                )

            if option_type not in ["CE", "PE"]:
                raise Exception("Invalid option type, must be CE or PE")

            strike_price = await get_strike_price(equity_symbol, strike_price_input)

            option_symbol = await self.order_broker_manager.add_option(
                base_symbol=equity_symbol.base_symbol,
                market_type=MarketType.Derivative.value,
                segment_type=SegmentType.Option.value,
                expiry_date=expiry_date,
                strike_price=strike_price,
                option_type=option_type,
            )

            return option_symbol
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def buy(
        self,
        *,
        broker_symbol: BrokerSymbolProtocol,
        market_type: MarketType,
        product_type: ProductType,
        order_type: OrderType,
        quantities: int,
    ) -> None:
        try:
            order_item = OrderItem(
                broker_symbol=broker_symbol,
                market_type=market_type,
                product_type=product_type,
                order_type=order_type,
                position_type=PositionType.BUY,
                quantities=quantities,
            )

            await self.create_order(order_item=order_item)
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def sell(
        self,
        *,
        broker_symbol: BrokerSymbolProtocol,
        market_type: MarketType,
        product_type: ProductType,
        order_type: OrderType,
        quantities: int,
    ) -> None:
        try:
            order_item = OrderItem(
                broker_symbol=broker_symbol,
                market_type=market_type,
                product_type=product_type,
                order_type=order_type,
                position_type=PositionType.SELL,
                quantities=quantities,
            )

            await self.create_order(order_item=order_item)
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def create_risk_reward(
        self,
        *,
        position: PositionProtocol,
        stoploss: Stoploss | Any = None,
        target: Target | Any = None,
        unit: RiskRewardUnit = RiskRewardUnit.POINTS,
    ) -> None:
        try:
            risk_reward = RiskReward(
                position=position,
                stoploss=stoploss,
                target=target,
                unit=unit,
            )

            await self.order_broker_manager.create_risk_reward(
                position=position, item=risk_reward.to_item()
            )
        except Exception as e:
            raise Exception(e)

    async def create_order(self, *, order_item: OrderItem) -> None:
        try:
            await order_item.validate(algorithm=self)

            await self.order_broker_manager.create_order(order_item=order_item)
        except Exception as e:
            raise Exception(e)

    async def create_multiple_orders(self, *, order_items: List[OrderItem]) -> None:
        try:
            [await order_item.validate(algorithm=self) for order_item in order_items]

            await self.order_broker_manager.create_multiple_orders(
                order_items=order_items
            )
        except Exception as e:
            raise Exception(e)

    async def exit_all_positions(self) -> None:
        try:
            return await self.order_broker_manager.exit_all_positions()
        except Exception as e:
            raise Exception(e)
