import asyncio

from logzero import logger
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Tuple

from proalgotrader_core.algo_session import AlgoSession
from proalgotrader_core.api import Api
from proalgotrader_core.base_symbol import BaseSymbol
from proalgotrader_core.enums.order_type import OrderType
from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
from proalgotrader_core.protocols.base_symbol import BaseSymbolProtocol
from proalgotrader_core.broker_symbol import BrokerSymbol
from proalgotrader_core.notification_manager import NotificationManager
from proalgotrader_core.order import Order
from proalgotrader_core.order_item import OrderItem
from proalgotrader_core.position import Position
from proalgotrader_core.trade import Trade
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.broker import BrokerProtocol
from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol
from proalgotrader_core.protocols.order import OrderProtocol
from proalgotrader_core.protocols.position import PositionProtocol
from proalgotrader_core.protocols.trade import TradeProtocol


class RequestProcessor:
    def __init__(self, broker: BrokerProtocol) -> None:
        self.__broker = broker
        self.__processing_request: bool = False
        self.__order_lock: asyncio.Lock = asyncio.Lock()

    def is_processing(self) -> bool:
        return self.__processing_request

    @asynccontextmanager
    async def processing(self):
        await self.acquire_lock()

        try:
            yield
        except Exception as e:
            raise Exception(e)
        finally:
            await self.release_lock()

    async def acquire_lock(self):
        """Manually acquire the lock and set processing to true."""
        await self.__order_lock.acquire()
        self.__processing_request = True

    async def release_lock(self):
        """Manually release the lock and set processing to false."""
        self.__processing_request = False
        self.__order_lock.release()


class Broker(BrokerProtocol):
    def __init__(
        self,
        api: Api,
        algo_session: AlgoSession,
        notification_manager: NotificationManager,
        algorithm: AlgorithmProtocol,
    ) -> None:
        self.api = api
        self.algo_session = algo_session
        self.notification_manager = notification_manager

        self.algorithm = algorithm
        self.algo_session_broker = algo_session.project.broker_info

        self.id = self.algo_session_broker.id
        self.broker_uid = self.algo_session_broker.broker_uid
        self.broker_title = self.algo_session_broker.broker_title
        self.broker_name = self.algo_session_broker.broker_name
        self.broker_config = self.algo_session_broker.broker_config

        self.base_symbols: Dict[str, BaseSymbolProtocol] = {}
        self.broker_symbols: Dict[Any, BrokerSymbolProtocol] = {}

        self.__orders: Dict[str, OrderProtocol] = {}
        self.__positions: Dict[str, PositionProtocol] = {}
        self.__trades: Dict[str, TradeProtocol] = {}

        self.initial_capital: float = 0
        self.current_capital: float = 0

        self.__broker_symbol_subscriptions: Dict[str, Any] = {}
        self.__broker_symbol_listeners: Dict[str, List[Callable[..., Any]]] = {}
        self.__request_processor: RequestProcessor = RequestProcessor(broker=self)
        self.__notifiable_actions: Dict[str, Any] = {}

    @property
    def request_processor(self):
        return self.__request_processor

    def is_processing(self) -> bool:
        return self.request_processor.is_processing()

    def get_symbol_subscriptions(self) -> Dict[str, Any]:
        return self.__broker_symbol_subscriptions

    def get_broker_symbol_listeners(self) -> Dict[str, List[Callable[..., Any]]]:
        return self.__broker_symbol_listeners

    def get_unsubscribed_symbols(self) -> List[BrokerSymbol]:
        """Get list of broker symbols that are queued but not yet subscribed."""
        return [
            subscription_data["broker_symbol"]
            for subscription_data in self.__broker_symbol_subscriptions.values()
            if not subscription_data["broker_symbol"].subscribed
        ]

    async def subscribe(
        self, broker_symbol: BrokerSymbol, on_tick: Callable[..., Any]
    ) -> None:
        logger.info(
            f"🔗 Broker subscribing to {broker_symbol.symbol_name} (subscribed: {broker_symbol.subscribed})"
        )

        # Check if symbol already exists in subscriptions
        if broker_symbol.symbol_name in self.__broker_symbol_subscriptions:
            logger.info(
                f"📝 Adding listener to existing subscription for {broker_symbol.symbol_name}"
            )
            # Add to existing listeners list (check for duplicates)
            if broker_symbol.symbol_name not in self.__broker_symbol_listeners:
                self.__broker_symbol_listeners[broker_symbol.symbol_name] = []

            if on_tick not in self.__broker_symbol_listeners[broker_symbol.symbol_name]:
                self.__broker_symbol_listeners[broker_symbol.symbol_name].append(
                    on_tick
                )
        else:
            # Create new subscription entry
            self.__broker_symbol_subscriptions[broker_symbol.symbol_name] = {
                "broker_symbol": broker_symbol,
            }
            # Create new listeners list
            self.__broker_symbol_listeners[broker_symbol.symbol_name] = [on_tick]

    @property
    def orders(self) -> List[OrderProtocol]:
        return list(self.__orders.values())

    @property
    def pending_orders(self) -> List[OrderProtocol]:
        return [order for order in self.orders if order.status == "pending"]

    @property
    def positions(self) -> List[PositionProtocol]:
        return list(self.__positions.values())

    @property
    def trades(self) -> List[TradeProtocol]:
        return list(self.__trades.values())

    async def set_notifiable_actions(self, actions: Dict[str, Any]):
        self.__notifiable_actions = actions

    def get_order(self, order_id: str) -> OrderProtocol | None:
        try:
            return self.__orders[order_id]
        except KeyError:
            return None

    def get_position(self, position_id: str) -> PositionProtocol | None:
        try:
            return self.__positions[position_id]
        except KeyError:
            return None

    def get_trade(self, trade_id: str) -> TradeProtocol | None:
        try:
            return self.__trades[trade_id]
        except KeyError:
            return None

    async def initialize(self) -> None:
        print("base order broker initializing")

        symbols = await self.api.get_base_symbols()

        base_symbols = symbols["base_symbols"]

        self.base_symbols = {
            base_symbol["key"]: BaseSymbol(base_symbol) for base_symbol in base_symbols
        }

        asyncio.create_task(self.__monitor_notifiable_actions())

        asyncio.create_task(self.__monitor_symbol_subscriptions())

    async def __monitor_notifiable_actions(self):
        """Background loop to monitor for notifiable actions."""
        while True:
            try:
                if self.__notifiable_actions and not self.is_processing():
                    await self.process_notifiable_actions()
                    self.__notifiable_actions = {}
            except Exception as e:
                logger.error(f"Error in monitor_notifiable_actions: {e}")
            finally:
                await asyncio.sleep(0.1)

    async def __monitor_symbol_subscriptions(self):
        """Background loop to monitor symbol subscriptions and start them when needed."""
        while True:
            try:
                unsubscribed_symbols = self.get_unsubscribed_symbols()

                if unsubscribed_symbols:
                    await self.start_subscriptions(unsubscribed_symbols)

            except Exception as e:
                logger.error(f"Error in monitor_symbol_subscriptions: {e}")
            finally:
                await asyncio.sleep(0.1)

    async def process_notifiable_actions(self) -> None:
        position_actions = self.__notifiable_actions.get("positions", {})

        created_ids = [
            pid for pid, action in position_actions.items() if action == "created"
        ]

        deleted_ids = [
            pid for pid, action in position_actions.items() if action == "deleted"
        ]

        # Notify for created positions
        for pid in created_ids:
            position = self.get_position(pid)

            if position:
                try:
                    await self.algorithm.on_position_open(position=position)
                except Exception as e:
                    logger.debug(f"Error notifying position open for {pid}: {e}")

        # Notify for deleted positions
        for pid in deleted_ids:
            position = self.get_position(pid)

            if position:
                try:
                    await self.algorithm.on_position_closed(position=position)
                except Exception as e:
                    logger.debug(f"Error notifying position closed for {pid}: {e}")

    async def get_order_info(self, data: Dict[str, Any]) -> OrderProtocol:
        order_id = data["order_id"]

        if order_id in self.__orders:
            existing_order = self.__orders[order_id]

            existing_order.update_from_dict(data)

            return existing_order

        broker_symbol = await self.get_symbol(
            broker_symbol_info=data["broker_symbol"],
            should_refresh=True,
        )

        order = Order(data, broker_symbol=broker_symbol, algorithm=self.algorithm)

        await order.initialize()

        return order

    async def get_position_info(self, data: Dict[str, Any]) -> PositionProtocol:
        position_id = data["position_id"]

        if position_id in self.__positions:
            existing_position = self.__positions[position_id]

            existing_position.update_from_dict(data)

            return existing_position

        broker_symbol = await self.get_symbol(
            broker_symbol_info=data["broker_symbol"],
            should_refresh=True,
        )

        position = Position(data, broker_symbol=broker_symbol, algorithm=self.algorithm)

        await position.initialize()

        return position

    async def get_trade_info(self, data: Dict[str, Any]) -> TradeProtocol:
        trade_id = data["trade_id"]

        if trade_id in self.__trades:
            existing_trade = self.__trades[trade_id]

            existing_trade.update_from_dict(data)

            return existing_trade

        broker_symbol = await self.get_symbol(
            broker_symbol_info=data["broker_symbol"],
            should_refresh=True,
        )

        trade = Trade(data, broker_symbol=broker_symbol, algorithm=self.algorithm)

        await trade.initialize()

        return trade

    async def set_portfolio(self) -> None:
        try:
            portfolio = await self.api.get_portfolio()

            await self.set_orders(portfolio["orders"])

            await self.set_positions(portfolio["positions"])

            await self.set_trades(portfolio["trades"])
        except Exception as e:
            logger.info("set_portfolio: error happened", e)
            raise Exception(e)

    async def set_broker_symbols(self, broker_symbols: List[Dict[str, Any]]) -> None:
        tasks: List[asyncio.Task[BrokerSymbolProtocol]] = []

        for broker_symbol_info in broker_symbols:
            task = asyncio.create_task(
                self.get_symbol(
                    broker_symbol_info=broker_symbol_info,
                    should_refresh=False,
                )
            )

            tasks.append(task)

        await asyncio.gather(*tasks)

    async def set_orders(self, orders: List) -> None:
        try:
            self.__orders = {
                order["order_id"]: await self.get_order_info(order) for order in orders
            }
        except Exception as e:
            logger.info("set_orders: error happened", e)
            raise Exception(e)

    async def set_positions(self, positions: List) -> None:
        try:
            self.__positions = {
                position["position_id"]: await self.get_position_info(position)
                for position in positions
            }
        except Exception as e:
            logger.info("set_positions: error happened", e)
            raise Exception(e)

    async def set_trades(self, trades: List) -> None:
        try:
            self.__trades = {
                trade["trade_id"]: await self.get_trade_info(trade) for trade in trades
            }
        except Exception as e:
            logger.info("set_trades: error happened", e)
            raise Exception(e)

    async def on_after_market_closed(self) -> None:
        try:
            for position in self.positions:
                await position.on_after_market_closed()

            await self.stop_connection()
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def add_equity(
        self,
        *,
        base_symbol: BaseSymbolProtocol,
        market_type: str,
        segment_type: str,
    ) -> BrokerSymbolProtocol:
        try:
            data = {
                "base_symbol_id": base_symbol.id,
                "exchange": base_symbol.exchange,
                "market_type": market_type,
                "segment_type": segment_type,
                "expiry_input": None,
                "expiry_date": None,
                "strike_price": None,
                "option_type": None,
            }

            broker_symbol = await self.get_symbol(
                broker_symbol_info=data,
                should_refresh=True,
            )

            return broker_symbol
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def add_future(
        self,
        *,
        base_symbol: BaseSymbolProtocol,
        market_type: str,
        segment_type: str,
        expiry_date: str,
    ) -> BrokerSymbolProtocol:
        try:
            data = {
                "base_symbol_id": base_symbol.id,
                "exchange": base_symbol.exchange,
                "market_type": market_type,
                "segment_type": segment_type,
                "expiry_date": expiry_date,
                "strike_price": None,
                "option_type": None,
            }

            broker_symbol = await self.get_symbol(
                broker_symbol_info=data,
                should_refresh=True,
            )

            return broker_symbol
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def add_option(
        self,
        *,
        base_symbol: BaseSymbolProtocol,
        market_type: str,
        segment_type: str,
        expiry_date: str,
        strike_price: int,
        option_type: str,
    ) -> BrokerSymbolProtocol:
        try:
            data = {
                "base_symbol_id": base_symbol.id,
                "exchange": base_symbol.exchange,
                "market_type": market_type,
                "segment_type": segment_type,
                "expiry_date": expiry_date,
                "strike_price": strike_price,
                "option_type": option_type,
            }

            broker_symbol = await self.get_symbol(
                broker_symbol_info=data,
                should_refresh=True,
            )

            return broker_symbol
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def __get_broker_symbol_key(
        self, broker_symbol_info: Dict[str, Any]
    ) -> Tuple[Any, ...]:
        base_symbol_id = broker_symbol_info["base_symbol_id"]
        exchange = broker_symbol_info["exchange"]
        market_type = broker_symbol_info["market_type"]
        segment_type = broker_symbol_info["segment_type"]
        expiry_date = broker_symbol_info["expiry_date"]
        strike_price = broker_symbol_info["strike_price"]
        option_type = broker_symbol_info["option_type"]

        key = (
            base_symbol_id,
            exchange,
            market_type,
            segment_type,
            expiry_date,
            strike_price,
            option_type,
        )

        return key

    async def get_symbol(
        self,
        broker_symbol_info: Dict[str, Any],
        should_refresh: bool = True,
    ) -> BrokerSymbolProtocol:
        key = await self.__get_broker_symbol_key(broker_symbol_info)

        if not should_refresh:
            return await self.__set_symbol(
                key=key,
                broker_symbol_info=broker_symbol_info,
            )

        try:
            return self.broker_symbols[key]
        except KeyError:
            base_symbol_id = broker_symbol_info["base_symbol_id"]

            filtered_base_symbol = next(
                base_symbol
                for base_symbol in self.base_symbols.values()
                if base_symbol.id == base_symbol_id
            )

            if not filtered_base_symbol:
                raise Exception("Invalid Base Symbol")

            broker_symbol_info = await self.__get_broker_symbols(
                broker_title=self.broker_title,
                payload=broker_symbol_info,
            )

            broker_symbol = await self.__set_symbol(
                key=key,
                broker_symbol_info=broker_symbol_info,
            )

            return broker_symbol

    async def __set_symbol(
        self,
        key: Tuple[Any, ...],
        broker_symbol_info: Dict[str, Any],
    ) -> BrokerSymbolProtocol:
        broker_symbol = BrokerSymbol(
            order_broker_manager=self,
            broker_symbol_info=broker_symbol_info,
        )

        await broker_symbol.initialize()

        self.broker_symbols[key] = broker_symbol

        return broker_symbol

    async def __get_broker_symbols(
        self, broker_title: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            broker_symbol: Dict[str, Any] = await self.api.get_broker_symbols(
                broker_title=broker_title,
                payload=payload,
            )

            return broker_symbol
        except Exception as e:
            logger.debug(e)
            raise Exception(e)

    async def get_positions(
        self,
        symbol_name: str,
        market_type: str,
        order_type: str,
        product_type: str,
        position_type: str,
    ) -> List[PositionProtocol]:
        return [
            position
            for position in self.positions
            if (
                position.broker_symbol.symbol_name == symbol_name
                and position.broker_symbol.market_type == market_type
                and position.order_type == order_type
                and position.product_type == product_type
                and position.position_type == position_type
            )
        ]

    async def _process_order(
        self, *, data: Dict[str, Any], actions: Dict[str, Any]
    ) -> None:
        for order_data in data.get("orders", []):
            order = await self.get_order_info(order_data)
            self.__orders[order.order_id] = order

        deleted_positions = {
            pid
            for pid, action in actions.get("positions", {}).items()
            if action == "deleted"
        }

        for pid in deleted_positions:
            self.__positions.pop(pid, None)

        for position_data in data.get("positions", []):
            pid = position_data["position_id"]

            if pid not in deleted_positions:
                position = await self.get_position_info(position_data)
                self.__positions[position.position_id] = position

        for trade_data in data.get("trades", []):
            trade = await self.get_trade_info(trade_data)
            self.__trades[trade.trade_id] = trade

        await self.set_current_capital()

        await self.set_notifiable_actions(actions=actions)

    async def build_payload(
        self,
        algo_session: AlgoSessionProtocol,
        payload_item: OrderItem,
    ) -> Dict[str, Any]:
        ltp_value = await payload_item.broker_symbol.get_ltp()
        return {
            "algo_session_id": algo_session.id,
            "broker_symbol_id": payload_item.broker_symbol.id,
            "market_type": payload_item.market_type,
            "product_type": payload_item.product_type,
            "order_type": payload_item.order_type,
            "position_type": payload_item.position_type,
            "quantities": payload_item.quantities,
            "price": (
                ltp_value
                if payload_item.order_type == OrderType.MARKET_ORDER.value and ltp_value
                else None
            ),
            "limit_price": (
                payload_item.limit_price
                if payload_item.order_type == OrderType.LIMIT_ORDER.value
                and payload_item.limit_price
                else None
            ),
            "ltp": ltp_value,
        }

    async def create_risk_reward(
        self, *, position: PositionProtocol, item: Dict[str, Any]
    ) -> None:
        async with self.request_processor.processing():
            response = await self.api.create_risk_reward(
                position_id=position.position_id, payload={"item": item}
            )

            updated_position = response["data"]["position"]

            await self.set_positions(positions=[updated_position])

    async def on_risk_reward_trail(
        self,
        *,
        risk_reward_id: str,
        position_id: str,
        price: float,
        type: str,
    ) -> None:
        """Handle risk reward trailing updates."""
        async with self.request_processor.processing():
            try:
                logger.info(
                    f"Trailing {type} updated to {price} for position {position_id}"
                )

                # Call API to update trailing risk reward
                payload = {
                    "item": {
                        "risk_reward_id": risk_reward_id,
                        "position_id": position_id,
                        "price": price,
                        "type": type,
                    }
                }

                response = await self.api.trail_risk_reward(
                    position_id=position_id, payload=payload
                )

                print(response)
            except Exception as e:
                logger.error(f"Error in risk reward trail: {e}")
                raise Exception(e)

    async def on_risk_reward_hit(
        self,
        *,
        risk_reward_id: str,
        position_id: str,
        price: float,
        type: str,
    ) -> None:
        """Handle risk reward hit events."""
        async with self.request_processor.processing():
            try:
                logger.info(
                    f"{type.capitalize()} hit for position {position_id} at {price}"
                )

                # Call API to handle risk reward hit
                payload = {
                    "item": {
                        "risk_reward_id": risk_reward_id,
                        "position_id": position_id,
                        "price": price,
                        "type": type,
                    }
                }

                response = await self.api.hit_risk_reward(
                    position_id=position_id, payload=payload
                )

                print(response)
            except Exception as e:
                logger.error(f"Error in risk reward hit: {e}")
                raise Exception(e)

    async def create_order(self, *, order_item: OrderItem) -> None:
        async with self.request_processor.processing():
            payload = {
                "item": await self.build_payload(self.algo_session, order_item),
            }

            response = await self.api.create_order(payload=payload)

            await self._process_order(
                data=response["data"], actions=response["actions"]
            )

    async def create_multiple_orders(self, *, order_items: List[OrderItem]) -> None:
        async with self.request_processor.processing():
            payload: Dict[str, List[Dict[str, Any]]] = {
                "items": [
                    await self.build_payload(self.algo_session, order_item)
                    for order_item in order_items
                ]
            }

            response = await self.api.create_multiple_orders(payload=payload)

            await self._process_order(
                data=response["data"], actions=response["actions"]
            )

    async def exit_all_positions(self) -> None:
        payload = {
            "items": [
                {
                    "position_id": position.position_id,
                    "ltp": position.broker_symbol.ltp,
                }
                for position in self.positions
            ]
        }

        if len(payload) > 0:
            response = await self.api.exit_all_positions(payload=payload)

            await self._process_order(
                data=response["data"], actions=response["actions"]
            )
        else:
            logger.info("No position to exit")

    async def next(self) -> None:
        for order in self.orders:
            if (
                order.order_type == OrderType.LIMIT_ORDER.value
                and order.status == "pending"
            ):
                await self.manage_pending_limit_orders(order)

        for position in self.positions:
            if position.order_type == OrderType.MARKET_ORDER.value:
                await position.next()

        if self.algorithm.position_manager:
            if self.algorithm.position_manager_type == "single":
                await self.algorithm.position_manager.next()

            if self.algorithm.position_manager_type == "multiple":
                for position in self.positions:
                    await position.position_manager.next()

    async def set_initial_capital(self) -> None:
        pass

    async def set_current_capital(self) -> None:
        pass

    async def stop_connection(self) -> None:
        pass
