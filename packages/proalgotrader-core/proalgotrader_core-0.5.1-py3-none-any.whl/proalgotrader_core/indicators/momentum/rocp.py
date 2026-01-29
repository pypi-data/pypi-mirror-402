import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class ROCP(Indicator):
    """
    ROCP - Rate of Change Percentage

    The Rate of Change Percentage (ROCP) is a momentum indicator that measures the
    percentage change in price over a specified number of periods. ROCP is similar
    to ROC but provides a different perspective on momentum by calculating the
    percentage change as a ratio rather than a percentage.

    ROCP is calculated as the ratio of the current price to the price N periods ago,
    expressed as a percentage. This approach makes ROCP particularly useful for:
    - Momentum trend analysis
    - Price change measurement
    - Relative performance assessment
    - Normalized momentum comparison

    Key characteristics:
    - Percentage-based momentum measurement
    - Oscillates around 100 (100% = no change)
    - Leading indicator for trend changes
    - Excellent for momentum analysis
    - Useful for trend strength assessment
    - Works well across all timeframes

    The calculation formula:
    ROCP = (Current Price / Price[N periods ago]) * 100

    Interpretation:
    - Values > 100: Upward momentum (current price higher than N periods ago)
    - Values < 100: Downward momentum (current price lower than N periods ago)
    - Value = 100: No change (current price equals N periods ago)
    - Higher values: Stronger upward momentum
    - Lower values: Stronger downward momentum

    Typical ROCP ranges (vary by timeframe and instrument):
    - Strong upward momentum: > 105%
    - Moderate upward momentum: 102% to 105%
    - Weak momentum: 98% to 102%
    - Moderate downward momentum: 95% to 98%
    - Strong downward momentum: < 95%

    Common applications:
    - Momentum trend analysis
    - Price change measurement
    - Relative performance comparison
    - Trend strength assessment
    - Multi-timeframe momentum analysis

    Parameters:
    - timeperiod: The period for ROCP calculation (default: 10)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        rocp = ROCP(timeperiod=10)
        rocp_fast = ROCP(timeperiod=5, output_columns=["rocp_fast"])
        rocp_slow = ROCP(timeperiod=20)
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
        self.rocp_col = f"rocp_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the ROCP expression."""
        col = pl.col(self.column)
        return (col - col.shift(self.timeperiod)) / col.shift(self.timeperiod)

    def expr(self) -> pl.Expr:
        """Return the ROCP expression with proper column alias."""
        return self.build().alias(self.rocp_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.rocp_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "ROCP expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("ROCP requires a non-empty single output column name")

            self.rocp_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for ROCP calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable ROCP calculation."""
        # ROCP is simple and doesn't need much warmup beyond the timeperiod
        return self.timeperiod + 5
