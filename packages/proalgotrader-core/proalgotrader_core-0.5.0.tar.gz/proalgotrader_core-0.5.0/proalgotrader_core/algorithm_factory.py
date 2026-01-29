from asyncio import AbstractEventLoop
from typing import Any, Dict, Type
from logzero import logger

from proalgotrader_core.algo_session import AlgoSession
from proalgotrader_core.api import Api
from proalgotrader_core.args_manager import ArgsManager
from proalgotrader_core.chart_manager import ChartManager
from proalgotrader_core.notification_manager import NotificationManager
from proalgotrader_core.broker_manager import BrokerManager
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
from proalgotrader_core.protocols.api import ApiProtocol
from proalgotrader_core.protocols.chart_manager import ChartManagerProtocol
from proalgotrader_core.protocols.notification_manager import (
    NotificationManagerProtocol,
)
from proalgotrader_core.protocols.broker import BrokerProtocol


class AlgorithmFactory:
    def __init__(
        self,
        *,
        event_loop: AbstractEventLoop,
        strategy_class: Type[AlgorithmProtocol],
    ) -> None:
        self.event_loop = event_loop
        self.strategy_class = strategy_class

    def get_notification_manager(
        self,
        algo_session: AlgoSessionProtocol,
    ) -> NotificationManagerProtocol:
        return NotificationManager(algo_session=algo_session)

    def get_chart_manager(self, algorithm: AlgorithmProtocol) -> ChartManagerProtocol:
        return ChartManager(
            algorithm=algorithm,
        )

    def get_order_broker_manager(
        self,
        algorithm: AlgorithmProtocol,
        api: ApiProtocol,
        algo_session: AlgoSessionProtocol,
        notification_manager: NotificationManagerProtocol,
    ) -> BrokerProtocol:
        return BrokerManager.get_instance(
            algorithm=algorithm,
            api=api,
            algo_session=algo_session,
            notification_manager=notification_manager,
        )

    def get_algo_session(
        self, algo_session_info: Dict[str, Any]
    ) -> AlgoSessionProtocol:
        return AlgoSession(
            algo_session_info=algo_session_info,
        )

    async def create_algorithm_with_session(self) -> AlgorithmProtocol:
        """
        Factory function to create Algorithm with pre-initialized AlgoSession.
        This eliminates the need to make API calls inside Algorithm.boot()
        """
        try:
            args_manager = ArgsManager()

            args_manager.validate_arguments()

            api = Api(args_manager=args_manager)

            algo_session_info = await api.get_algo_session_info()

            # Always use the strategy passed from main.py
            strategy_class = self.strategy_class
            logger.info("Using strategy from main.py")

            algorithm = strategy_class(
                algorithm_factory=self,
                event_loop=self.event_loop,
                args_manager=args_manager,
                api=api,
                algo_session_info=algo_session_info,
            )

            return algorithm

        except Exception as e:
            logger.error(f"Failed to create algorithm with session: {e}")
            raise
