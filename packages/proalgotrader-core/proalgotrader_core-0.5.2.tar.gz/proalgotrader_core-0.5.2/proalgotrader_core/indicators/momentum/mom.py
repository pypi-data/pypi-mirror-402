import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class MOM(Indicator):
    """
    MOM - Momentum

    The Momentum indicator is one of the simplest and most fundamental indicators
    in technical analysis. It measures the rate of change in price over a specified
    number of periods, providing insight into the strength and speed of price movements.

    MOM is calculated as the difference between the current price and the price
    N periods ago. A positive momentum indicates that prices are rising, while
    negative momentum indicates falling prices. The magnitude of the momentum
    value reflects the speed of the price change.

    Key characteristics:
    - Simple and intuitive calculation
    - Leading indicator that can signal trend changes
    - Oscillates around zero (no upper or lower bounds)
    - Useful for identifying overbought/oversold conditions
    - Works well in trending markets
    - Can be used for divergence analysis

    The calculation is straightforward:
    MOM = Current Price - Price[N periods ago]

    Interpretation:
    - Positive values: Upward momentum (prices rising)
    - Negative values: Downward momentum (prices falling)
    - Zero crossings: Potential trend change signals
    - Increasing absolute values: Accelerating momentum
    - Decreasing absolute values: Momentum slowing down

    Common applications:
    - Trend confirmation
    - Divergence analysis (price vs momentum)
    - Overbought/oversold identification
    - Entry/exit signal generation
    - Momentum-based filtering

    Parameters:
    - timeperiod: The period for momentum calculation (default: 10)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        mom = MOM(timeperiod=10)
        mom_fast = MOM(timeperiod=5, output_columns=["momentum_fast"])
        mom_slow = MOM(timeperiod=20)
    """

    def __init__(
        self,
        timeperiod: int = 10,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.column = column
        self.mom_col = f"mom_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the MOM expression."""
        return pl.col(self.column) - pl.col(self.column).shift(self.timeperiod)

    def expr(self) -> pl.Expr:
        """Return the MOM expression with proper column alias."""
        return self.build().alias(self.mom_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.mom_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "MOM expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("MOM requires a non-empty single output column name")

            self.mom_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for MOM calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable MOM calculation."""
        # MOM is simple and doesn't need much warmup beyond the timeperiod
        return self.timeperiod + 5
