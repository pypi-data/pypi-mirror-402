import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class TRIX(Indicator):
    """
    TRIX - Triple Exponential Average

    TRIX is a momentum oscillator that displays the percent rate of change of a
    triple exponentially smoothed moving average. It was developed by Jack Hutson
    to filter out price movements that are considered insignificant. TRIX is an
    excellent indicator for detecting trends and generating buy/sell signals.

    The TRIX calculation involves three steps:
    1. Calculate the first EMA of the closing price
    2. Calculate the second EMA using the first EMA as input
    3. Calculate the third EMA using the second EMA as input
    4. TRIX = Percent change of the third EMA

    TRIX = ((EMA3[today] - EMA3[yesterday]) / EMA3[yesterday]) * 10000

    Key characteristics:
    - Range: Unbounded (but typically oscillates around zero)
    - Zero line crossings indicate trend changes
    - Positive values suggest upward momentum
    - Negative values suggest downward momentum
    - Triple smoothing reduces false signals
    - Excellent for trend identification

    The triple exponential smoothing provides several advantages:
    - Filters out market noise effectively
    - Reduces whipsaws and false signals
    - Provides clearer trend direction
    - Works well in both trending and sideways markets
    - Less sensitive to short-term price fluctuations

    Interpretation:
    - TRIX crossing above zero: Potential bullish signal
    - TRIX crossing below zero: Potential bearish signal
    - Rising TRIX: Increasing upward momentum
    - Falling TRIX: Increasing downward momentum
    - TRIX divergence from price: Potential trend reversal

    Common applications:
    - Trend identification and confirmation
    - Signal generation on zero line crossings
    - Divergence analysis between TRIX and price
    - Momentum confirmation for other indicators
    - Long-term trend analysis (works well on higher timeframes)

    Trading signals:
    - Buy signal: TRIX crosses above zero line
    - Sell signal: TRIX crosses below zero line
    - Trend confirmation: TRIX direction aligns with price trend
    - Divergence signals: TRIX direction opposes price direction

    Advantages:
    - Excellent noise reduction through triple smoothing
    - Clear trend direction signals
    - Fewer false signals compared to other oscillators
    - Works well across different timeframes
    - Simple interpretation (zero line crossings)

    Limitations:
    - Significant lag due to triple smoothing
    - May miss short-term opportunities
    - Requires patience for signal confirmation
    - Best used with other indicators for entry timing

    Parameters:
    - timeperiod: The period for exponential moving average calculation (default: 30)
    - column: The price column to use (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        trix = TRIX(timeperiod=30)
        trix_fast = TRIX(timeperiod=14, output_columns=["trix_fast"])
        trix_custom = TRIX(timeperiod=50, column="typical_price")
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
        self.trix_col = f"trix_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the TRIX expression."""
        source = pl.col(self.column)
        alpha = 2.0 / (self.timeperiod + 1)

        # Triple EMA smoothing
        ema1 = source.ewm_mean(alpha=alpha, adjust=False)
        ema2 = ema1.ewm_mean(alpha=alpha, adjust=False)
        ema3 = ema2.ewm_mean(alpha=alpha, adjust=False)

        # Calculate percent rate of change (scaled by 10000)
        return 10000 * (ema3 - ema3.shift(1)) / ema3.shift(1)

    def expr(self) -> pl.Expr:
        """Return the TRIX expression with proper column alias."""
        return self.build().alias(self.trix_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.trix_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "TRIX expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("TRIX requires a non-empty single output column name")

            self.trix_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for TRIX calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable TRIX calculation."""
        # TRIX uses triple exponential smoothing, requiring extensive warmup
        # Using 4x timeperiod for stable triple EMA calculation
        return self.timeperiod * 4
