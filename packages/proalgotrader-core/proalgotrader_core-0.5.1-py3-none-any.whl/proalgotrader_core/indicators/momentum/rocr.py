import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class ROCR(Indicator):
    """
    ROCR - Rate of Change Ratio

    The Rate of Change Ratio (ROCR) is a momentum indicator that measures the
    ratio of the current price to the price N periods ago. ROCR provides a
    different perspective on momentum by calculating the ratio rather than
    percentage change, making it useful for trend analysis and momentum
    measurement.

    ROCR is calculated as the ratio of the current price to the price N periods ago.
    This approach makes ROCR particularly useful for:
    - Momentum trend analysis
    - Price ratio measurement
    - Relative performance assessment
    - Normalized momentum comparison

    Key characteristics:
    - Ratio-based momentum measurement
    - Oscillates around 1.0 (1.0 = no change)
    - Leading indicator for trend changes
    - Excellent for momentum analysis
    - Useful for trend strength assessment
    - Works well across all timeframes

    The calculation formula:
    ROCR = Current Price / Price[N periods ago]

    Interpretation:
    - Values > 1.0: Upward momentum (current price higher than N periods ago)
    - Values < 1.0: Downward momentum (current price lower than N periods ago)
    - Value = 1.0: No change (current price equals N periods ago)
    - Higher values: Stronger upward momentum
    - Lower values: Stronger downward momentum

    Typical ROCR ranges (vary by timeframe and instrument):
    - Strong upward momentum: > 1.05
    - Moderate upward momentum: 1.02 to 1.05
    - Weak momentum: 0.98 to 1.02
    - Moderate downward momentum: 0.95 to 0.98
    - Strong downward momentum: < 0.95

    Common applications:
    - Momentum trend analysis
    - Price ratio measurement
    - Relative performance comparison
    - Trend strength assessment
    - Multi-timeframe momentum analysis

    Parameters:
    - timeperiod: The period for ROCR calculation (default: 10)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        rocr = ROCR(timeperiod=10)
        rocr_fast = ROCR(timeperiod=5, output_columns=["rocr_fast"])
        rocr_slow = ROCR(timeperiod=20)
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
        self.rocr_col = f"rocr_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the ROCR expression."""
        return pl.col(self.column) / pl.col(self.column).shift(self.timeperiod)

    def expr(self) -> pl.Expr:
        """Return the ROCR expression with proper column alias."""
        return self.build().alias(self.rocr_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.rocr_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "ROCR expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("ROCR requires a non-empty single output column name")

            self.rocr_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for ROCR calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable ROCR calculation."""
        # ROCR is simple and doesn't need much warmup beyond the timeperiod
        return self.timeperiod + 5
