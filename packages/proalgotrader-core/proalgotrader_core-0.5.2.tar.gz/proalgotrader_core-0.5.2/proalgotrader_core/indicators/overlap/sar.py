"""
SAR - Parabolic SAR (Stop and Reverse)

Category: Overlap Studies
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class SAR(Indicator):
    """
    SAR - Parabolic SAR (Stop and Reverse)

    Category: Overlap Studies

    The Parabolic SAR (Stop and Reverse) is a trend-following indicator that provides
    stop and reverse points. It is designed to keep traders in a trend as long as
    the trend is sustained, but will reverse when the trend changes.

    Formula: SAR = Previous SAR + AF * (EP - Previous SAR)
    Where:
    - AF (Acceleration Factor) starts at acceleration and increases by acceleration
      each time a new extreme point is reached, up to maximum
    - EP (Extreme Point) is the highest high in an uptrend or lowest low in a downtrend

    Parameters:
        high: High price data (default: "high")
        low: Low price data (default: "low")
        acceleration: Acceleration factor (default: 0.02)
        maximum: Maximum acceleration (default: 0.2)
        output_columns: Optional custom output column names

    Returns:
        DataFrame with SAR column
    """

    def __init__(
        self,
        high: str = "high",
        low: str = "low",
        acceleration: float = 0.02,
        maximum: float = 0.2,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.high = high
        self.low = low
        self.acceleration = acceleration
        self.maximum = maximum
        self.output_column = f"sar_{acceleration}_{maximum}_{high}_{low}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build SAR expression."""
        return Indicators.build_sar(
            high=pl.col(self.high),
            low=pl.col(self.low),
            acceleration=self.acceleration,
            maximum=self.maximum,
        )

    def expr(self) -> pl.Expr:
        """Return SAR expression with alias."""
        return self.build().alias(self.output_column)

    def _exprs(self) -> List[pl.Expr]:
        """Return SAR expressions."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.output_column]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.high, self.low]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "SAR expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("SAR requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # SAR doesn't have a fixed window size, but needs at least 2 periods to start
        return 2

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # SAR needs a few periods to establish trend direction
        return 5
