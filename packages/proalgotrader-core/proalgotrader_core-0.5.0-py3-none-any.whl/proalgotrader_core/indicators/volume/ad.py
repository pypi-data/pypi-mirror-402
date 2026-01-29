"""
AD - Chaikin A/D Line

Category: Volume Indicators
"""

import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class AD(Indicator):
    """
    AD - Chaikin A/D Line

    Category: Volume Indicators

    The Chaikin Accumulation/Distribution Line (A/D Line) is a volume-based
    indicator that measures the cumulative flow of money into and out of a
    security. It uses the relationship between the close price and the high-low
    range to determine whether volume is flowing into or out of the security.

    The A/D Line is calculated as:
    A/D = Previous A/D + ((Close - Low) - (High - Close)) / (High - Low) * Volume

    When the close is in the upper half of the high-low range, the A/D line
    increases, indicating accumulation. When the close is in the lower half,
    the A/D line decreases, indicating distribution.

    Parameters:
        high: High price data (default: "high")
        low: Low price data (default: "low")
        close: Close price data (default: "close")
        volume: Volume data (default: "volume")
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with AD column
    """

    def __init__(
        self,
        high: str = "high",
        low: str = "low",
        close: str = "close",
        volume: str = "volume",
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

        base = prefix or f"ad_{high}_{low}_{close}_{volume}"
        self.ad_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build AD expression."""
        high = pl.col(self.high)
        low = pl.col(self.low)
        close = pl.col(self.close)
        volume = pl.col(self.volume)

        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fill_null(0)
        return (clv * volume).cum_sum()

    def _exprs(self) -> List[pl.Expr]:
        """Return AD expressions."""
        return [self.build().alias(self.ad_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.ad_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.high, self.low, self.close, self.volume]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "AD expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("AD requires a non-empty single output column name")
            self.ad_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # AD is cumulative but only requires previous bar state to update
        return 1

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # AD needs warmup to establish stable cumulative values
        return 50
