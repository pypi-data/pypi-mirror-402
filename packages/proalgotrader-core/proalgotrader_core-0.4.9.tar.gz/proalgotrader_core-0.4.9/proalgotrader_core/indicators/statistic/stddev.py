"""
STDDEV - Standard Deviation

Category: Statistic Functions
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class STDDEV(Indicator):
    """
    STDDEV - Standard Deviation

    Category: Statistic Functions

    The Standard Deviation (STDDEV) is a statistical function that measures
    the amount of variation or dispersion of a price series over a specified
    time period. It quantifies how much the values deviate from the mean.

    STDDEV is useful for:
    - Volatility measurement
    - Risk assessment
    - Price dispersion analysis
    - Statistical analysis of price movements
    - Market stability analysis

    The calculation formula:
    STDDEV calculates the standard deviation of the price data over the
    specified time period, with an optional deviation multiplier (nbdev).

    This statistical measure helps identify price volatility and can be used
    for risk management and volatility-based strategies.

    Parameters:
        price: Price series column (default: "close")
        timeperiod: Time period for calculation (default: 5)
        nbdev: Number of deviations (default: 1)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with stddev column
    """

    def __init__(
        self,
        price: str = "close",
        timeperiod: int = 5,
        nbdev: float = 1.0,
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.price = price
        self.timeperiod = timeperiod
        self.nbdev = nbdev

        base = prefix or f"stddev_{timeperiod}_{nbdev}_{price}"
        self.stddev_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build STDDEV expression."""
        return Indicators.build_stddev(
            source=pl.col(self.price),
            timeperiod=self.timeperiod,
            nbdev=self.nbdev,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return STDDEV expressions."""
        return [self.build().alias(self.stddev_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.stddev_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.price]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "STDDEV expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("STDDEV requires a non-empty output column name")
            self.stddev_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # STDDEV needs the timeperiod for calculation
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # STDDEV needs warmup data for stable statistical calculation
        return self.timeperiod
