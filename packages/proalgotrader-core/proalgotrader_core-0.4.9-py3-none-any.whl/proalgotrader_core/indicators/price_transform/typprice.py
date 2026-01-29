"""
TYPPRICE - Typical Price

Category: Price Transform
"""

import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class TYPPRICE(Indicator):
    """
    TYPPRICE - Typical Price

    Category: Price Transform

    The Typical Price (TYPPRICE) is a price transform indicator that calculates
    the typical price using high, low, and close prices. This provides a
    representative price value that gives more weight to the closing price
    compared to the median price.

    TYPPRICE is useful for:
    - Price smoothing and filtering
    - Creating representative price values
    - Price analysis and comparison
    - Technical analysis applications
    - Volume-weighted price analysis

    The calculation formula:
    TYPPRICE = (High + Low + Close) / 3

    This transformation provides a balanced view of the price action by
    incorporating three key price components, with equal weighting to each.

    Parameters:
        high: High price column (default: "high")
        low: Low price column (default: "low")
        close: Close price column (default: "close")
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with typprice column
    """

    def __init__(
        self,
        high: str = "high",
        low: str = "low",
        close: str = "close",
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.high = high
        self.low = low
        self.close = close

        base = prefix or f"typprice_{high}_{low}_{close}"
        self.typprice_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build TYPPRICE expression."""
        return (pl.col(self.high) + pl.col(self.low) + pl.col(self.close)) / 3

    def _exprs(self) -> List[pl.Expr]:
        """Return TYPPRICE expressions."""
        return [self.build().alias(self.typprice_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.typprice_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.high, self.low, self.close]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "TYPPRICE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("TYPPRICE requires a non-empty output column name")
            self.typprice_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # TYPPRICE is a simple price transform, no window needed
        return 0

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # TYPPRICE is a simple price transform, no warmup needed
        return 0
