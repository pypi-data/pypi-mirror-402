"""
MEDPRICE - Median Price

Category: Price Transform
"""

import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class MEDPRICE(Indicator):
    """
    MEDPRICE - Median Price

    Category: Price Transform

    The Median Price (MEDPRICE) is a price transform indicator that calculates
    the median of the high and low prices. This provides a representative
    price value that is less sensitive to extreme values compared to the average.

    MEDPRICE is useful for:
    - Price smoothing and filtering
    - Creating representative price values
    - Reducing impact of extreme values
    - Price analysis and comparison
    - Technical analysis applications

    The calculation formula:
    MEDPRICE = (High + Low) / 2

    This simple but effective transformation provides a balanced view of
    the price range by using the midpoint between high and low prices.

    Parameters:
        high: High price column (default: "high")
        low: Low price column (default: "low")
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with medprice column
    """

    def __init__(
        self,
        high: str = "high",
        low: str = "low",
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.high = high
        self.low = low

        base = prefix or f"medprice_{high}_{low}"
        self.medprice_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build MEDPRICE expression."""
        return (pl.col(self.high) + pl.col(self.low)) / 2

    def _exprs(self) -> List[pl.Expr]:
        """Return MEDPRICE expressions."""
        return [self.build().alias(self.medprice_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.medprice_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.high, self.low]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "MEDPRICE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("MEDPRICE requires a non-empty output column name")
            self.medprice_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # MEDPRICE is a simple price transform, no window needed
        return 0

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # MEDPRICE is a simple price transform, no warmup needed
        return 0
