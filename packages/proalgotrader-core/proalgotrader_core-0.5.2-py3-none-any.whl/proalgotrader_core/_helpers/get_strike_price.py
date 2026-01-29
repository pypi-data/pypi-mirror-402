from logzero import logger

from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol


async def get_strike_price(
    broker_symbol: BrokerSymbolProtocol, strike_price_input: int = 0
) -> int:
    try:
        strike_size = broker_symbol.base_symbol.strike_size
        total_increment = strike_size * strike_price_input

        rounded_quotient = round(await broker_symbol.get_ltp() / strike_size)
        nearest_denomination = rounded_quotient * strike_size

        return int(nearest_denomination + total_increment)
    except Exception as e:
        logger.debug(e)
        raise Exception(e)
