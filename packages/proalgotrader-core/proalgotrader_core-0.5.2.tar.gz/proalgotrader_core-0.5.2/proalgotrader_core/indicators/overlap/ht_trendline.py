"""
HT_TRENDLINE - Hilbert Transform - Instantaneous Trendline

Category: Overlap Studies
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class HT_TRENDLINE(Indicator):
    """
    HT_TRENDLINE - Hilbert Transform - Instantaneous Trendline

    Category: Overlap Studies

    The Hilbert Transform Instantaneous Trendline is a trend-following indicator
    that uses the Hilbert Transform to identify the instantaneous trendline of
    a price series. It provides a smooth trend line that adapts to price changes
    and helps identify trend direction and potential reversal points.

    The indicator uses complex mathematical transformations to extract the
    instantaneous trend component from price data, making it particularly
    useful for identifying cyclical patterns and trend changes.

    Parameters:
        real: Input price data (default: "close")
        output_columns: Optional custom output column names

    Returns:
        DataFrame with HT_TRENDLINE column
    """

    def __init__(
        self,
        real: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.real = real
        self.output_column = f"ht_trendline_{real}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build HT_TRENDLINE expression."""
        return Indicators.build_ht_trendline(source=pl.col(self.real))

    def expr(self) -> pl.Expr:
        """Return HT_TRENDLINE expression with alias."""
        return self.build().alias(self.output_column)

    def _exprs(self) -> List[pl.Expr]:
        """Return HT_TRENDLINE expressions."""
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
                    "HT_TRENDLINE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "HT_TRENDLINE requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # HT_TRENDLINE uses Hilbert Transform which typically needs around 50-100 periods
        return 50

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # Hilbert Transform needs significant warmup for stable output
        return 50
