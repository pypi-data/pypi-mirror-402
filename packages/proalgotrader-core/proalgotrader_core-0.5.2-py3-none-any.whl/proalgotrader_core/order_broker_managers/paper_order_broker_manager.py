from proalgotrader_core.algo_session import AlgoSession
from proalgotrader_core.api import Api
from proalgotrader_core.notification_manager import NotificationManager
from proalgotrader_core.broker import Broker
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.order import OrderProtocol


class PaperOrderBrokerManager(Broker):
    def __init__(
        self,
        api: Api,
        algo_session: AlgoSession,
        notification_manager: NotificationManager,
        algorithm: AlgorithmProtocol,
    ) -> None:
        super().__init__(
            api=api,
            algo_session=algo_session,
            notification_manager=notification_manager,
            algorithm=algorithm,
        )

    async def set_initial_capital(self) -> None:
        self.initial_capital = self.algo_session.initial_capital

    async def set_current_capital(self) -> None:
        self.current_capital = self.algo_session.current_capital

    async def manage_pending_limit_orders(self, order: OrderProtocol):
        should_execute = await self.__should_execute_order(order)

        if not should_execute:
            return None

        await self.__execute_limit_order(
            ltp=await order.broker_symbol.get_ltp(), order_id=order.order_id
        )

    async def __should_execute_order(self, order: OrderProtocol) -> bool:
        current_ltp = float(await order.broker_symbol.get_ltp())
        trigger_price = float(order.trigger_price)
        limit_price = float(order.limit_price)

        if trigger_price > limit_price:
            return current_ltp >= trigger_price
        else:
            return current_ltp <= trigger_price

    async def __execute_limit_order(self, ltp: float, order_id: str):
        try:
            async with self.processing():
                payload = {
                    "item": {
                        "ltp": ltp,
                        "price": ltp,
                        "status": "completed",
                    }
                }

                response = await self.api.modify_order(
                    order_id=order_id,
                    payload=payload,
                )

                await self._process_order(
                    data=response["data"], actions=response["actions"]
                )
        except Exception as e:
            raise Exception(e)
