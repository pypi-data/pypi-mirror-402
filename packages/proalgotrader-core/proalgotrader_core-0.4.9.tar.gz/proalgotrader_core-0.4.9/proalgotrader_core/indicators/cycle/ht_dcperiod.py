import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class HT_DCPERIOD(Indicator):
    """
    HT_DCPERIOD - Hilbert Transform - Dominant Cycle Period

    The Hilbert Transform - Dominant Cycle Period (HT_DCPERIOD) is a cycle indicator
    that uses the Hilbert Transform to identify the dominant cycle period in price data.
    This indicator is part of the Hilbert Transform family of indicators that provide
    insights into market cycles and their characteristics.

    HT_DCPERIOD analyzes the price data using advanced mathematical transformations
    to identify the most significant cycle period. This approach makes HT_DCPERIOD
    particularly useful for:
    - Cycle period identification
    - Market cycle analysis
    - Cycle-based trading strategies
    - Period optimization
    - Market regime identification

    Key characteristics:
    - Real-valued output (cycle period in time units)
    - No timeperiod parameter required
    - Advanced mathematical transformation
    - Excellent for cycle analysis
    - Useful for period identification
    - Works well across all timeframes

    The calculation formula:
    HT_DCPERIOD uses Hilbert Transform mathematical analysis to determine
    the dominant cycle period in the price data. The output represents
    the period length of the most significant cycle.

    Interpretation:
    - Higher values: Longer dominant cycles
    - Lower values: Shorter dominant cycles
    - Stable values: Consistent cycle periods
    - Changing values: Cycle period transitions
    - Values around 20-30: Common market cycles
    - Values above 50: Long-term cycles
    - Values below 10: Short-term cycles

    Typical HT_DCPERIOD values:
    - Short cycles: 5-15 periods
    - Medium cycles: 15-30 periods
    - Long cycles: 30+ periods
    - Market cycles: 20-25 periods (common)

    Common applications:
    - Cycle period identification
    - Market cycle analysis
    - Period-based strategy optimization
    - Cycle detection and analysis
    - Market regime identification

    Parameters:
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        ht_dcperiod = HT_DCPERIOD()
        ht_dcperiod_high = HT_DCPERIOD(column='high', output_columns=['ht_dcperiod_high'])
    """

    def __init__(
        self,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.column = column
        self.ht_dcperiod_col = f"ht_dcperiod_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the HT_DCPERIOD expression using polars_talib."""
        return Indicators.build_ht_dcperiod(source=pl.col(self.column))

    def expr(self) -> pl.Expr:
        """Return the HT_DCPERIOD expression with proper column alias."""
        return self.build().alias(self.ht_dcperiod_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.ht_dcperiod_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "HT_DCPERIOD expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "HT_DCPERIOD requires a non-empty single output column name"
                )

            self.ht_dcperiod_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for HT_DCPERIOD calculation."""
        # HT_DCPERIOD uses Hilbert Transform which typically needs a reasonable amount of data
        return 50

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable HT_DCPERIOD calculation."""
        # Hilbert Transform needs more warmup data for stable calculations
        return 100
