import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class HT_TRENDMODE(Indicator):
    """
    HT_TRENDMODE - Hilbert Transform - Trend vs Cycle Mode

    The Hilbert Transform - Trend vs Cycle Mode (HT_TRENDMODE) is a trend indicator
    that uses the Hilbert Transform to determine whether the market is in a trending
    or cycling mode. This indicator is part of the Hilbert Transform family of
    indicators that provide insights into market cycles and trends.

    HT_TRENDMODE analyzes the price data using advanced mathematical transformations
    to identify the current market state. This approach makes HT_TRENDMODE particularly
    useful for:
    - Trend vs cycle identification
    - Market state analysis
    - Cycle detection
    - Trend strength assessment
    - Market regime identification

    Key characteristics:
    - Integer-based output (0 or 1)
    - No timeperiod parameter required
    - Advanced mathematical transformation
    - Excellent for market regime identification
    - Useful for trend vs cycle analysis
    - Works well across all timeframes

    The calculation formula:
    HT_TRENDMODE uses Hilbert Transform mathematical analysis to determine
    whether the market is in trending mode (1) or cycling mode (0).

    Interpretation:
    - Value = 1: Market is in trending mode
    - Value = 0: Market is in cycling mode
    - Transitions between 0 and 1: Market regime changes
    - Consistent 1 values: Strong trending market
    - Consistent 0 values: Strong cycling market

    Typical HT_TRENDMODE values:
    - Trending mode: 1
    - Cycling mode: 0
    - Mode transitions: Changes between 0 and 1

    Common applications:
    - Market regime identification
    - Trend vs cycle analysis
    - Strategy selection based on market state
    - Cycle detection and analysis
    - Trend strength assessment

    Parameters:
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        ht_trendmode = HT_TRENDMODE()
        ht_trendmode_high = HT_TRENDMODE(column='high', output_columns=['ht_trendmode_high'])
    """

    def __init__(
        self,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.column = column
        self.ht_trendmode_col = f"ht_trendmode_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the HT_TRENDMODE expression using polars_talib."""
        return Indicators.build_ht_trendmode(source=pl.col(self.column))

    def expr(self) -> pl.Expr:
        """Return the HT_TRENDMODE expression with proper column alias."""
        return self.build().alias(self.ht_trendmode_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.ht_trendmode_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "HT_TRENDMODE expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "HT_TRENDMODE requires a non-empty single output column name"
                )

            self.ht_trendmode_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for HT_TRENDMODE calculation."""
        # HT_TRENDMODE uses Hilbert Transform which typically needs a reasonable amount of data
        return 50

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable HT_TRENDMODE calculation."""
        # Hilbert Transform needs more warmup data for stable calculations
        return 100
