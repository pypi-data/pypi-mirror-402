import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class ROCR100(Indicator):
    """
    ROCR100 - Rate of Change Ratio 100

    The Rate of Change Ratio 100 (ROCR100) is a momentum indicator that measures the
    ratio of the current price to the price N periods ago, scaled by 100. ROCR100
    provides a percentage-based perspective on momentum by calculating the ratio
    multiplied by 100, making it useful for trend analysis and momentum measurement.

    ROCR100 is calculated as the ratio of the current price to the price N periods ago,
    multiplied by 100. This approach makes ROCR100 particularly useful for:
    - Momentum trend analysis
    - Price ratio measurement with percentage scale
    - Relative performance assessment
    - Normalized momentum comparison

    Key characteristics:
    - Percentage-based momentum measurement (100 scale)
    - Oscillates around 100 (100 = no change)
    - Leading indicator for trend changes
    - Excellent for momentum analysis
    - Useful for trend strength assessment
    - Works well across all timeframes

    The calculation formula:
    ROCR100 = (Current Price / Price[N periods ago]) * 100

    Interpretation:
    - Values > 100: Upward momentum (current price higher than N periods ago)
    - Values < 100: Downward momentum (current price lower than N periods ago)
    - Value = 100: No change (current price equals N periods ago)
    - Higher values: Stronger upward momentum
    - Lower values: Stronger downward momentum

    Typical ROCR100 ranges (vary by timeframe and instrument):
    - Strong upward momentum: > 105
    - Moderate upward momentum: 102 to 105
    - Weak momentum: 98 to 102
    - Moderate downward momentum: 95 to 98
    - Strong downward momentum: < 95

    Common applications:
    - Momentum trend analysis
    - Price ratio measurement with percentage scale
    - Relative performance comparison
    - Trend strength assessment
    - Multi-timeframe momentum analysis

    Parameters:
    - timeperiod: The period for ROCR100 calculation (default: 10)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        rocr100 = ROCR100(timeperiod=10)
        rocr100_fast = ROCR100(timeperiod=5, output_columns=["rocr100_fast"])
        rocr100_slow = ROCR100(timeperiod=20)
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
        self.rocr100_col = f"rocr100_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the ROCR100 expression."""
        col = pl.col(self.column)
        return 100 * col / col.shift(self.timeperiod)

    def expr(self) -> pl.Expr:
        """Return the ROCR100 expression with proper column alias."""
        return self.build().alias(self.rocr100_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.rocr100_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "ROCR100 expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "ROCR100 requires a non-empty single output column name"
                )

            self.rocr100_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for ROCR100 calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable ROCR100 calculation."""
        # ROCR100 is simple and doesn't need much warmup beyond the timeperiod
        return self.timeperiod + 5
