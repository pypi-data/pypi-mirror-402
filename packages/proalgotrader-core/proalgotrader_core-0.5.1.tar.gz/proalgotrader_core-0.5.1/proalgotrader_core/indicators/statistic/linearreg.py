"""
LINEARREG - Linear Regression

Category: Statistic Functions
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class LINEARREG(Indicator):
    """
    LINEARREG - Linear Regression

    Category: Statistic Functions

    The Linear Regression (LINEARREG) is a statistical function that calculates
    the linear regression line for a price series over a specified time period.
    It fits a straight line to the data points using the least squares method.

    LINEARREG is useful for:
    - Trend analysis and identification
    - Price forecasting and prediction
    - Statistical analysis of price movements
    - Trend strength measurement
    - Market direction analysis

    The calculation formula:
    LINEARREG uses least squares regression to find the best-fit line
    through the price data points over the specified time period.

    This statistical measure helps identify the overall trend direction
    and can be used for trend-following strategies and analysis.

    Parameters:
        price: Price series column (default: "close")
        timeperiod: Time period for calculation (default: 14)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with linearreg column
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

        base = prefix or f"linearreg_{timeperiod}_{price}"
        self.linearreg_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build LINEARREG expression."""
        return Indicators.build_linearreg(
            source=pl.col(self.price),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return LINEARREG expressions."""
        return [self.build().alias(self.linearreg_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.linearreg_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.price]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "LINEARREG expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("LINEARREG requires a non-empty output column name")
            self.linearreg_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # LINEARREG needs the timeperiod for calculation
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # LINEARREG needs warmup data for stable statistical calculation
        return self.timeperiod
