import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class BOP(Indicator):
    """
    BOP - Balance of Power

    The Balance of Power (BOP) indicator measures the strength of buyers versus
    sellers by evaluating the ability of each to push prices to extreme levels.
    It analyzes the relationship between the closing price and the trading range
    (high-low spread) to determine market sentiment and momentum.

    The Balance of Power is calculated as:
    BOP = (Close - Open) / (High - Low)

    When Open is not available, some implementations use:
    BOP = (Close - Low) - (High - Close) / (High - Low)

    Key characteristics:
    - Range: -1 to +1 (when using Close-Open formula)
    - Values near +1: Strong buying pressure (close near high)
    - Values near -1: Strong selling pressure (close near low)
    - Values near 0: Balanced buying/selling or indecision
    - No smoothing applied (raw calculation)
    - Requires OHLC data for accurate calculation

    The BOP indicator is particularly useful for:
    - Identifying the relative strength of buyers vs sellers
    - Confirming price movements with underlying momentum
    - Spotting divergences between price and buying/selling pressure
    - Determining market sentiment at key levels
    - Validating breakouts and trend changes

    Interpretation:
    - BOP > 0.5: Strong buying pressure, bullish sentiment
    - BOP > 0: Moderate buying pressure, buyers in control
    - BOP = 0: Neutral, balanced market
    - BOP < 0: Moderate selling pressure, sellers in control
    - BOP < -0.5: Strong selling pressure, bearish sentiment

    Common applications:
    - Trend confirmation: BOP direction should align with price trend
    - Divergence analysis: Price vs BOP divergences signal potential reversals
    - Support/resistance validation: Strong BOP at key levels confirms significance
    - Momentum confirmation: Rising BOP confirms upward momentum
    - Market sentiment gauge: Overall BOP levels indicate market mood

    Advantages:
    - Simple and intuitive calculation
    - Provides clear buy/sell pressure readings
    - Works well in trending markets
    - Excellent for divergence analysis
    - No lag (uses current period data)

    Limitations:
    - Can be noisy in sideways markets
    - Requires OHLC data (not just closing prices)
    - May give false signals in low-volume periods
    - Works best when combined with other indicators

    Parameters:
    - output_columns: Optional list to override default output column names

    Example:
        bop = BOP()
        bop_custom = BOP(output_columns=["balance_of_power"])
    """

    def __init__(
        self,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.bop_col = "bop"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the BOP expression."""
        return (pl.col("close") - pl.col("open")) / (pl.col("high") - pl.col("low"))

    def expr(self) -> pl.Expr:
        """Return the BOP expression with proper column alias."""
        return self.build().alias(self.bop_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.bop_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return ["open", "high", "low", "close"]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "BOP expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("BOP requires a non-empty single output column name")

            self.bop_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for BOP calculation."""
        return 1  # BOP only needs current period data

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable BOP calculation."""
        return 1  # BOP is calculated per period, no warmup needed
