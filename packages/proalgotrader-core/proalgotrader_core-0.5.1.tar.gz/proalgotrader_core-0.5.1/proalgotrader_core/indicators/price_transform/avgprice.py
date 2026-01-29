"""
AVGPRICE - Average Price

Category: Price Transform
"""

import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class AVGPRICE(Indicator):
    """
    AVGPRICE - Average Price

    Category: Price Transform

    The Average Price (AVGPRICE) is a price transform indicator that calculates
    the average of the four basic price components: open, high, low, and close.
    This provides a single representative price value for each period.

    AVGPRICE is useful for:
    - Price smoothing and filtering
    - Creating representative price values
    - Reducing noise in price data
    - Price analysis and comparison
    - Technical analysis applications

    The calculation formula:
    AVGPRICE = (Open + High + Low + Close) / 4

    This simple but effective transformation provides a balanced view of
    the price action by incorporating all four price components equally.

    Parameters:
        open: Open price column (default: "open")
        high: High price column (default: "high")
        low: Low price column (default: "low")
        close: Close price column (default: "close")
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with avgprice column
    """

    def __init__(
        self,
        open: str = "open",
        high: str = "high",
        low: str = "low",
        close: str = "close",
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.open = open
        self.high = high
        self.low = low
        self.close = close

        base = prefix or f"avgprice_{open}_{high}_{low}_{close}"
        self.avgprice_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build AVGPRICE expression."""
        return (
            pl.col(self.open)
            + pl.col(self.high)
            + pl.col(self.low)
            + pl.col(self.close)
        ) / 4

    def _exprs(self) -> List[pl.Expr]:
        """Return AVGPRICE expressions."""
        return [self.build().alias(self.avgprice_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.avgprice_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.open, self.high, self.low, self.close]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "AVGPRICE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("AVGPRICE requires a non-empty output column name")
            self.avgprice_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # AVGPRICE is a simple price transform, no window needed
        return 0

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # AVGPRICE is a simple price transform, no warmup needed
        return 0
