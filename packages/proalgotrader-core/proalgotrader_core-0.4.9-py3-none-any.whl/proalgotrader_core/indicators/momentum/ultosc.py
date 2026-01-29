import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class ULTOSC(Indicator):
    """
    ULTOSC - Ultimate Oscillator

    The Ultimate Oscillator is a momentum oscillator developed by Larry Williams
    that combines short-term, medium-term, and long-term price movements into a
    single oscillator to reduce the false signals that are common with single
    timeframe oscillators. It addresses the key weakness of most momentum
    oscillators - their tendency to give false signals during strong trends.

    The Ultimate Oscillator is calculated using three different timeframes:
    1. Short-term period (default: 7)
    2. Medium-term period (default: 14)
    3. Long-term period (default: 28)

    Formula:
    UO = 100 * ((4 * Average7) + (2 * Average14) + Average28) / (4 + 2 + 1)

    Where:
    - Average7 = Sum of (Close - True Low) over 7 periods / Sum of (True Range) over 7 periods
    - Average14 = Sum of (Close - True Low) over 14 periods / Sum of (True Range) over 14 periods
    - Average28 = Sum of (Close - True Low) over 28 periods / Sum of (True Range) over 28 periods

    And:
    - True Low = Min(Low, Previous Close)
    - True Range = Max(High, Previous Close) - Min(Low, Previous Close)

    Key characteristics:
    - Range: 0 to 100 (bounded oscillator)
    - Multi-timeframe approach reduces false signals
    - Weighted combination favors shorter timeframes (4:2:1 ratio)
    - Uses True Range for better volatility adjustment
    - Excellent for trend confirmation and divergence analysis

    The Ultimate Oscillator's multi-timeframe approach provides several advantages:
    - Reduces whipsaws common in single-period oscillators
    - Provides more reliable overbought/oversold readings
    - Better trend confirmation through multiple timeframe consensus
    - Fewer false breakout signals
    - More stable during volatile market conditions

    Interpretation:
    - UO > 70: Potentially overbought condition
    - UO > 50: Bullish momentum, above midpoint
    - UO = 50: Neutral momentum
    - UO < 50: Bearish momentum, below midpoint
    - UO < 30: Potentially oversold condition

    Larry Williams' trading rules:
    1. Buy signal: UO above 50, divergence with price, and UO above previous swing high
    2. Sell signal: UO below 50, divergence with price, and UO below previous swing low
    3. Confirmation: Multiple timeframes showing same direction

    Common applications:
    - Overbought/oversold identification (30/70 levels)
    - Divergence analysis between UO and price
    - Trend confirmation across multiple timeframes
    - Entry/exit signal generation
    - Market strength measurement

    Trading signals:
    - UO crossing above 50: Potential bullish momentum
    - UO crossing below 50: Potential bearish momentum
    - UO above 70: Consider taking profits on long positions
    - UO below 30: Consider taking profits on short positions
    - Divergences: Price vs UO divergences signal potential reversals

    Advantages over single-timeframe oscillators:
    - Reduced false signals through multi-timeframe analysis
    - Better trend identification
    - More reliable extreme readings
    - Superior divergence signals
    - Less susceptible to market noise

    Limitations:
    - More complex calculation than simple oscillators
    - Can be slow to react to sudden market changes
    - Requires understanding of multi-timeframe analysis
    - May give fewer signals than faster oscillators

    Parameters:
    - timeperiod1: Short-term period (default: 7)
    - timeperiod2: Medium-term period (default: 14)
    - timeperiod3: Long-term period (default: 28)
    - output_columns: Optional list to override default output column names

    Example:
        ultosc = ULTOSC()  # Default periods: 7, 14, 28
        ultosc_fast = ULTOSC(timeperiod1=5, timeperiod2=10, timeperiod3=20)
        ultosc_custom = ULTOSC(timeperiod1=7, timeperiod2=14, timeperiod3=28, output_columns=["ultimate_osc"])
    """

    def __init__(
        self,
        timeperiod1: int = 7,
        timeperiod2: int = 14,
        timeperiod3: int = 28,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod1 = timeperiod1
        self.timeperiod2 = timeperiod2
        self.timeperiod3 = timeperiod3
        self.ultosc_col = f"ultosc_{timeperiod1}_{timeperiod2}_{timeperiod3}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the ULTOSC expression using polars_talib."""
        return Indicators.build_ultosc(
            high=pl.col("high"),
            low=pl.col("low"),
            close=pl.col("close"),
            timeperiod1=self.timeperiod1,
            timeperiod2=self.timeperiod2,
            timeperiod3=self.timeperiod3,
        )

    def expr(self) -> pl.Expr:
        """Return the ULTOSC expression with proper column alias."""
        return self.build().alias(self.ultosc_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.ultosc_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return ["high", "low", "close"]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "ULTOSC expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "ULTOSC requires a non-empty single output column name"
                )

            self.ultosc_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for ULTOSC calculation."""
        return max(self.timeperiod1, self.timeperiod2, self.timeperiod3)

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable ULTOSC calculation."""
        # ULTOSC uses multiple timeframes, need warmup for longest period
        # Using 2x longest period for stable calculation
        return max(self.timeperiod1, self.timeperiod2, self.timeperiod3) * 2
