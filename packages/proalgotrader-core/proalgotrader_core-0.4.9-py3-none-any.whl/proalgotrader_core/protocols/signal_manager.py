from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
    from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol


class SignalManagerProtocol(ABC):
    @abstractmethod
    def __init__(
        self, *, algorithm: "AlgorithmProtocol", broker_symbol: "BrokerSymbolProtocol"
    ) -> None: ...

    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def next(self) -> None: ...
