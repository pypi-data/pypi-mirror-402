"""
LINEARREG_ANGLE - Linear Regression Angle

Category: Statistic Functions
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class LINEARREG_ANGLE(Indicator):
    """
    LINEARREG_ANGLE - Linear Regression Angle

    Category: Statistic Functions

    The Linear Regression Angle (LINEARREG_ANGLE) is a statistical function that
    calculates the angle of the linear regression line for a price series over
    a specified time period. It measures the slope of the regression line in degrees.

    LINEARREG_ANGLE is useful for:
    - Trend strength measurement
    - Trend direction analysis
    - Momentum identification
    - Trend change detection
    - Market direction analysis

    The calculation formula:
    LINEARREG_ANGLE calculates the angle (in degrees) of the linear regression
    line fitted to the price data over the specified time period.

    This statistical measure helps identify the steepness and direction of trends,
    making it valuable for trend-following strategies and momentum analysis.

    Parameters:
        price: Price series column (default: "close")
        timeperiod: Time period for calculation (default: 14)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with linearreg_angle column
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

        base = prefix or f"linearreg_angle_{timeperiod}_{price}"
        self.linearreg_angle_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build LINEARREG_ANGLE expression."""
        return Indicators.build_linearreg_angle(
            source=pl.col(self.price),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return LINEARREG_ANGLE expressions."""
        return [self.build().alias(self.linearreg_angle_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.linearreg_angle_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.price]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "LINEARREG_ANGLE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "LINEARREG_ANGLE requires a non-empty output column name"
                )
            self.linearreg_angle_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # LINEARREG_ANGLE needs the timeperiod for calculation
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # LINEARREG_ANGLE needs warmup data for stable statistical calculation
        return self.timeperiod
