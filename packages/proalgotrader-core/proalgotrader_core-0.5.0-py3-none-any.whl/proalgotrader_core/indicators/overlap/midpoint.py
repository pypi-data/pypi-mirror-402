"""
MIDPOINT - MidPoint over period

Category: Overlap Studies
"""

import polars as pl
from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class MIDPOINT(Indicator):
    """
    MIDPOINT - MidPoint over period

    Category: Overlap Studies

    The MidPoint indicator calculates the midpoint of the highest high and
    lowest low over a specified period.

    Formula: (Highest High + Lowest Low) / 2 over the specified period

    Parameters:
        real: Input data (typically close price, default: "close")
        timeperiod: Time period for calculation (default: 14)
        output_columns: Optional custom output column names

    Returns:
        DataFrame with MIDPOINT column
    """

    def __init__(
        self,
        real: str = "close",
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.real = real
        self.timeperiod = timeperiod
        self.output_column = f"midpoint_{timeperiod}_{real}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build MIDPOINT expression."""
        source = pl.col(self.real)
        highest_high = source.rolling_max(window_size=self.timeperiod)
        lowest_low = source.rolling_min(window_size=self.timeperiod)
        return (highest_high + lowest_low) / 2

    def expr(self) -> pl.Expr:
        """Return MIDPOINT expression with alias."""
        return self.build().alias(self.output_column)

    def _exprs(self) -> List[pl.Expr]:
        """Return MIDPOINT expressions."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.output_column]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.real]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "MIDPOINT expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "MIDPOINT requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        return 0
