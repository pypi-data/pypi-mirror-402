"""
LINEARREG_SLOPE - Linear Regression Slope

Category: Statistic Functions
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class LINEARREG_SLOPE(Indicator):
    """
    LINEARREG_SLOPE - Linear Regression Slope

    Category: Statistic Functions

    The Linear Regression Slope (LINEARREG_SLOPE) is a statistical function that
    calculates the slope of the linear regression line for a price series over
    a specified time period. It measures the rate of change of the regression line.

    LINEARREG_SLOPE is useful for:
    - Trend strength measurement
    - Trend direction analysis
    - Momentum identification
    - Trend change detection
    - Market direction analysis

    The calculation formula:
    LINEARREG_SLOPE calculates the slope of the linear regression
    line fitted to the price data over the specified time period.

    This statistical measure helps identify the rate of change of trends,
    making it valuable for trend-following strategies and momentum analysis.

    Parameters:
        price: Price series column (default: "close")
        timeperiod: Time period for calculation (default: 14)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with linearreg_slope column
    """

    def __init__(
        self,
        price: str = "close",
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.price = price
        self.timeperiod = timeperiod

        base = prefix or f"linearreg_slope_{timeperiod}_{price}"
        self.linearreg_slope_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build LINEARREG_SLOPE expression."""
        return Indicators.build_linearreg_slope(
            source=pl.col(self.price),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return LINEARREG_SLOPE expressions."""
        return [self.build().alias(self.linearreg_slope_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.linearreg_slope_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.price]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "LINEARREG_SLOPE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "LINEARREG_SLOPE requires a non-empty output column name"
                )
            self.linearreg_slope_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # LINEARREG_SLOPE needs the timeperiod for calculation
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # LINEARREG_SLOPE needs warmup data for stable statistical calculation
        return self.timeperiod
