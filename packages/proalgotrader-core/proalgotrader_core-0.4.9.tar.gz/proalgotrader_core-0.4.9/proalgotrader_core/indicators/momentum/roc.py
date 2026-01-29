import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class ROC(Indicator):
    """
    ROC - Rate of Change

    The Rate of Change (ROC) is a momentum indicator that measures the percentage
    change in price over a specified number of periods. Unlike the simple Momentum
    indicator which calculates absolute price differences, ROC expresses the change
    as a percentage, making it ideal for comparing momentum across different
    instruments regardless of their price levels.

    ROC is calculated as the percentage difference between the current price and
    the price N periods ago. This percentage-based approach makes ROC particularly
    useful for:
    - Cross-instrument momentum comparison
    - Portfolio momentum analysis
    - Relative strength assessment
    - Normalized momentum screening

    Key characteristics:
    - Percentage-based momentum measurement
    - Oscillates around zero (no upper or lower bounds)
    - Leading indicator for trend changes
    - Excellent for divergence analysis
    - Useful for overbought/oversold identification
    - Works well across all timeframes

    The calculation formula:
    ROC = ((Current Price - Price[N periods ago]) / Price[N periods ago]) * 100

    Interpretation:
    - Positive values: Upward momentum (current price higher than N periods ago)
    - Negative values: Downward momentum (current price lower than N periods ago)
    - Zero crossings: Potential trend change signals
    - Higher absolute values: Stronger momentum
    - Values near zero: Weak momentum or consolidation

    Typical ROC ranges (vary by timeframe and instrument):
    - Strong momentum: >5% or <-5%
    - Moderate momentum: 2% to 5% or -2% to -5%
    - Weak momentum: -2% to 2%

    Common applications:
    - Momentum confirmation
    - Trend change identification
    - Divergence analysis with price
    - Overbought/oversold screening
    - Multi-timeframe momentum analysis

    Parameters:
    - timeperiod: The period for ROC calculation (default: 10)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        roc = ROC(timeperiod=10)
        roc_fast = ROC(timeperiod=5, output_columns=["roc_fast"])
        roc_slow = ROC(timeperiod=20)
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
        self.roc_col = f"roc_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the ROC expression."""
        col = pl.col(self.column)
        return 100 * (col - col.shift(self.timeperiod)) / col.shift(self.timeperiod)

    def expr(self) -> pl.Expr:
        """Return the ROC expression with proper column alias."""
        return self.build().alias(self.roc_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.roc_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "ROC expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("ROC requires a non-empty single output column name")

            self.roc_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for ROC calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable ROC calculation."""
        # ROC is simple and doesn't need much warmup beyond the timeperiod
        return self.timeperiod + 5
