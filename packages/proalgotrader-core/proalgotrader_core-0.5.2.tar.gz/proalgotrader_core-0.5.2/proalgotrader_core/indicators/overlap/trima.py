import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class TRIMA(Indicator):
    """
    TRIMA - Triangular Moving Average

    The Triangular Moving Average (TRIMA) is a type of weighted moving average that
    places more weight on the middle portion of the price series. It's calculated
    by taking a Simple Moving Average (SMA) of an SMA, which creates a triangular
    weighting distribution.

    TRIMA provides better smoothing than a simple moving average and is less sensitive
    to short-term price fluctuations. The triangular weighting gives more importance
    to recent prices while still considering older prices, making it excellent for
    trend identification with reduced noise.

    Key characteristics:
    - Double smoothing (SMA of SMA) creates triangular weight distribution
    - Less responsive to price changes compared to EMA
    - Better smoothing than SMA with similar lag characteristics
    - Excellent for identifying medium to long-term trends
    - Reduces whipsaws in choppy market conditions

    The calculation involves:
    1. If period is odd: SMA of SMA with periods (N+1)/2
    2. If period is even: SMA of SMA with periods N/2 + 1

    Parameters:
    - timeperiod: The period for TRIMA calculation (default: 30)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        trima = TRIMA(timeperiod=14)
        trima_fast = TRIMA(timeperiod=10, output_columns=["trima_fast"])
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
        self.trima_col = f"trima_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the TRIMA expression using polars_talib."""
        return Indicators.build_trima(
            source=pl.col(self.column), timeperiod=self.timeperiod
        )

    def expr(self) -> pl.Expr:
        """Return the TRIMA expression with proper column alias."""
        return self.build().alias(self.trima_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.trima_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "TRIMA expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("TRIMA requires a non-empty single output column name")

            self.trima_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for TRIMA calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable TRIMA calculation."""
        # TRIMA needs extra warmup due to double smoothing
        # Using 2x timeperiod for stable calculation
        return self.timeperiod * 2
