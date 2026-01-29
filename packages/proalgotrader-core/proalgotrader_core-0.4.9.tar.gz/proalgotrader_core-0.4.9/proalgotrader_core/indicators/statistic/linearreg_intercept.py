"""
LINEARREG_INTERCEPT - Linear Regression Intercept

Category: Statistic Functions
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class LINEARREG_INTERCEPT(Indicator):
    """
    LINEARREG_INTERCEPT - Linear Regression Intercept

    Category: Statistic Functions

    The Linear Regression Intercept (LINEARREG_INTERCEPT) is a statistical function that
    calculates the y-intercept of the linear regression line for a price series over
    a specified time period. It represents the value where the regression line crosses
    the y-axis.

    LINEARREG_INTERCEPT is useful for:
    - Trend analysis and identification
    - Price level estimation
    - Support and resistance level calculation
    - Statistical analysis of price movements
    - Market direction analysis

    The calculation formula:
    LINEARREG_INTERCEPT calculates the y-intercept of the linear regression
    line fitted to the price data over the specified time period.

    This statistical measure helps identify price levels and can be used for
    trend-following strategies and statistical analysis of market behavior.

    Parameters:
        price: Price series column (default: "close")
        timeperiod: Time period for calculation (default: 14)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with linearreg_intercept column
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

        base = prefix or f"linearreg_intercept_{timeperiod}_{price}"
        self.linearreg_intercept_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build LINEARREG_INTERCEPT expression."""
        return Indicators.build_linearreg_intercept(
            source=pl.col(self.price),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return LINEARREG_INTERCEPT expressions."""
        return [self.build().alias(self.linearreg_intercept_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.linearreg_intercept_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.price]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "LINEARREG_INTERCEPT expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "LINEARREG_INTERCEPT requires a non-empty output column name"
                )
            self.linearreg_intercept_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # LINEARREG_INTERCEPT needs the timeperiod for calculation
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # LINEARREG_INTERCEPT needs warmup data for stable statistical calculation
        return self.timeperiod
