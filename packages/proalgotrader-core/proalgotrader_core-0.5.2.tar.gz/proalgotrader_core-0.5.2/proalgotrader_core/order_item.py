from proalgotrader_core.broker_symbol import BrokerSymbol
from proalgotrader_core.enums.account_type import AccountType
from proalgotrader_core.protocols.broker_symbol import BrokerSymbolProtocol
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.enums.market_type import MarketType
from proalgotrader_core.enums.order_type import OrderType
from proalgotrader_core.enums.position_type import PositionType
from proalgotrader_core.enums.product_type import ProductType


class OrderItem:
    def __init__(
        self,
        broker_symbol: BrokerSymbolProtocol,
        market_type: MarketType | str,
        product_type: ProductType | str,
        order_type: OrderType | str,
        position_type: PositionType | str,
        quantities: int,
        limit_price: float | None = None,
    ) -> None:
        self.broker_symbol = broker_symbol

        self.market_type = (
            market_type if isinstance(market_type, str) else market_type.value
        )

        self.product_type = (
            product_type if isinstance(product_type, str) else product_type.value
        )

        self.order_type = (
            order_type if isinstance(order_type, str) else order_type.value
        )

        self.position_type = (
            position_type if isinstance(position_type, str) else position_type.value
        )

        self.quantities = quantities

        self.limit_price = limit_price

    async def validate(self, algorithm: AlgorithmProtocol | None = None):
        if not isinstance(self.broker_symbol, BrokerSymbol):
            raise Exception("Symbol must be instance of BrokerSymbol")

        if not self.quantities:
            raise Exception("Quantities is required")

        if self.broker_symbol.market_type != self.market_type:
            raise Exception("Invalid market type")

        if not self.broker_symbol.can_trade:
            raise Exception("Can not trade in this symbol")

        if (
            self.market_type == MarketType.Cash.value
            and self.product_type == ProductType.CNC.value
            and self.position_type == PositionType.SELL.value
        ):
            raise Exception("Equity can't be sold")

        if self.order_type not in [e.value for e in OrderType]:
            raise Exception("Invalid order type")

        if self.quantities % self.broker_symbol.lot_size != 0:
            lot_size = self.broker_symbol.lot_size

            raise Exception(f"Invalid quantities, must be multiple of {lot_size}")

        if self.order_type == OrderType.LIMIT_ORDER.value and not self.limit_price:
            raise Exception("Limit price is required for creating limit order")

        if algorithm and algorithm.account_type is not None:
            await self._validate_account_type(algorithm.account_type)

    async def _validate_account_type(self, account_type: AccountType) -> None:
        """Validate that order parameters match the configured AccountType."""

        # Get the expected market_type and product_type from AccountType
        expected_market_type, expected_product_type = account_type.value

        # Validate market_type matches
        if self.market_type != expected_market_type.value:
            raise Exception(
                f"Order market_type '{self.market_type}' does not match AccountType "
                f"'{account_type}' which requires '{expected_market_type.value}'"
            )

        # Validate product_type matches
        if self.product_type != expected_product_type.value:
            raise Exception(
                f"Order product_type '{self.product_type}' does not match AccountType "
                f"'{account_type}' which requires '{expected_product_type.value}'"
            )

        # Additional symbol type validation for market restrictions
        if expected_market_type.value == MarketType.Cash.value:
            # Cash market should only trade equity/stocks
            if self.broker_symbol.base_symbol.type not in ["Stock"]:
                raise Exception(
                    f"AccountType '{account_type}' (Cash market) can only trade equity/stocks, "
                    f"but trying to trade '{self.broker_symbol.base_symbol.type}'"
                )
        elif expected_market_type.value == MarketType.Derivative.value:
            # Derivative market should trade options/futures
            if self.broker_symbol.base_symbol.type not in [
                "Option",
                "Future",
                "Index",
            ]:
                raise Exception(
                    f"AccountType '{account_type}' (Derivative market) can only trade options/futures, "
                    f"but trying to trade '{self.broker_symbol.base_symbol.type}'"
                )
