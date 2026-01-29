import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class NATR(Indicator):
    """
    NATR - Normalized Average True Range

    The Normalized Average True Range (NATR) is a volatility indicator that expresses
    the Average True Range (ATR) as a percentage of the closing price. This normalization
    makes NATR particularly useful for comparing volatility across different instruments
    or time periods, regardless of their absolute price levels.

    NATR is calculated by dividing the ATR by the closing price and multiplying by 100
    to get a percentage. This allows traders to:
    - Compare volatility across different stocks or instruments
    - Identify when volatility is unusually high or low relative to price
    - Use consistent volatility thresholds across different markets
    - Analyze volatility patterns independent of price level

    Key characteristics:
    - Percentage-based volatility measurement (0-100+ range)
    - Price-independent volatility comparison
    - Useful for position sizing based on volatility
    - Excellent for screening instruments by volatility
    - Helps identify breakout and consolidation periods

    The calculation involves:
    1. Calculate True Range for each period
    2. Apply exponential moving average to get ATR
    3. Divide ATR by closing price and multiply by 100

    Typical NATR values:
    - Low volatility: 0.5% - 2%
    - Normal volatility: 2% - 5%
    - High volatility: 5% - 10%
    - Very high volatility: 10%+

    Parameters:
    - timeperiod: The period for NATR calculation (default: 14)
    - output_columns: Optional list to override default output column names

    Example:
        natr = NATR(timeperiod=14)
        natr_short = NATR(timeperiod=7, output_columns=["natr_fast"])
        natr_long = NATR(timeperiod=21)
    """

    def __init__(
        self,
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.natr_col = f"natr_{timeperiod}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the NATR expression."""
        # Calculate True Range
        high = pl.col("high")
        low = pl.col("low")
        close = pl.col("close")

        hl = high - low
        hc = (high - close.shift(1)).abs()
        lc = (low - close.shift(1)).abs()
        tr = pl.max_horizontal(hl, hc, lc)

        # Calculate EMA of True Range (ATR)
        alpha = 2.0 / (self.timeperiod + 1)
        atr_val = tr.ewm_mean(alpha=alpha, adjust=False)

        # Return NATR as percentage
        return 100 * atr_val / close

    def expr(self) -> pl.Expr:
        """Return the NATR expression with proper column alias."""
        return self.build().alias(self.natr_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.natr_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return ["high", "low", "close"]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "NATR expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("NATR requires a non-empty single output column name")

            self.natr_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for NATR calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable NATR calculation."""
        # NATR needs extra warmup for stable ATR calculation
        # Using 2x timeperiod for reliable results
        return self.timeperiod * 2
