from logzero import logger
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


class Application:
    def __init__(self, algorithm: AlgorithmProtocol) -> None:
        self.algorithm = algorithm

    async def start(self) -> None:
        logger.debug("booting application")
        await self.algorithm.boot()

        logger.debug("running application")
        await self.algorithm.run()
