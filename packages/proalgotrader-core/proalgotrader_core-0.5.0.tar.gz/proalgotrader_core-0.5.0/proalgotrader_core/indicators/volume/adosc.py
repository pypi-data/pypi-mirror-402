import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class ADOSC(Indicator):
    """
    ADOSC - Chaikin A/D Oscillator

    The Chaikin A/D Oscillator (Accumulation/Distribution Oscillator) is a volume indicator
    that measures the difference between two exponential moving averages of the A/D Line.
    It combines price and volume to show momentum changes in money flow, helping to identify
    potential trend reversals and momentum shifts.

    The A/D Oscillator is calculated by taking the difference between a fast and slow
    exponential moving average of the A/D Line. This approach makes ADOSC particularly useful for:
    - Volume momentum analysis
    - Trend reversal detection
    - Money flow momentum measurement
    - Divergence analysis
    - Accumulation/distribution momentum

    Key characteristics:
    - Volume-based momentum indicator
    - Uses fastperiod and slowperiod parameters
    - Combines price and volume data
    - Excellent for momentum analysis
    - Useful for trend reversal detection
    - Works well across all timeframes

    The calculation formula:
    A/D Line = Cumulative sum of Money Flow Volume
    ADOSC = EMA(A/D Line, fastperiod) - EMA(A/D Line, slowperiod)
    Where Money Flow Volume = ((Close - Low) - (High - Close)) / (High - Low) * Volume

    Interpretation:
    - Positive ADOSC: Accumulation momentum (buying pressure increasing)
    - Negative ADOSC: Distribution momentum (selling pressure increasing)
    - Rising ADOSC: Increasing accumulation momentum
    - Falling ADOSC: Increasing distribution momentum
    - ADOSC divergence with price: Potential trend reversal
    - ADOSC crossing zero: Momentum shift

    Typical ADOSC patterns:
    - Rising ADOSC with rising price: Strong bullish momentum
    - Falling ADOSC with falling price: Strong bearish momentum
    - Rising ADOSC with falling price: Bullish divergence
    - Falling ADOSC with rising price: Bearish divergence
    - ADOSC crossing above zero: Bullish momentum shift
    - ADOSC crossing below zero: Bearish momentum shift

    Common applications:
    - Volume momentum analysis
    - Trend reversal detection
    - Money flow momentum measurement
    - Divergence analysis
    - Accumulation/distribution momentum

    Parameters:
    - high_column: The high price column name (default: "high")
    - low_column: The low price column name (default: "low")
    - close_column: The close price column name (default: "close")
    - volume_column: The volume column name (default: "volume")
    - fastperiod: Fast EMA period (default: 3)
    - slowperiod: Slow EMA period (default: 10)
    - output_columns: Optional list to override default output column names

    Example:
        adosc = ADOSC()
        adosc_custom = ADOSC(fastperiod=5, slowperiod=15)
    """

    def __init__(
        self,
        high_column: str = "high",
        low_column: str = "low",
        close_column: str = "close",
        volume_column: str = "volume",
        fastperiod: int = 3,
        slowperiod: int = 10,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.volume_column = volume_column
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.adosc_col = f"adosc_{fastperiod}_{slowperiod}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the ADOSC expression using polars_talib."""
        return Indicators.build_adosc(
            high=pl.col(self.high_column),
            low=pl.col(self.low_column),
            close=pl.col(self.close_column),
            volume=pl.col(self.volume_column),
            fastperiod=self.fastperiod,
            slowperiod=self.slowperiod,
        )

    def expr(self) -> pl.Expr:
        """Return the ADOSC expression with proper column alias."""
        return self.build().alias(self.adosc_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.adosc_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [
            self.high_column,
            self.low_column,
            self.close_column,
            self.volume_column,
        ]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "ADOSC expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("ADOSC requires a non-empty single output column name")

            self.adosc_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for ADOSC calculation."""
        # ADOSC needs enough data for both fast and slow EMAs
        return max(self.fastperiod, self.slowperiod)

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable ADOSC calculation."""
        # ADOSC needs more warmup for stable EMA calculations
        return max(self.fastperiod, self.slowperiod) * 3
