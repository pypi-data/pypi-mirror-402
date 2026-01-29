import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class CMO(Indicator):
    """
    CMO - Chande Momentum Oscillator

    The Chande Momentum Oscillator (CMO) is a momentum indicator developed by
    Tushar Chande that measures the momentum of a security by calculating the
    difference between the sum of gains and the sum of losses over a specified
    period, then normalizing the result to oscillate between -100 and +100.

    The CMO is calculated as:
    CMO = 100 * (Sum of Gains - Sum of Losses) / (Sum of Gains + Sum of Losses)

    Where:
    - Sum of Gains = Sum of positive price changes over the period
    - Sum of Losses = Sum of negative price changes over the period (absolute values)

    Key characteristics:
    - Range: -100 to +100 (bounded oscillator)
    - Unsmoothed momentum indicator (more sensitive than RSI)
    - Uses actual price changes rather than exponential smoothing
    - Excellent for identifying overbought/oversold conditions
    - Superior to RSI in certain market conditions

    The CMO differs from RSI in several important ways:
    1. Uses simple moving sums instead of exponential smoothing
    2. More sensitive to recent price changes
    3. Provides clearer signals in trending markets
    4. Less prone to false signals in strong trends
    5. Better at identifying momentum shifts

    Interpretation:
    - CMO > +50: Strong upward momentum, potentially overbought
    - CMO > 0: Bullish momentum, uptrend in progress
    - CMO = 0: Neutral momentum, market balance
    - CMO < 0: Bearish momentum, downtrend in progress
    - CMO < -50: Strong downward momentum, potentially oversold

    Common applications:
    - Overbought/oversold identification (±50 levels)
    - Momentum confirmation for trend analysis
    - Divergence analysis between price and momentum
    - Entry/exit signal generation on zero line crossings
    - Market regime identification (trending vs ranging)

    Trading signals:
    - CMO crossing above 0: Potential bullish signal
    - CMO crossing below 0: Potential bearish signal
    - CMO above +50: Consider taking profits on long positions
    - CMO below -50: Consider taking profits on short positions
    - Divergences: Price vs CMO divergences signal potential reversals

    Advantages over RSI:
    - More responsive to price changes
    - Clearer signals in trending markets
    - Better momentum measurement in volatile conditions
    - Less smoothing means fewer false signals in trends
    - More accurate extreme readings

    Limitations:
    - Can be choppy in sideways markets
    - May generate more false signals than smoothed indicators
    - Requires careful parameter selection for different timeframes
    - Best used with trend confirmation tools

    Parameters:
    - timeperiod: The period for CMO calculation (default: 14)
    - column: The price column to use (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        cmo = CMO(timeperiod=14)
        cmo_fast = CMO(timeperiod=9, output_columns=["cmo_fast"])
        cmo_custom = CMO(timeperiod=21, column="typical_price")
    """

    def __init__(
        self,
        timeperiod: int = 14,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.column = column
        self.cmo_col = f"cmo_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the CMO expression using polars_talib."""
        return Indicators.build_cmo(
            source=pl.col(self.column),
            timeperiod=self.timeperiod,
        )

    def expr(self) -> pl.Expr:
        """Return the CMO expression with proper column alias."""
        return self.build().alias(self.cmo_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.cmo_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "CMO expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("CMO requires a non-empty single output column name")

            self.cmo_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for CMO calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable CMO calculation."""
        # CMO needs warmup to accumulate gains and losses
        # Using 2x timeperiod for stable calculation
        return self.timeperiod * 2
