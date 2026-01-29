import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class MAMA(Indicator):
    """
    MAMA - MESA Adaptive Moving Average

    The MESA Adaptive Moving Average (MAMA) is a sophisticated technical indicator
    developed by John Ehlers that uses the Hilbert Transform to automatically adapt
    to market cycles and price changes. MAMA provides two output lines:
    - MAMA: The main adaptive moving average
    - FAMA: Following Adaptive Moving Average (slower, following line)

    MAMA is designed to solve the inherent problems of traditional moving averages:
    - Lag in trending markets
    - Excessive noise in sideways markets
    - Fixed parameters that don't adapt to changing market conditions

    Key characteristics:
    - Automatically adapts to market cycle periods
    - Uses Hilbert Transform for cycle analysis
    - Provides both fast (MAMA) and slow (FAMA) adaptive averages
    - Excellent for trend identification and crossover signals
    - Reduces lag while maintaining smoothness
    - Works well in both trending and ranging markets

    The algorithm uses:
    - Hilbert Transform to detect dominant market cycles
    - Fast and slow limits to control adaptation speed
    - Dynamic alpha calculation based on cycle periods
    - Exponential smoothing with adaptive parameters

    Typical usage:
    - MAMA/FAMA crossovers for trend changes
    - Price vs MAMA for trend direction
    - MAMA slope for trend strength
    - Adaptive support/resistance levels

    Parameters:
    - fastlimit: Upper limit for the adaptive alpha (default: 0.5, range: 0.01-0.99)
    - slowlimit: Lower limit for the adaptive alpha (default: 0.05, range: 0.01-0.99)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        mama = MAMA(fastlimit=0.5, slowlimit=0.05)
        mama_custom = MAMA(fastlimit=0.7, slowlimit=0.1, output_columns=["mama_fast", "fama_slow"])
    """

    def __init__(
        self,
        fastlimit: float = 0.5,
        slowlimit: float = 0.05,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.fastlimit = fastlimit
        self.slowlimit = slowlimit
        self.column = column
        self.mama_col = f"mama_{fastlimit}_{slowlimit}_{column}"
        self.fama_col = f"fama_{fastlimit}_{slowlimit}_{column}"
        self._requested_output_columns = output_columns

        # Validate limits
        if not 0.01 <= fastlimit <= 0.99:
            raise ValueError(
                f"fastlimit must be between 0.01 and 0.99, got {fastlimit}"
            )
        if not 0.01 <= slowlimit <= 0.99:
            raise ValueError(
                f"slowlimit must be between 0.01 and 0.99, got {slowlimit}"
            )
        if slowlimit >= fastlimit:
            raise ValueError(
                f"slowlimit ({slowlimit}) must be less than fastlimit ({fastlimit})"
            )

    def build(self) -> pl.Expr:
        """Build the MAMA expression using polars_talib."""
        return Indicators.build_mama(
            source=pl.col(self.column),
            fastlimit=self.fastlimit,
            slowlimit=self.slowlimit,
        )

    def expr(self) -> pl.Expr:
        """Return the MAMA expression with proper column aliases."""
        # MAMA returns a struct with 'mama' and 'fama' fields
        mama_expr = self.build()
        return pl.struct(
            [
                mama_expr.struct.field("mama").alias(self.mama_col),
                mama_expr.struct.field("fama").alias(self.fama_col),
            ]
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        mama_expr = self.build()
        return [
            mama_expr.struct.field("mama").alias(self.mama_col),
            mama_expr.struct.field("fama").alias(self.fama_col),
        ]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.mama_col, self.fama_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 2:
                raise ValueError(
                    "MAMA expects exactly 2 output column names in 'output_columns' (mama, fama)"
                )

            mama_name = self._requested_output_columns[0]
            fama_name = self._requested_output_columns[1]

            if not isinstance(mama_name, str) or not mama_name:
                raise ValueError(
                    "MAMA requires a non-empty string for mama column name"
                )
            if not isinstance(fama_name, str) or not fama_name:
                raise ValueError(
                    "MAMA requires a non-empty string for fama column name"
                )

            self.mama_col = mama_name
            self.fama_col = fama_name

    def window_size(self) -> int:
        """Return the minimum window size needed for MAMA calculation."""
        # MAMA needs significant data for Hilbert Transform and cycle analysis
        return 32

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable MAMA calculation."""
        # MAMA needs extensive warmup due to Hilbert Transform complexity
        # and adaptive parameter calculation
        return 100
