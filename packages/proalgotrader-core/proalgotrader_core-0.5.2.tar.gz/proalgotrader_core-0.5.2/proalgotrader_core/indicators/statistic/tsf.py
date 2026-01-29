"""
TSF - Time Series Forecast

Category: Statistic Functions
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class TSF(Indicator):
    """
    TSF - Time Series Forecast

    Category: Statistic Functions

    The Time Series Forecast (TSF) is a statistical function that predicts
    future values of a price series based on linear regression analysis
    over a specified time period. It provides a forecast of the next value.

    TSF is useful for:
    - Price prediction and forecasting
    - Trend analysis and identification
    - Future value estimation
    - Statistical analysis of price movements
    - Market direction analysis

    The calculation formula:
    TSF uses linear regression to fit a line to the price data over the
    specified time period and then projects the next value based on this trend.

    This statistical measure helps predict future price movements and can be used
    for trend-following strategies and price forecasting.

    Parameters:
        price: Price series column (default: "close")
        timeperiod: Time period for calculation (default: 14)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with tsf column
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

        base = prefix or f"tsf_{timeperiod}_{price}"
        self.tsf_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build TSF expression."""
        return Indicators.build_tsf(
            source=pl.col(self.price),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return TSF expressions."""
        return [self.build().alias(self.tsf_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.tsf_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.price]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "TSF expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("TSF requires a non-empty output column name")
            self.tsf_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # TSF needs the timeperiod for calculation
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # TSF needs warmup data for stable statistical calculation
        return self.timeperiod
