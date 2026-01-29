from typing import Any, Dict
from logzero import logger

from proalgotrader_core.base_symbol import BaseSymbol
from proalgotrader_core.protocols.base_symbol import BaseSymbolProtocol

from proalgotrader_core.enums.segment_type import SegmentType

from proalgotrader_core.protocols.tick import TickProtocol
from proalgotrader_core.protocols.broker import BrokerProtocol


class BrokerSymbol:
    def __init__(
        self,
        order_broker_manager: BrokerProtocol,
        broker_symbol_info: Dict[str, Any],
    ):
        self.order_broker_manager = order_broker_manager
        self.base_symbol: BaseSymbolProtocol = BaseSymbol(
            broker_symbol_info["base_symbol"]
        )

        self.id: int = broker_symbol_info["id"]
        self.market_type: str = broker_symbol_info["market_type"]
        self.segment_type: str = broker_symbol_info["segment_type"]
        self.expiry_date: str = broker_symbol_info["expiry_date"]
        self.strike_price: int = broker_symbol_info["strike_price"]
        self.option_type: str = broker_symbol_info["option_type"]
        self.lot_size: int = broker_symbol_info["lot_size"]
        self.symbol_name: str = broker_symbol_info["symbol_name"]
        self.symbol_token: str = broker_symbol_info["symbol_token"]
        self.exchange_token: int = broker_symbol_info["exchange_token"]

        self.__ltp: float = 0
        self.total_volume: int = 0
        self.subscribed: bool = False

    @property
    def can_trade(self) -> bool:
        return not (
            self.segment_type == SegmentType.Equity.value
            and self.base_symbol.type == "Index"
        )

    async def get_ltp(self) -> float:
        """Get LTP data. If not available, fetch quotes on-demand."""
        # If we already have LTP data, return it
        if self.__ltp > 0:
            return self.__ltp

        await self.order_broker_manager.fetch_quotes(self)

        return self.__ltp

    async def initialize(self):
        await self.order_broker_manager.subscribe(self, self.on_tick)

    async def on_bar(self, ltp: float, total_volume: int) -> None:
        self.__ltp = ltp
        self.total_volume = total_volume

    async def on_tick(self, tick: TickProtocol) -> None:
        self.__ltp = tick.ltp
        self.total_volume = tick.total_volume

        try:
            await self.order_broker_manager.notification_manager.send_message(
                data={
                    "exchange_token": self.exchange_token,
                    "ltp": self.__ltp,
                    "total_volume": self.total_volume,
                },
            )
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    def __str__(self):
        return self.symbol_name
