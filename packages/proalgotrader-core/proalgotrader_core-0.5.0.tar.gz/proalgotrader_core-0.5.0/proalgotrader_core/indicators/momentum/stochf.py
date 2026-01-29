import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class STOCHF(Indicator):
    """
    STOCHF - Stochastic Fast

    The Stochastic Fast (STOCHF) is a momentum oscillator that compares the closing
    price to the high-low range over a specific period. It's the "fast" version of
    the Stochastic oscillator, providing quicker signals by using the raw %K and
    smoothed %D without additional smoothing that the regular Stochastic applies.

    STOCHF generates two lines:
    - FastK: The raw stochastic value (similar to %K in regular Stochastic)
    - FastD: A smoothed version of FastK (moving average of FastK)

    The key difference from regular Stochastic is that STOCHF eliminates the
    additional smoothing step, making it more responsive to price changes but
    also more volatile. This makes it excellent for:
    - Quick reversal signals
    - Short-term trading
    - Early overbought/oversold detection
    - Fast trend change identification

    Key characteristics:
    - Range: 0 to 100
    - More sensitive than regular Stochastic
    - Two output lines: FastK and FastD
    - Excellent for short-term signals
    - Higher frequency of signals
    - More prone to false signals (trade-off for speed)

    Calculation:
    - FastK = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
    - FastD = Moving Average of FastK over fastd_period

    Interpretation:
    - Values > 80: Potentially overbought condition
    - Values < 20: Potentially oversold condition
    - FastK crossing above FastD: Potential bullish signal
    - FastK crossing below FastD: Potential bearish signal
    - Divergences: Price vs STOCHF divergences signal potential reversals

    Parameters:
    - fastk_period: Period for FastK calculation (default: 5)
    - fastd_period: Period for FastD smoothing (default: 3)
    - fastd_matype: Moving average type for FastD (default: 0 = SMA)
    - output_columns: Optional list to override default output column names

    Example:
        stochf = STOCHF(fastk_period=5, fastd_period=3)
        stochf_custom = STOCHF(fastk_period=8, fastd_period=5, output_columns=["fast_k", "fast_d"])
    """

    def __init__(
        self,
        fastk_period: int = 5,
        fastd_period: int = 3,
        fastd_matype: int = 0,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.fastk_period = fastk_period
        self.fastd_period = fastd_period
        self.fastd_matype = fastd_matype
        self.fastk_col = f"fastk_{fastk_period}_{fastd_period}"
        self.fastd_col = f"fastd_{fastk_period}_{fastd_period}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the STOCHF expression using polars_talib."""
        return Indicators.build_stochf(
            high=pl.col("high"),
            low=pl.col("low"),
            close=pl.col("close"),
            fastk_period=self.fastk_period,
            fastd_period=self.fastd_period,
            fastd_matype=self.fastd_matype,
        )

    def expr(self) -> pl.Expr:
        """Return the STOCHF expression with proper column aliases."""
        # STOCHF returns a struct with 'fastk' and 'fastd' fields
        stochf_expr = self.build()
        return pl.struct(
            [
                stochf_expr.struct.field("fastk").alias(self.fastk_col),
                stochf_expr.struct.field("fastd").alias(self.fastd_col),
            ]
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        stochf_expr = self.build()
        return [
            stochf_expr.struct.field("fastk").alias(self.fastk_col),
            stochf_expr.struct.field("fastd").alias(self.fastd_col),
        ]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.fastk_col, self.fastd_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return ["high", "low", "close"]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 2:
                raise ValueError(
                    "STOCHF expects exactly 2 output column names in 'output_columns' (fastk, fastd)"
                )

            fastk_name = self._requested_output_columns[0]
            fastd_name = self._requested_output_columns[1]

            if not isinstance(fastk_name, str) or not fastk_name:
                raise ValueError(
                    "STOCHF requires a non-empty string for FastK column name"
                )
            if not isinstance(fastd_name, str) or not fastd_name:
                raise ValueError(
                    "STOCHF requires a non-empty string for FastD column name"
                )

            self.fastk_col = fastk_name
            self.fastd_col = fastd_name

    def window_size(self) -> int:
        """Return the minimum window size needed for STOCHF calculation."""
        return max(self.fastk_period, self.fastd_period)

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable STOCHF calculation."""
        # STOCHF needs warmup for both FastK and FastD calculations
        return max(self.fastk_period, self.fastd_period) * 2
