"""
MIDPRICE - Midpoint Price over period

Category: Overlap Studies
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class MIDPRICE(Indicator):
    """
    MIDPRICE - Midpoint Price over period

    Category: Overlap Studies

    The MIDPRICE indicator calculates the midpoint price between the highest high
    and lowest low over a specified period.

    Formula: (Highest High + Lowest Low) / 2 over the specified period

    Parameters:
        high: High price data (default: "high")
        low: Low price data (default: "low")
        timeperiod: Time period for calculation (default: 14)
        output_columns: Optional custom output column names

    Returns:
        DataFrame with MIDPRICE column
    """

    def __init__(
        self,
        high: str = "high",
        low: str = "low",
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.high = high
        self.low = low
        self.timeperiod = timeperiod
        self.output_column = f"midprice_{timeperiod}_{high}_{low}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build MIDPRICE expression."""
        return Indicators.build_midprice(
            high=pl.col(self.high), low=pl.col(self.low), timeperiod=self.timeperiod
        )

    def expr(self) -> pl.Expr:
        """Return MIDPRICE expression with alias."""
        return self.build().alias(self.output_column)

    def _exprs(self) -> List[pl.Expr]:
        """Return MIDPRICE expressions."""
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
                    "MIDPRICE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "MIDPRICE requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        return 0
