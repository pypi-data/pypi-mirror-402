"""
WCLPRICE - Weighted Close Price

Category: Price Transform
"""

import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class WCLPRICE(Indicator):
    """
    WCLPRICE - Weighted Close Price

    Category: Price Transform

    The Weighted Close Price (WCLPRICE) is a price transform indicator that calculates
    the weighted close price using high, low, and close prices. This provides a
    representative price value that gives more weight to the closing price
    compared to the typical price.

    WCLPRICE is useful for:
    - Price smoothing and filtering
    - Creating representative price values
    - Price analysis and comparison
    - Technical analysis applications
    - Volume-weighted price analysis

    The calculation formula:
    WCLPRICE = (High + Low + 2 * Close) / 4

    This transformation provides a balanced view of the price action by
    giving double weight to the closing price, which is often considered
    the most important price component.

    Parameters:
        high: High price column (default: "high")
        low: Low price column (default: "low")
        close: Close price column (default: "close")
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with wclprice column
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

        base = prefix or f"wclprice_{high}_{low}_{close}"
        self.wclprice_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build WCLPRICE expression."""
        return (pl.col(self.high) + pl.col(self.low) + 2 * pl.col(self.close)) / 4

    def _exprs(self) -> List[pl.Expr]:
        """Return WCLPRICE expressions."""
        return [self.build().alias(self.wclprice_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.wclprice_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.high, self.low, self.close]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "WCLPRICE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("WCLPRICE requires a non-empty output column name")
            self.wclprice_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # WCLPRICE is a simple price transform, no window needed
        return 0

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # WCLPRICE is a simple price transform, no warmup needed
        return 0
