import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class AROONOSC(Indicator):
    """
    AROONOSC - Aroon Oscillator

    The Aroon Oscillator is a momentum indicator derived from the Aroon indicator
    that measures the strength and direction of trends by calculating the difference
    between Aroon Up and Aroon Down. It simplifies the dual-line Aroon indicator
    into a single oscillator that fluctuates between -100 and +100.

    The Aroon Oscillator is calculated as:
    AROONOSC = Aroon Up - Aroon Down

    Where:
    - Aroon Up measures how long it has been since the highest high within the period
    - Aroon Down measures how long it has been since the lowest low within the period

    Key characteristics:
    - Range: -100 to +100
    - Positive values: Uptrend dominance (recent highs)
    - Negative values: Downtrend dominance (recent lows)
    - Zero line crossings: Potential trend change signals
    - Extreme values indicate strong trend momentum
    - Values near zero suggest consolidation or weak trends

    Interpretation:
    - Values > +50: Strong uptrend (Aroon Up dominating)
    - Values > +25: Moderate uptrend
    - Values -25 to +25: Consolidation/ranging market
    - Values < -25: Moderate downtrend
    - Values < -50: Strong downtrend (Aroon Down dominating)

    The oscillator format makes it easier to:
    - Identify trend strength at a glance
    - Spot divergences between price and momentum
    - Generate clear buy/sell signals on zero crossings
    - Filter trades based on trend strength thresholds
    - Combine with other oscillators for confirmation

    Advantages over regular Aroon:
    - Single line instead of two (easier to read)
    - Clear zero-line reference for trend direction
    - Better for systematic trading rules
    - Easier divergence analysis
    - More compact display on charts

    Common applications:
    - Trend direction confirmation
    - Trend strength measurement
    - Divergence analysis
    - Entry/exit signal generation
    - Market regime identification

    Parameters:
    - timeperiod: The period for Aroon calculation (default: 14)
    - output_columns: Optional list to override default output column names

    Example:
        aroonosc = AROONOSC(timeperiod=14)
        aroonosc_fast = AROONOSC(timeperiod=7, output_columns=["aroon_osc"])
        aroonosc_slow = AROONOSC(timeperiod=25)
    """

    def __init__(
        self,
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.aroonosc_col = f"aroonosc_{timeperiod}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the AROONOSC expression using polars_talib."""
        return Indicators.build_aroonosc(
            high=pl.col("high"),
            low=pl.col("low"),
            timeperiod=self.timeperiod,
        )

    def expr(self) -> pl.Expr:
        """Return the AROONOSC expression with proper column alias."""
        return self.build().alias(self.aroonosc_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.aroonosc_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return ["high", "low"]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "AROONOSC expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "AROONOSC requires a non-empty single output column name"
                )

            self.aroonosc_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for AROONOSC calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable AROONOSC calculation."""
        # AROONOSC needs warmup to identify highest highs and lowest lows
        # Using 2x timeperiod for stable calculation
        return self.timeperiod * 2
