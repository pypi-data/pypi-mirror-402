import asyncio
import polars as pl

from asyncio import AbstractEventLoop, sleep
from datetime import datetime, timedelta
from typing import Any, Dict, List, Type
from logzero import logger

from proalgotrader_core._helpers.get_data_path import get_data_path
from proalgotrader_core.protocols.api import ApiProtocol
from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol
from proalgotrader_core.protocols.base_symbol import BaseSymbolProtocol
from proalgotrader_core.enums.account_type import AccountType
from proalgotrader_core.protocols.multiple_position_manager import (
    MultiplePositionManagerProtocol,
)
from proalgotrader_core.protocols.position import PositionProtocol
from proalgotrader_core.protocols.position_manager import PositionManagerProtocol
from proalgotrader_core.protocols.signal_manager import SignalManagerProtocol
from proalgotrader_core.protocols.algorithm_factory import AlgorithmFactoryProtocol


class BaseAlgorithm:
    def __init__(
        self,
        algorithm_factory: AlgorithmFactoryProtocol,
        event_loop: AbstractEventLoop,
        args_manager: ArgsManagerProtocol,
        api: ApiProtocol,
        algo_session_info: Dict[str, Any],
    ) -> None:
        self.algorithm_factory = algorithm_factory
        self.event_loop = event_loop
        self.args_manager = args_manager
        self.api = api
        self.algo_session_info = algo_session_info

        self.algo_session = self.algorithm_factory.get_algo_session(
            algo_session_info=self.algo_session_info,
        )

        self.notification_manager = self.algorithm_factory.get_notification_manager(
            algo_session=self.algo_session,
        )

        self.order_broker_manager = self.algorithm_factory.get_order_broker_manager(
            algorithm=self,
            api=self.api,
            algo_session=self.algo_session,
            notification_manager=self.notification_manager,
        )

        self.chart_manager = self.algorithm_factory.get_chart_manager(
            algorithm=self,
        )

        self.account_type: AccountType | Any = None

        self.__signals: List[SignalManagerProtocol] = []

        self.position_manager_class: (
            Type[PositionManagerProtocol] | Type[MultiplePositionManagerProtocol] | Any
        ) = None

        self.position_manager_type: str | Any = None

        self.position_manager: (
            PositionManagerProtocol | MultiplePositionManagerProtocol | Any
        ) = None

        self.interval = timedelta(seconds=1)

        # Cache for FNO expiry dates to avoid repeated API calls
        self.__fno_expiry_cache: Dict[str, str] = {}

        self.__trading_days: pl.DataFrame | None = None

        self.__booted = False

    @property
    def signals(self) -> List[SignalManagerProtocol]:
        return self.__signals

    @property
    def booted(self) -> bool:
        return self.__booted

    async def get_trading_days(self) -> pl.DataFrame:
        if self.__trading_days is None:
            self.__trading_days = await self.__fetch_trading_days()

        return self.__trading_days

    async def get_market_status(self) -> str:
        try:
            trading_days = await self.get_trading_days()

            if self.current_datetime.date() not in trading_days["date"].to_list():
                return "trading_closed"

            if self.current_datetime < self.pre_market_time:
                return "before_market_opened"

            if (self.current_datetime >= self.pre_market_time) and (
                self.current_datetime < self.market_start_datetime
            ):
                return "pre_market_opened"

            if self.current_datetime > self.market_end_datetime:
                return "after_market_closed"

            return "market_opened"
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def __validate_market_status(self) -> None:
        try:
            while True:
                market_status = await self.get_market_status()

                if market_status == "trading_closed":
                    raise Exception("trading is closed")
                elif market_status == "after_market_closed":
                    raise Exception("market is closed")
                elif market_status == "before_market_opened":
                    raise Exception("market is not opened yet")
                elif market_status == "pre_market_opened":
                    logger.info("market will be opened soon")
                    await sleep(1)
                elif market_status == "market_opened":
                    break
                else:
                    raise Exception("Invalid market status")
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def __fetch_trading_days(self) -> pl.DataFrame:
        data_path = await get_data_path(self.current_datetime)

        file = f"{data_path}/trading_days.csv"

        try:
            return pl.read_csv(file, try_parse_dates=True)
        except FileNotFoundError:
            trading_days = await self.api.get_trading_days()

            def get_json(date: str) -> Dict[str, Any]:
                dt = datetime.strptime(date, "%Y-%m-%d")

                return {
                    "date": dt.strftime("%Y-%m-%d"),
                    "day": dt.strftime("%A"),
                    "year": dt.year,
                }

            df = pl.DataFrame(
                data=[get_json(trading_day["date"]) for trading_day in trading_days],
            )

            df.write_csv(file)

        return pl.read_csv(file, try_parse_dates=True)

    async def _get_fno_expiry(
        self,
        expiry_type,
        expiry_input,
        base_symbol: BaseSymbolProtocol,
        market_type: str,
        segment_type: str,
    ) -> str:
        try:
            if not expiry_input:
                raise Exception("Expiry input is required")

            if not isinstance(expiry_input, tuple):
                raise Exception("Expiry input must be a tuple")

            expiry_period, expiry_number = expiry_input

            if expiry_type == "future" and expiry_period != "Monthly":
                raise Exception("Future expiry must be Monthly")

            if expiry_period not in ["Weekly", "Monthly"]:
                raise Exception("Expiry period must be Weekly or Monthly")

            if expiry_number < 0:
                raise Exception("Expiry number must be 0 or greater")

            # Create cache key from the request parameters
            cache_key = f"{base_symbol.id}_{market_type}_{segment_type}_{expiry_type}_{expiry_period}_{expiry_number}"

            # Check if expiry date is already cached
            if cache_key in self.__fno_expiry_cache:
                return self.__fno_expiry_cache[cache_key]

            # If not in cache, make API call
            payload = {
                "base_symbol_id": base_symbol.id,
                "market_type": market_type,
                "segment_type": segment_type,
                "expiry_input": expiry_input,
                "broker_title": self.order_broker_manager.broker_title,
            }

            expiry_date = await self.api.get_fno_expiry(payload)

            if not expiry_date:
                raise Exception("There was some error fetching expiry date")

            # Cache the result for future use
            self.__fno_expiry_cache[cache_key] = expiry_date

            return expiry_date
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def boot(self) -> None:
        try:
            if self.__booted:
                raise Exception("Algorithm already booted")

            logger.debug("booting algo")

            await self.notification_manager.connect()

            await self.__validate_market_status()

            await self.order_broker_manager.initialize()

            await self.order_broker_manager.start_connection()
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def run(self) -> None:
        try:
            if self.__booted:
                raise Exception("Algorithm already booted")

            logger.debug("market is opened")

            await self.__initialize()

            await self.__next()
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def __initialize(self) -> None:
        try:
            logger.debug("running initialize")

            await self.order_broker_manager.set_initial_capital()

            await self.order_broker_manager.set_portfolio()

            await self.order_broker_manager.set_current_capital()

            await self.initialize()
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def __next(self) -> None:
        try:
            self.__booted = True

            logger.debug("running Algorithm@next")

            market_status = await self.get_market_status()

            while market_status == "market_opened":
                try:
                    # Only proceed with main algorithm logic if all symbols have LTP data
                    if self.chart_manager.charts:
                        await self.__chart_next()

                    if not self.order_broker_manager.is_processing():
                        if self.signals:
                            await self.__signal_next()

                        await self.next()

                        await self.order_broker_manager.next()

                finally:
                    await sleep(self.interval.seconds)

            if market_status == "after_market_closed":
                await self.order_broker_manager.on_after_market_closed()

                logger.debug("market is closed")
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def __signal_next(self) -> None:
        try:
            tasks = []

            for signal in self.signals:
                task = asyncio.create_task(signal.next())
                tasks.append(task)

            await asyncio.gather(*tasks)
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def __chart_next(self) -> None:
        try:
            tasks = []

            for chart in self.chart_manager.charts:
                task = asyncio.create_task(chart.next())
                tasks.append(task)

            await asyncio.gather(*tasks)
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def on_position_open(self, position: PositionProtocol) -> None:
        pass

    async def on_position_closed(self, position: PositionProtocol) -> None:
        pass

    async def on_market_closed(self) -> None:
        pass

    def lot_to_quantities(self, broker_symbol, lots: int) -> int:
        """
        Convert lot quantities to actual quantities using the broker symbol's lot_size.

        Args:
            broker_symbol: The broker symbol object containing lot_size
            lots: Number of lots to convert

        Returns:
            int: Actual quantity (lots * lot_size)
        """
        try:
            return lots * broker_symbol.lot_size
        except (ValueError, TypeError):
            return lots
