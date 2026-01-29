import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class KAMA(Indicator):
    """
    KAMA - Kaufman Adaptive Moving Average

    The Kaufman Adaptive Moving Average (KAMA) is a moving average that adjusts its
    smoothing constant based on market volatility. It was developed by Perry Kaufman.

    KAMA is designed to account for market noise and volatility. When the market
    is trending, KAMA will follow the trend more closely. When the market is ranging
    or choppy, KAMA will be more stable and less reactive to price changes.

    The calculation involves:
    1. Efficiency Ratio (ER) = Direction / Volatility
    2. Smoothing Constant (SC) = [ER * (fastest SC - slowest SC) + slowest SC]^2
    3. KAMA = Previous KAMA + SC * (Price - Previous KAMA)

    Parameters:
    - timeperiod: The period for KAMA calculation (default: 30)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        kama = KAMA(timeperiod=14)
        kama_fast = KAMA(timeperiod=10, output_columns=["kama_fast"])
    """

    def __init__(
        self,
        timeperiod: int = 30,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.column = column
        self.kama_col = f"kama_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the KAMA expression using polars_talib."""
        return Indicators.build_kama(
            source=pl.col(self.column), timeperiod=self.timeperiod
        )

    def expr(self) -> pl.Expr:
        """Return the KAMA expression with proper column alias."""
        return self.build().alias(self.kama_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.kama_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "KAMA expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("KAMA requires a non-empty single output column name")

            self.kama_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for KAMA calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable KAMA calculation."""
        # KAMA needs more warmup data due to its adaptive nature
        # and the efficiency ratio calculation
        return self.timeperiod * 3
