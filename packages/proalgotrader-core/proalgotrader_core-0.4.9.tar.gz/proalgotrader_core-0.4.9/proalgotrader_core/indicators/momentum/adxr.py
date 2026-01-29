import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class ADXR(Indicator):
    """
    ADXR - Average Directional Movement Index Rating

    The Average Directional Movement Index Rating (ADXR) is an enhanced version
    of the ADX indicator that provides smoother and more stable trend strength
    measurements. ADXR is calculated by taking the average of the current ADX
    and the ADX from a specified number of periods ago.

    ADXR was developed to reduce the volatility of the standard ADX while
    maintaining its effectiveness in measuring trend strength. By averaging
    current and historical ADX values, ADXR provides a more stable reading
    that's less prone to sudden spikes and drops.

    Key characteristics:
    - Smoother trend strength measurement than standard ADX
    - Reduces false signals from ADX volatility
    - Better for identifying sustained trend strength
    - Range: 0-100 (same as ADX)
    - More reliable for trend-following strategies

    The calculation involves:
    1. Calculate ADX for the specified period
    2. Take the ADX value from N periods ago
    3. Average current ADX with historical ADX: ADXR = (ADX + ADX[N]) / 2

    ADXR Interpretation (same thresholds as ADX):
    - Weak trend: 0-25 (ranging/sideways market)
    - Moderate trend: 25-50 (developing trend)
    - Strong trend: 50-75 (well-established trend)
    - Very strong trend: 75-100 (powerful trending market)

    Parameters:
    - timeperiod: The period for ADXR calculation (default: 14)
    - output_columns: Optional list to override default output column names

    Example:
        adxr = ADXR(timeperiod=14)
        adxr_fast = ADXR(timeperiod=7, output_columns=["adxr_fast"])
        adxr_long = ADXR(timeperiod=21)
    """

    def __init__(
        self,
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.adxr_col = f"adxr_{timeperiod}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the ADXR expression using polars_talib."""
        return Indicators.build_adxr(
            high=pl.col("high"),
            low=pl.col("low"),
            close=pl.col("close"),
            timeperiod=self.timeperiod,
        )

    def expr(self) -> pl.Expr:
        """Return the ADXR expression with proper column alias."""
        return self.build().alias(self.adxr_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.adxr_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return ["high", "low", "close"]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "ADXR expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("ADXR requires a non-empty single output column name")

            self.adxr_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for ADXR calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable ADXR calculation."""
        # ADXR needs significant warmup due to ADX calculation complexity
        # and the need for historical ADX values for averaging
        # Using 3x timeperiod for stable calculation
        return self.timeperiod * 3
